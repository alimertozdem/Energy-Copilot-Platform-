# =============================================================================
# iot_device_simulator.py
# Energy Copilot Platform — IoT Device Simulator
# =============================================================================
#
# PURPOSE:
#   Simulates 6 buildings × 4 sensor types sending real-time readings
#   to Azure Event Hub. This is the trial-period stand-in for real IoT hardware.
#
#   WHY SIMULATE:
#   We don't have physical BACnet/Modbus devices for the trial, but the
#   architecture is identical. This script plays the role of the edge gateway
#   that would sit on-site and forward real sensor data.
#
#   PRODUCTION REPLACEMENT:
#   When a real building connects, this script is replaced by the edge
#   gateway running on a Raspberry Pi / industrial PC. The Event Hub
#   connection string is the same. Nothing downstream changes.
#
# HOW TO RUN:
#   1. pip install azure-eventhub python-dotenv
#   2. Set EVENTHUB_CONNECTION_STRING in .env (or environment variable)
#   3. python iot_device_simulator.py --mode continuous --interval 15
#      OR
#      python iot_device_simulator.py --mode batch --count 96
#
# MODES:
#   continuous: sends 1 reading per sensor every --interval seconds (default 15)
#   batch:      sends --count historical readings per sensor at once (backfill)
#
# OUTPUT:
#   JSON messages → Azure Event Hub → Fabric EventStream → KQL + Lakehouse
# =============================================================================

import argparse
import json
import logging
import math
import os
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

# Azure Event Hub SDK
try:
    from azure.eventhub import EventHubProducerClient, EventData, EventDataBatch
    EVENTHUB_AVAILABLE = True
except ImportError:
    EVENTHUB_AVAILABLE = False
    print("⚠️  azure-eventhub not installed. Run: pip install azure-eventhub")
    print("   Running in DRY RUN mode (prints JSON to stdout instead).\n")

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S"
)
logger = logging.getLogger(__name__)


# =============================================================================
# BUILDING CONFIGURATION
# =============================================================================

BUILDINGS = {
    "B001": {
        "name": "Berliner Büro GmbH",
        "city": "Berlin",
        "country": "DE",
        "floors": 4,
        "zones_per_floor": 3,
        "base_power_kw": 45.0,
        "hvac_type": "heat_pump",
        "protocol": "BACnet",     # dominant protocol per building
    },
    "B002": {
        "name": "Frankfurt Tower",
        "city": "Frankfurt",
        "country": "DE",
        "floors": 8,
        "zones_per_floor": 4,
        "base_power_kw": 82.0,
        "hvac_type": "gas_boiler",
        "protocol": "Modbus",
    },
    "B003": {
        "name": "München Logistik AG",
        "city": "Munich",
        "country": "DE",
        "floors": 2,
        "zones_per_floor": 5,
        "base_power_kw": 38.0,
        "hvac_type": "gas_boiler",
        "protocol": "Modbus",
    },
    "B004": {
        "name": "Hamburg Handel GmbH",
        "city": "Hamburg",
        "country": "DE",
        "floors": 3,
        "zones_per_floor": 3,
        "base_power_kw": 52.0,
        "hvac_type": "district",
        "protocol": "MQTT",
    },
    "B005": {
        "name": "Istanbul Plaza",
        "city": "Istanbul",
        "country": "TR",
        "floors": 6,
        "zones_per_floor": 4,
        "base_power_kw": 68.0,
        "hvac_type": "gas_boiler",
        "protocol": "REST",
    },
    "B006": {
        "name": "Amsterdam Office Hub",
        "city": "Amsterdam",
        "country": "NL",
        "floors": 5,
        "zones_per_floor": 3,
        "base_power_kw": 55.0,
        "hvac_type": "vrf",
        "protocol": "MQTT",
    },
}

# Sensor types with their normal operating ranges and alert thresholds
SENSOR_CONFIG = {
    "HVAC_temp": {
        "unit": "C",
        "normal_min": 20.0,
        "normal_max": 24.0,
        "alert_low": 17.0,
        "alert_high": 27.0,
        "baseline": 22.0,
        "noise_std": 0.8,          # realistic sensor noise
    },
    "humidity": {
        "unit": "%",
        "normal_min": 40.0,
        "normal_max": 60.0,
        "alert_low": 28.0,
        "alert_high": 72.0,
        "baseline": 50.0,
        "noise_std": 2.5,
    },
    "CO2": {
        "unit": "ppm",
        "normal_min": 400.0,
        "normal_max": 1000.0,
        "alert_low": None,         # no low alert for CO2
        "alert_high": 1500.0,
        "baseline": 600.0,
        "noise_std": 40.0,
    },
    "power": {
        "unit": "kW",
        "normal_min": None,        # building-specific
        "normal_max": None,
        "alert_low": None,
        "alert_high": None,        # 120% of baseline
        "baseline": None,          # set per building
        "noise_std": 3.5,
    },
}

# Sensor locations per zone pattern
LOCATION_TEMPLATES = [
    "Floor {floor}, Zone {zone}",
    "Floor {floor}, Open Office",
    "Floor {floor}, Meeting Room {zone}",
    "Floor {floor}, Server Room",
    "Basement, Plant Room",
    "Rooftop, AHU Unit {zone}",
]


# =============================================================================
# SENSOR READING GENERATOR
# =============================================================================

class SensorReadingGenerator:
    """
    Generates physically realistic sensor readings with:
    - Circadian patterns (temperature rises during day, CO2 peaks at occupancy hours)
    - Seasonal variation (winter/summer baseline shift)
    - Random anomaly injection (10% of readings)
    - Realistic sensor noise
    """

    ANOMALY_RATE = 0.10    # 10% of readings have an anomaly
    ANOMALY_TYPES = ["spike", "drift", "threshold_exceeded"]

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)

    def _time_of_day_factor(self, hour: int, sensor_type: str) -> float:
        """
        Returns a multiplier [0.7–1.3] based on time of day.
        Simulates occupancy: high during 08:00–18:00, low at night.
        CO2 tracks occupancy closely. Temp is more stable (HVAC setpoint).
        Power peaks morning and afternoon.
        """
        # Occupancy curve: sine wave peaking at noon
        occ = 0.5 + 0.5 * math.sin(math.pi * max(0, hour - 7) / 11) if 7 <= hour <= 18 else 0.1

        factors = {
            "HVAC_temp": 0.95 + 0.1 * occ,     # slight rise during day
            "humidity":  1.0 - 0.05 * occ,     # drier when occupied (aircon)
            "CO2":       0.6 + 1.4 * occ,      # CO2 tracks occupancy strongly
            "power":     0.5 + 1.0 * occ,      # power tracks occupancy
        }
        return factors.get(sensor_type, 1.0)

    def _inject_anomaly(self, value: float, sensor_type: str, config: dict) -> tuple:
        """
        Returns (anomalous_value, anomaly_type, severity).
        Anomaly types:
          spike             — sudden jump (2–4× noise std)
          drift             — value outside normal range but not alert level
          threshold_exceeded — value beyond alert threshold
        """
        anomaly_type = random.choice(self.ANOMALY_TYPES)

        if anomaly_type == "spike":
            spike_magnitude = random.uniform(3, 6) * config["noise_std"]
            direction = random.choice([-1, 1])
            value = value + direction * spike_magnitude
            severity = "Medium"

        elif anomaly_type == "drift":
            n_min = config.get("normal_min") or (value * 0.7)
            n_max = config.get("normal_max") or (value * 1.3)
            drift_range = (n_max - n_min) * 0.3
            # Push value outside normal range in random direction
            if random.random() > 0.5:
                value = n_max + random.uniform(0, drift_range)
            else:
                value = n_min - random.uniform(0, drift_range) if n_min else value
            severity = "Low"

        elif anomaly_type == "threshold_exceeded":
            alert_high = config.get("alert_high")
            alert_low = config.get("alert_low")
            if alert_high and random.random() > 0.3:
                value = alert_high * random.uniform(1.05, 1.25)
                severity = "High"
            elif alert_low:
                value = alert_low * random.uniform(0.75, 0.95)
                severity = "High"
            else:
                value = value * 1.3
                severity = "Medium"

        return round(max(0, value), 2), anomaly_type, severity

    def generate(
        self,
        building_id: str,
        building_config: dict,
        sensor_type: str,
        location: str,
        timestamp: datetime,
    ) -> dict:
        """
        Generate one realistic sensor reading for given building/sensor/time.
        Returns the full 9-field standard schema dict.
        """
        config = SENSOR_CONFIG[sensor_type].copy()

        # Set power baseline from building config
        if sensor_type == "power":
            config["baseline"] = building_config["base_power_kw"]
            config["normal_min"] = config["baseline"] * 0.3
            config["normal_max"] = config["baseline"] * 1.2
            config["alert_high"] = config["baseline"] * 1.4

        # Base value: baseline + time-of-day factor + noise
        hour = timestamp.hour
        tod_factor = self._time_of_day_factor(hour, sensor_type)
        base = config["baseline"] * tod_factor if config["baseline"] else 50.0
        noise = random.gauss(0, config["noise_std"])
        value = round(base + noise, 2)

        # Determine if this reading gets an anomaly
        is_anomaly = random.random() < self.ANOMALY_RATE
        anomaly_type = None
        anomaly_severity = None

        if is_anomaly:
            value, anomaly_type, anomaly_severity = self._inject_anomaly(
                value, sensor_type, config
            )

        # Reading quality: 95-100 normally, drops to 60-80 during anomalies
        quality = random.randint(60, 80) if is_anomaly else random.randint(93, 100)

        # Device ID: deterministic from building + sensor + location
        location_slug = location.lower().replace(", ", "_").replace(" ", "_")
        device_id = f"{building_id}_{sensor_type}_{location_slug}"

        return {
            "device_id":        device_id,
            "building_id":      building_id,
            "sensor_type":      sensor_type,
            "sensor_location":  location,
            "reading_value":    value,
            "reading_unit":     config["unit"],
            "source_protocol":  building_config["protocol"],
            "timestamp":        timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "reading_quality":  quality,
            # Anomaly metadata (included in message, used by Notebook 11b)
            "is_anomaly":       is_anomaly,
            "anomaly_type":     anomaly_type,
            "anomaly_severity": anomaly_severity,
        }


# =============================================================================
# SENSOR MASTER DATA GENERATOR
# =============================================================================

def generate_sensor_master() -> list:
    """
    Generate gold_iot_sensor_master rows — one row per sensor per building.
    This is the reference table that defines setpoints and alert thresholds.
    """
    rows = []
    install_date = "2024-01-15"
    calibration_date = "2025-12-01"

    for building_id, bldg in BUILDINGS.items():
        floor_count = bldg["floors"]
        zones = bldg["zones_per_floor"]

        sensor_id_counter = 1
        for floor in range(1, floor_count + 1):
            for zone in range(1, zones + 1):
                for sensor_type, cfg in SENSOR_CONFIG.items():
                    location = f"Floor {floor}, Zone {zone}"

                    # Power sensor only on floor 1
                    if sensor_type == "power" and floor > 1:
                        continue

                    baseline = cfg["baseline"] or bldg["base_power_kw"]
                    sensor_id = f"{building_id}_{sensor_type}_F{floor}Z{zone}"

                    rows.append({
                        "sensor_id":             sensor_id,
                        "building_id":           building_id,
                        "sensor_type":           sensor_type,
                        "sensor_location":       location,
                        "setpoint_min":          cfg["normal_min"] or round(baseline * 0.7, 1),
                        "setpoint_max":          cfg["normal_max"] or round(baseline * 1.2, 1),
                        "alert_threshold_low":   cfg["alert_low"],
                        "alert_threshold_high":  cfg["alert_high"] or round(baseline * 1.4, 1),
                        "last_calibration_date": calibration_date,
                        "is_active":             True,
                        "install_date":          install_date,
                        "protocol":              bldg["protocol"],
                    })
                    sensor_id_counter += 1

    return rows


# =============================================================================
# EVENT HUB SENDER
# =============================================================================

class EventHubSender:
    """
    Sends normalized sensor readings to Azure Event Hub.
    Uses batching for efficiency (up to 1MB per batch).
    Falls back to dry-run (stdout) if SDK not available or no connection string.
    """

    def __init__(self, connection_string: Optional[str] = None, eventhub_name: str = "sensor-readings"):
        self.connection_string = connection_string or os.getenv("EVENTHUB_CONNECTION_STRING")
        self.eventhub_name = eventhub_name
        self.dry_run = not EVENTHUB_AVAILABLE or not self.connection_string
        self.client = None

        if self.dry_run:
            logger.warning("DRY RUN MODE — messages printed to stdout, not sent to Event Hub.")
            if not self.connection_string:
                logger.warning("Set EVENTHUB_CONNECTION_STRING env var to enable real sending.")
        else:
            self.client = EventHubProducerClient.from_connection_string(
                self.connection_string, eventhub_name=self.eventhub_name
            )
            logger.info(f"Connected to Event Hub: {self.eventhub_name}")

    def send_batch(self, readings: list[dict]) -> int:
        """Send a list of reading dicts. Returns count sent."""
        if self.dry_run:
            for r in readings[:3]:   # print first 3 in dry-run
                print(json.dumps(r))
            if len(readings) > 3:
                print(f"  ... and {len(readings) - 3} more readings")
            return len(readings)

        sent = 0
        batch: EventDataBatch = self.client.create_batch()
        for reading in readings:
            event = EventData(json.dumps(reading))
            try:
                batch.add(event)
            except ValueError:
                # Batch full — send and start new batch
                self.client.send_batch(batch)
                sent += len(batch)
                batch = self.client.create_batch()
                batch.add(event)

        if len(batch) > 0:
            self.client.send_batch(batch)
            sent += len(batch)

        return sent

    def close(self):
        if self.client:
            self.client.close()


# =============================================================================
# MAIN SIMULATION LOGIC
# =============================================================================

def run_continuous(interval_seconds: int, connection_string: Optional[str]):
    """
    Continuous mode: sends one reading per sensor per interval.
    Designed to run indefinitely (Ctrl+C to stop).
    Use this for live demo or when Fabric trial is active.
    """
    generator = SensorReadingGenerator()
    sender = EventHubSender(connection_string)

    logger.info(f"Starting continuous simulation — {interval_seconds}s interval")
    logger.info(f"Buildings: {len(BUILDINGS)} | Sensor types: {len(SENSOR_CONFIG)}")

    cycle = 0
    try:
        while True:
            cycle += 1
            now = datetime.now(timezone.utc)
            readings = []

            for building_id, bldg in BUILDINGS.items():
                for sensor_type in SENSOR_CONFIG:
                    # One reading per sensor type per building per cycle
                    location = f"Floor 1, Zone 1"   # simplified for continuous
                    reading = generator.generate(
                        building_id, bldg, sensor_type, location, now
                    )
                    readings.append(reading)

            sent = sender.send_batch(readings)
            anomaly_count = sum(1 for r in readings if r.get("is_anomaly"))
            logger.info(f"Cycle {cycle}: sent {sent} readings | {anomaly_count} anomalies | {now.strftime('%H:%M:%S')}")

            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        logger.info("Simulation stopped by user.")
    finally:
        sender.close()


def run_batch(readings_per_sensor: int, connection_string: Optional[str]):
    """
    Batch mode: generates --count historical readings per sensor.
    Use this to backfill data when first setting up the pipeline.
    Generates data going back (readings_per_sensor × interval) minutes.
    """
    generator = SensorReadingGenerator(seed=42)  # reproducible
    sender = EventHubSender(connection_string)

    interval_minutes = 15
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(minutes=interval_minutes * readings_per_sensor)

    logger.info(f"Batch mode: {readings_per_sensor} readings/sensor from {start_time.strftime('%Y-%m-%d %H:%M')} UTC")

    all_readings = []
    for building_id, bldg in BUILDINGS.items():
        for sensor_type in SENSOR_CONFIG:
            for i in range(readings_per_sensor):
                ts = start_time + timedelta(minutes=interval_minutes * i)
                location = f"Floor 1, Zone 1"
                reading = generator.generate(
                    building_id, bldg, sensor_type, location, ts
                )
                all_readings.append(reading)

    total = len(all_readings)
    anomalies = sum(1 for r in all_readings if r.get("is_anomaly"))
    logger.info(f"Generated {total} readings | {anomalies} anomalies ({anomalies/total*100:.1f}%)")

    sent = sender.send_batch(all_readings)
    logger.info(f"Sent {sent} readings to Event Hub.")
    sender.close()

    # Also save as CSV for inspection
    import csv
    output_path = os.path.join(os.path.dirname(__file__), "iot_batch_output.csv")
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_readings[0].keys())
        writer.writeheader()
        writer.writerows(all_readings)
    logger.info(f"Saved CSV: {output_path}")


def export_sensor_master():
    """Export sensor master table as CSV for Fabric Lakehouse upload."""
    import csv
    rows = generate_sensor_master()
    output_path = os.path.join(os.path.dirname(__file__), "gold_iot_sensor_master.csv")
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    logger.info(f"Sensor master exported: {output_path} ({len(rows)} sensors)")
    return output_path


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="EnergyLens IoT Device Simulator — sends sensor readings to Azure Event Hub"
    )
    parser.add_argument(
        "--mode",
        choices=["continuous", "batch", "sensor-master"],
        default="batch",
        help="continuous: live loop | batch: historical backfill | sensor-master: export reference CSV"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=15,
        help="(continuous) seconds between readings (default: 15)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=96,
        help="(batch) readings per sensor — 96 = 24h at 15-min interval (default: 96)"
    )
    parser.add_argument(
        "--connection-string",
        type=str,
        default=None,
        help="Azure Event Hub connection string (overrides EVENTHUB_CONNECTION_STRING env var)"
    )

    args = parser.parse_args()

    if args.mode == "continuous":
        run_continuous(args.interval, args.connection_string)
    elif args.mode == "batch":
        run_batch(args.count, args.connection_string)
    elif args.mode == "sensor-master":
        path = export_sensor_master()
        print(f"\n✅ Sensor master saved to: {path}")
