# =============================================================================
# iot_device_simulator.py
# Energy Copilot Platform — IoT Device Simulator (v2 — revised 2026-05-07)
# =============================================================================
#
# CHANGES FROM v1:
#   - Replaced generic "power" sensor with "building_kwh" + "hvac_kwh" (split)
#   - Added extended sensor profiles per building (HVAC_supply_temp, boiler_eff, etc.)
#   - sensor_type is now a DIMENSION — each building has its own sensor set
#   - Added setpoint_min, setpoint_max, baseline_value to readings (for cost estimation)
#   - Added in_setpoint boolean to each reading
#   - Duration tracking for anomaly cost calculation in Notebook 11b
#
# PURPOSE:
#   Simulates 6 buildings × dynamic sensor types sending real-time readings
#   to Azure Event Hub. Trial-period stand-in for real IoT hardware.
#
#   PRODUCTION REPLACEMENT:
#   When a real building connects, this script is replaced by the edge
#   gateway running on-site. Event Hub connection string stays identical.
#   Nothing downstream changes.
#
# HOW TO RUN:
#   pip install azure-eventhub python-dotenv
#   python iot_device_simulator.py --mode batch --count 96
#   python iot_device_simulator.py --mode continuous --interval 15
#   python iot_device_simulator.py --mode sensor-master
#
# =============================================================================

import argparse
import json
import logging
import math
import os
import random
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

try:
    from azure.eventhub import EventHubProducerClient, EventData, EventDataBatch
    EVENTHUB_AVAILABLE = True
except ImportError:
    EVENTHUB_AVAILABLE = False
    print("⚠️  azure-eventhub not installed. Running in DRY RUN mode.\n")

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
# SENSOR TYPE REGISTRY
# =============================================================================
# sensor_type is a DIMENSION — not hardcoded.
# Each sensor type has: unit, normal range, alert thresholds, baseline, noise.
# "baseline" = None means it's set per building (e.g. power sensors).

SENSOR_REGISTRY = {
    # ── Environmental sensors (comfort & air quality) ──
    "HVAC_temp": {
        "unit": "C",
        "normal_min": 20.0, "normal_max": 24.0,
        "alert_low":  17.0, "alert_high": 27.0,
        "baseline": 22.0,   "noise_std": 0.8,
        "category": "comfort",
    },
    "humidity": {
        "unit": "%",
        "normal_min": 40.0, "normal_max": 60.0,
        "alert_low":  28.0, "alert_high": 72.0,
        "baseline": 50.0,   "noise_std": 2.5,
        "category": "comfort",
    },
    "CO2": {
        "unit": "ppm",
        "normal_min": 400.0, "normal_max": 1000.0,
        "alert_low":  None,  "alert_high": 1500.0,
        "baseline": 600.0,   "noise_std": 40.0,
        "category": "air_quality",
    },

    # ── Power / energy meters ──
    "building_kwh": {
        "unit": "kW",
        "normal_min": None,  "normal_max": None,   # building-specific
        "alert_low":  None,  "alert_high": None,   # 120% baseline
        "baseline": None,    "noise_std": 5.0,
        "category": "power",
    },
    "hvac_kwh": {
        "unit": "kW",
        "normal_min": None,  "normal_max": None,
        "alert_low":  None,  "alert_high": None,
        "baseline": None,    "noise_std": 3.0,
        "category": "power",
    },
    "lighting_kwh": {
        "unit": "kW",
        "normal_min": None,  "normal_max": None,
        "alert_low":  None,  "alert_high": None,
        "baseline": None,    "noise_std": 1.5,
        "category": "power",
    },
    "plug_load_kwh": {
        "unit": "kW",
        "normal_min": None,  "normal_max": None,
        "alert_low":  None,  "alert_high": None,
        "baseline": None,    "noise_std": 2.0,
        "category": "power",
    },

    # ── HVAC equipment sensors ──
    "HVAC_supply_temp": {
        "unit": "C",
        "normal_min": 14.0, "normal_max": 18.0,   # supply air: cooled
        "alert_low":  10.0, "alert_high": 22.0,
        "baseline": 16.0,   "noise_std": 0.5,
        "category": "hvac_equipment",
    },
    "HVAC_return_temp": {
        "unit": "C",
        "normal_min": 20.0, "normal_max": 26.0,   # return air: warmer
        "alert_low":  17.0, "alert_high": 30.0,
        "baseline": 23.0,   "noise_std": 0.6,
        "category": "hvac_equipment",
    },

    # ── Mechanical / equipment efficiency ──
    "chiller_cop": {
        "unit": "ratio",
        "normal_min": 3.5,  "normal_max": 6.0,
        "alert_low":  2.5,  "alert_high": None,
        "baseline": 4.5,    "noise_std": 0.3,
        "category": "equipment_efficiency",
    },
    "boiler_eff": {
        "unit": "%",
        "normal_min": 85.0, "normal_max": 96.0,
        "alert_low":  75.0, "alert_high": None,
        "baseline": 91.0,   "noise_std": 1.5,
        "category": "equipment_efficiency",
    },
    "pump_pressure": {
        "unit": "bar",
        "normal_min": 1.5,  "normal_max": 3.5,
        "alert_low":  1.0,  "alert_high": 4.5,
        "baseline": 2.5,    "noise_std": 0.15,
        "category": "mechanical",
    },
    "fan_rpm": {
        "unit": "RPM",
        "normal_min": 800,  "normal_max": 1500,
        "alert_low":  600,  "alert_high": 1800,
        "baseline": 1100,   "noise_std": 50,
        "category": "mechanical",
    },
}


# =============================================================================
# BUILDING CONFIGURATION
# =============================================================================
# Each building has:
#   - base_power_kw: total building baseline power
#   - hvac_fraction: HVAC's share of total power (0.35–0.60 typical commercial)
#   - sensor_profile: list of sensor_types this building has connected
#   - extra_zones: locations beyond standard floor/zone pattern

BUILDINGS = {
    "B001": {
        "name": "Berliner Büro GmbH",
        "city": "Berlin",
        "country": "DE",
        "floors": 4,
        "zones_per_floor": 3,
        "base_power_kw": 85.0,
        "hvac_fraction": 0.55,      # heat pump: higher HVAC share
        "hvac_type": "heat_pump",
        "protocol": "BACnet",
        # Extended sensors: heat pump delta-T monitoring
        "extended_sensors": ["HVAC_supply_temp", "HVAC_return_temp"],
    },
    "B002": {
        "name": "Frankfurt Tower",
        "city": "Frankfurt",
        "country": "DE",
        "floors": 8,
        "zones_per_floor": 4,
        "base_power_kw": 120.0,
        "hvac_fraction": 0.45,
        "hvac_type": "gas_boiler",
        "protocol": "Modbus",
        "extended_sensors": ["boiler_eff", "plug_load_kwh"],
    },
    "B003": {
        "name": "München Logistik AG",
        "city": "Munich",
        "country": "DE",
        "floors": 2,
        "zones_per_floor": 5,
        "base_power_kw": 95.0,
        "hvac_fraction": 0.40,
        "hvac_type": "gas_boiler",
        "protocol": "Modbus",
        "extended_sensors": ["lighting_kwh", "boiler_eff"],
    },
    "B004": {
        "name": "Hamburg Handel GmbH",
        "city": "Hamburg",
        "country": "DE",
        "floors": 3,
        "zones_per_floor": 3,
        "base_power_kw": 110.0,
        "hvac_fraction": 0.50,
        "hvac_type": "district",
        "protocol": "MQTT",
        "extended_sensors": ["pump_pressure", "fan_rpm"],
    },
    "B005": {
        "name": "Istanbul Plaza",
        "city": "Istanbul",
        "country": "TR",
        "floors": 6,
        "zones_per_floor": 4,
        "base_power_kw": 200.0,
        "hvac_fraction": 0.48,
        "hvac_type": "gas_boiler",
        "protocol": "REST",
        "extended_sensors": [],     # minimum sensor set only (TR market)
    },
    "B006": {
        "name": "Amsterdam Office Hub",
        "city": "Amsterdam",
        "country": "NL",
        "floors": 5,
        "zones_per_floor": 3,
        "base_power_kw": 130.0,
        "hvac_fraction": 0.42,
        "hvac_type": "vrf",
        "protocol": "MQTT",
        "extended_sensors": ["lighting_kwh", "plug_load_kwh", "chiller_cop"],
    },
}

# Grid price by country (€/kWh commercial tariff 2026)
GRID_PRICE = {
    "DE": 0.20,
    "TR": 0.14,
    "NL": 0.22,
    "EU": 0.18,
}


# =============================================================================
# SENSOR READING GENERATOR
# =============================================================================

class SensorReadingGenerator:
    """
    Generates physically realistic sensor readings with:
    - Circadian patterns (temperature/CO2/power track occupancy)
    - Building-specific power baselines
    - Dynamic sensor profiles (each building has different sensor set)
    - Realistic anomaly injection (~10%)
    - setpoint_min/max and in_setpoint included in each reading
    """

    ANOMALY_RATE = 0.10
    ANOMALY_TYPES = ["spike", "drift", "threshold_exceeded"]

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)

    def _time_of_day_factor(self, hour: int, sensor_type: str) -> float:
        """
        Occupancy-based time-of-day multiplier [0.5–1.5].
        Occupancy curve: sigmoid-like, peaks at 10:00–14:00.
        """
        if 7 <= hour <= 19:
            occ = 0.4 + 0.6 * math.sin(math.pi * (hour - 7) / 12)
        else:
            occ = 0.05  # night/weekend stub

        category = SENSOR_REGISTRY.get(sensor_type, {}).get("category", "")

        if category == "comfort":
            if sensor_type == "HVAC_temp":
                return 0.97 + 0.06 * occ   # setpoint-controlled, minor variation
            elif sensor_type == "humidity":
                return 1.0 - 0.08 * occ    # drier when occupied
            elif sensor_type == "CO2":
                return 0.55 + 1.45 * occ   # CO2 tracks occupancy strongly
        elif category in ("power", "air_quality"):
            return 0.45 + 1.1 * occ        # power and CO2 track occupancy
        elif category == "hvac_equipment":
            # Supply/return temp: driven by outdoor temp (assume winter scenario)
            return 1.0 + 0.1 * math.sin(2 * math.pi * hour / 24)
        elif category == "equipment_efficiency":
            # Efficiency drops slightly at peak load
            return 1.0 - 0.05 * occ
        elif category == "mechanical":
            return 0.7 + 0.5 * occ         # pump/fan speed tracks load

        return 1.0

    def _get_baseline_for_power(self, sensor_type: str, building: dict) -> tuple:
        """
        Returns (baseline_kw, normal_min, normal_max, alert_high) for power sensors.
        HVAC is a fraction of building total. Lighting/plug are smaller fractions.
        """
        total = building["base_power_kw"]
        hvac_frac = building.get("hvac_fraction", 0.45)

        if sensor_type == "building_kwh":
            baseline = total
        elif sensor_type == "hvac_kwh":
            baseline = total * hvac_frac
        elif sensor_type == "lighting_kwh":
            baseline = total * 0.18   # ~18% typical commercial
        elif sensor_type == "plug_load_kwh":
            baseline = total * 0.20   # ~20% typical commercial
        else:
            baseline = total * 0.10

        return (
            round(baseline, 1),
            round(baseline * 0.30, 1),   # min: 30% at night
            round(baseline * 1.20, 1),   # max normal
            round(baseline * 1.40, 1),   # alert high: 140% baseline
        )

    def _inject_anomaly(self, value: float, sensor_type: str, cfg: dict) -> tuple:
        """
        Returns (anomalous_value, anomaly_type, severity).
        spike             → sudden jump (Medium)
        drift             → outside normal range but below alert (Low)
        threshold_exceeded → beyond alert threshold (High)
        """
        anomaly_type = random.choice(self.ANOMALY_TYPES)

        if anomaly_type == "spike":
            spike = random.uniform(3, 6) * cfg["noise_std"]
            value = value + random.choice([-1, 1]) * spike
            severity = "Medium"

        elif anomaly_type == "drift":
            n_min = cfg.get("normal_min") or (value * 0.7)
            n_max = cfg.get("normal_max") or (value * 1.3)
            drift = (n_max - n_min) * 0.3
            if random.random() > 0.5:
                value = n_max + random.uniform(0, drift)
            elif n_min is not None:
                value = n_min - random.uniform(0, drift * 0.5)
            severity = "Low"

        else:  # threshold_exceeded
            a_high = cfg.get("alert_high")
            a_low  = cfg.get("alert_low")
            if a_high and random.random() > 0.3:
                value = a_high * random.uniform(1.05, 1.25)
                severity = "High"
            elif a_low:
                value = a_low * random.uniform(0.70, 0.95)
                severity = "High"
            else:
                value = value * random.uniform(1.3, 1.5)
                severity = "Medium"

        return round(max(0, value), 2), anomaly_type, severity

    def _action_text(self, sensor_type: str, severity: str, anomaly_type: str) -> str:
        """Rule-based action recommendation text."""
        actions = {
            ("HVAC_temp",    "High",   "threshold_exceeded"): "Check HVAC unit — temperature critical",
            ("HVAC_temp",    "Medium", "spike"):              "Inspect AHU thermostat",
            ("HVAC_temp",    "Low",    "drift"):              "Monitor zone temperature drift",
            ("humidity",     "High",   "threshold_exceeded"): "Check humidifier/dehumidifier",
            ("humidity",     "Medium", "spike"):              "Inspect humidity sensor calibration",
            ("CO2",          "High",   "threshold_exceeded"): "Increase ventilation — CO2 critical",
            ("CO2",          "Medium", "spike"):              "Check occupancy and ventilation rate",
            ("building_kwh", "High",   "threshold_exceeded"): "Investigate power spike — check equipment",
            ("building_kwh", "Medium", "spike"):              "Review load profile — unexpected peak",
            ("hvac_kwh",     "High",   "threshold_exceeded"): "HVAC overconsumption — check controls",
            ("HVAC_supply_temp", "High", "threshold_exceeded"): "Cooling coil issue — check chilled water",
            ("HVAC_return_temp", "High", "threshold_exceeded"): "Poor delta-T — check air distribution",
            ("boiler_eff",   "High",   "threshold_exceeded"): "Boiler efficiency critical — service needed",
            ("chiller_cop",  "High",   "threshold_exceeded"): "Chiller COP low — check refrigerant",
            ("pump_pressure","High",   "threshold_exceeded"): "Hydronic pressure fault — check pump",
            ("fan_rpm",      "High",   "threshold_exceeded"): "Fan overspeed — check VFD",
        }
        key = (sensor_type, severity, anomaly_type)
        return actions.get(key, f"Inspect {sensor_type.replace('_', ' ')} — {severity.lower()} anomaly")

    def _estimate_cost(
        self,
        sensor_type: str,
        deviation: float,
        duration_minutes: float,
        country: str
    ) -> float:
        """
        Estimate € cost of this anomaly. Always labeled 'Est.' — not exact.
        Based on EN 15232 (HVAC) and EN 13779 (ventilation) principles.
        """
        price = GRID_PRICE.get(country, 0.18)   # €/kWh
        hours = duration_minutes / 60.0

        if sensor_type == "HVAC_temp":
            # Each °C over/under setpoint ≈ 3.5 kW extra HVAC load (midpoint est.)
            waste_kw = abs(deviation) * 3.5
        elif sensor_type == "CO2" and deviation > 0:
            # Extra ventilation fan power: 2 kW typical for >500ppm excess
            waste_kw = 2.0
        elif sensor_type in ("building_kwh", "hvac_kwh") and deviation > 0:
            waste_kw = deviation   # actual excess kW is directly visible
        elif sensor_type == "boiler_eff":
            # Efficiency loss: 1% eff drop ≈ ~3% more fuel = ~1.5 kW equivalent
            waste_kw = abs(deviation) * 1.5
        elif sensor_type == "chiller_cop":
            # COP drop from 4.5 to 3.5 on 50kW load = ~3 kW extra
            waste_kw = abs(deviation) * 2.5
        else:
            waste_kw = 1.0   # conservative default

        return round(hours * waste_kw * price, 2)

    def get_sensor_profile(self, building: dict) -> list:
        """
        Returns the full list of sensor_types for this building.
        Minimum set (all buildings) + extended sensors per building config.
        """
        minimum = ["HVAC_temp", "humidity", "CO2", "building_kwh", "hvac_kwh"]
        extended = building.get("extended_sensors", [])
        return minimum + [s for s in extended if s not in minimum]

    def generate(
        self,
        building_id: str,
        building: dict,
        sensor_type: str,
        location: str,
        timestamp: datetime,
        anomaly_duration_minutes: float = 15.0,
    ) -> dict:
        """
        Generate one realistic sensor reading.
        Returns full schema dict including setpoint, baseline, in_setpoint, cost_estimate.
        """
        cfg = SENSOR_REGISTRY[sensor_type].copy()

        # Resolve power sensor baselines from building config
        if cfg["category"] == "power":
            baseline, norm_min, norm_max, alert_high = self._get_baseline_for_power(
                sensor_type, building
            )
            cfg["baseline"]   = baseline
            cfg["normal_min"] = norm_min
            cfg["normal_max"] = norm_max
            cfg["alert_high"] = alert_high

        baseline = cfg["baseline"] or 50.0
        hour = timestamp.hour
        tod = self._time_of_day_factor(hour, sensor_type)
        noise = random.gauss(0, cfg["noise_std"])
        value = round(baseline * tod + noise, 2)
        value = max(0.0, value)

        # Anomaly injection
        is_anomaly = random.random() < self.ANOMALY_RATE
        anomaly_type = None
        anomaly_severity = None
        action = None
        cost_estimate = 0.0

        if is_anomaly:
            value, anomaly_type, anomaly_severity = self._inject_anomaly(value, sensor_type, cfg)
            action = self._action_text(sensor_type, anomaly_severity, anomaly_type)

            # Deviation from normal for cost estimation
            setpoint_mid = ((cfg["normal_min"] or baseline) + (cfg["normal_max"] or baseline)) / 2
            deviation = abs(value - setpoint_mid)
            cost_estimate = self._estimate_cost(
                sensor_type, deviation, anomaly_duration_minutes, building["country"]
            )

        # in_setpoint check
        n_min = cfg.get("normal_min")
        n_max = cfg.get("normal_max")
        in_setpoint = True
        if n_min is not None and value < n_min:
            in_setpoint = False
        if n_max is not None and value > n_max:
            in_setpoint = False

        quality = random.randint(60, 80) if is_anomaly else random.randint(93, 100)

        location_slug = location.lower().replace(", ", "_").replace(" ", "_")
        device_id = f"{building_id}_{sensor_type}_{location_slug}"

        return {
            "device_id":              device_id,
            "building_id":            building_id,
            "sensor_type":            sensor_type,
            "sensor_location":        location,
            "reading_value":          value,
            "reading_unit":           cfg["unit"],
            "source_protocol":        building["protocol"],
            "timestamp":              timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "reading_quality":        quality,
            # Setpoint context (for Notebook 11b in_setpoint + cost calc)
            "setpoint_min":           cfg.get("normal_min"),
            "setpoint_max":           cfg.get("normal_max"),
            "baseline_value":         round(cfg["baseline"] * tod, 2),
            "in_setpoint":            in_setpoint,
            # Anomaly fields
            "is_anomaly":             is_anomaly,
            "anomaly_type":           anomaly_type,
            "anomaly_severity":       anomaly_severity,
            "action_recommended":     action,
            "cost_eur_estimate":      cost_estimate,
        }


# =============================================================================
# SENSOR MASTER DATA GENERATOR
# =============================================================================


# =============================================================================
# SENSOR MASTER DATA GENERATOR
# =============================================================================

def generate_sensor_master() -> list:
    """
    Generate gold_iot_sensor_master rows.
    One row per sensor per zone per building (zone-level sensors),
    or one row per building (power/equipment sensors).
    """
    generator = SensorReadingGenerator(seed=42)
    rows = []
    install_date     = "2024-01-15"
    calibration_date = "2025-12-01"

    for building_id, bldg in BUILDINGS.items():
        sensor_profile = generator.get_sensor_profile(bldg)

        for sensor_type in sensor_profile:
            cfg = SENSOR_REGISTRY[sensor_type].copy()

            # Power sensors: one per building (not per zone)
            if cfg["category"] == "power":
                baseline, norm_min, norm_max, alert_high = generator._get_baseline_for_power(
                    sensor_type, bldg
                )
                rows.append({
                    "sensor_id":             f"{building_id}_{sensor_type}_MAIN",
                    "building_id":           building_id,
                    "sensor_type":           sensor_type,
                    "sensor_location":       "Main Electrical Panel",
                    "setpoint_min":          norm_min,
                    "setpoint_max":          norm_max,
                    "alert_threshold_low":   None,
                    "alert_threshold_high":  alert_high,
                    "baseline_value":        baseline,
                    "last_calibration_date": calibration_date,
                    "is_active":             True,
                    "install_date":          install_date,
                    "protocol":              bldg["protocol"],
                })
                continue

            # Equipment / mechanical: one per building
            if cfg["category"] in ("equipment_efficiency", "mechanical"):
                rows.append({
                    "sensor_id":             f"{building_id}_{sensor_type}_UNIT1",
                    "building_id":           building_id,
                    "sensor_type":           sensor_type,
                    "sensor_location":       "Plant Room",
                    "setpoint_min":          cfg["normal_min"],
                    "setpoint_max":          cfg["normal_max"],
                    "alert_threshold_low":   cfg["alert_low"],
                    "alert_threshold_high":  cfg["alert_high"],
                    "baseline_value":        cfg["baseline"],
                    "last_calibration_date": calibration_date,
                    "is_active":             True,
                    "install_date":          install_date,
                    "protocol":              bldg["protocol"],
                })
                continue

            # Zone-level sensors: one per floor x zone
            for floor in range(1, bldg["floors"] + 1):
                for zone in range(1, bldg["zones_per_floor"] + 1):
                    location = f"Floor {floor}, Zone {zone}"
                    rows.append({
                        "sensor_id":             f"{building_id}_{sensor_type}_F{floor}Z{zone}",
                        "building_id":           building_id,
                        "sensor_type":           sensor_type,
                        "sensor_location":       location,
                        "setpoint_min":          cfg["normal_min"],
                        "setpoint_max":          cfg["normal_max"],
                        "alert_threshold_low":   cfg["alert_low"],
                        "alert_threshold_high":  cfg["alert_high"],
                        "baseline_value":        cfg["baseline"],
                        "last_calibration_date": calibration_date,
                        "is_active":             True,
                        "install_date":          install_date,
                        "protocol":              bldg["protocol"],
                    })

    return rows


# =============================================================================
# EVENT HUB SENDER
# =============================================================================

class EventHubSender:
    """
    Sends normalized sensor readings to Azure Event Hub.
    Batches up to 1MB per batch. Falls back to dry-run if SDK unavailable.
    """

    def __init__(self, connection_string=None, eventhub_name="sensor-readings"):
        self.connection_string = connection_string or os.getenv("EVENTHUB_CONNECTION_STRING")
        self.eventhub_name = eventhub_name
        self.dry_run = not EVENTHUB_AVAILABLE or not self.connection_string
        self.client = None

        if self.dry_run:
            logger.warning("DRY RUN — messages printed to stdout, not sent to Event Hub.")
        else:
            self.client = EventHubProducerClient.from_connection_string(
                self.connection_string, eventhub_name=self.eventhub_name
            )
            logger.info(f"Connected to Event Hub: {self.eventhub_name}")

    def send_batch(self, readings: list) -> int:
        if self.dry_run:
            for r in readings[:2]:
                print(json.dumps(r, indent=2))
            if len(readings) > 2:
                print(f"  ... and {len(readings) - 2} more readings")
            return len(readings)

        sent = 0
        batch = self.client.create_batch()
        for reading in readings:
            event = EventData(json.dumps(reading))
            try:
                batch.add(event)
            except ValueError:
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
# SIMULATION MODES
# =============================================================================

def run_batch(readings_per_sensor: int, connection_string=None):
    """
    Batch mode: generate historical backfill data.
    Default 96 readings = 24h at 15-min intervals.
    Saves iot_batch_output.csv for inspection / manual Fabric upload.
    """
    generator = SensorReadingGenerator(seed=42)
    sender = EventHubSender(connection_string)

    interval_min = 15
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(minutes=interval_min * readings_per_sensor)

    logger.info(f"Batch: {readings_per_sensor} readings/sensor from {start_time.strftime('%Y-%m-%d %H:%M')} UTC")

    all_readings = []

    for building_id, bldg in BUILDINGS.items():
        sensor_profile = generator.get_sensor_profile(bldg)
        logger.info(f"  {building_id} ({bldg['name']}): {len(sensor_profile)} sensor types")

        for sensor_type in sensor_profile:
            cfg = SENSOR_REGISTRY[sensor_type]
            if cfg["category"] in ("comfort", "air_quality", "hvac_equipment"):
                locations = [
                    f"Floor {f}, Zone {z}"
                    for f in range(1, bldg["floors"] + 1)
                    for z in range(1, bldg["zones_per_floor"] + 1)
                ]
            elif cfg["category"] == "power":
                locations = ["Main Electrical Panel"]
            else:
                locations = ["Plant Room"]

            for location in locations:
                for i in range(readings_per_sensor):
                    ts = start_time + timedelta(minutes=interval_min * i)
                    reading = generator.generate(building_id, bldg, sensor_type, location, ts)
                    all_readings.append(reading)

    total = len(all_readings)
    anomalies = sum(1 for r in all_readings if r.get("is_anomaly"))
    high_alerts = sum(1 for r in all_readings if r.get("anomaly_severity") == "High")

    logger.info(f"Generated {total:,} readings | {anomalies:,} anomalies ({anomalies/total*100:.1f}%)")
    logger.info(f"High: {high_alerts} | Med/Low: {anomalies - high_alerts}")

    sender.send_batch(all_readings)
    sender.close()

    import csv
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "iot_batch_output.csv")
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_readings[0].keys())
        writer.writeheader()
        writer.writerows(all_readings)
    logger.info(f"CSV saved: {output_path} ({total:,} rows)")


def run_continuous(interval_seconds: int, connection_string=None):
    """
    Continuous mode: one reading per sensor per interval (Floor 1/Zone 1 only).
    For live demo / Fabric trial when EventStream is active.
    """
    generator = SensorReadingGenerator()
    sender = EventHubSender(connection_string)
    logger.info(f"Continuous: {interval_seconds}s interval | {len(BUILDINGS)} buildings")

    cycle = 0
    try:
        while True:
            cycle += 1
            now = datetime.now(timezone.utc)
            readings = []
            for building_id, bldg in BUILDINGS.items():
                for sensor_type in generator.get_sensor_profile(bldg):
                    cfg = SENSOR_REGISTRY[sensor_type]
                    if cfg["category"] in ("comfort", "air_quality", "hvac_equipment"):
                        location = "Floor 1, Zone 1"
                    elif cfg["category"] == "power":
                        location = "Main Electrical Panel"
                    else:
                        location = "Plant Room"
                    reading = generator.generate(building_id, bldg, sensor_type, location, now)
                    readings.append(reading)

            sent = sender.send_batch(readings)
            anomalies = sum(1 for r in readings if r.get("is_anomaly"))
            logger.info(f"Cycle {cycle}: {sent} readings | {anomalies} anomalies | {now.strftime('%H:%M:%S')}")
            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        logger.info("Stopped.")
    finally:
        sender.close()


def export_sensor_master():
    """Export gold_iot_sensor_master as CSV for Fabric Lakehouse upload."""
    import csv
    rows = generate_sensor_master()
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gold_iot_sensor_master.csv")
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    logger.info(f"Sensor master: {output_path} ({len(rows)} sensors)")

    from collections import Counter
    by_building = Counter(r["building_id"] for r in rows)
    for bid, cnt in sorted(by_building.items()):
        profile = SensorReadingGenerator().get_sensor_profile(BUILDINGS[bid])
        logger.info(f"  {bid} {BUILDINGS[bid]['name']}: {cnt} rows | {profile}")

    return output_path


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="EnergyLens IoT Simulator v2 — sensor-readings → Azure Event Hub"
    )
    parser.add_argument(
        "--mode", choices=["continuous", "batch", "sensor-master"], default="batch",
        help="continuous: live loop | batch: historical backfill | sensor-master: export CSV"
    )
    parser.add_argument("--interval", type=int, default=15,
        help="(continuous) seconds between readings (default: 15)")
    parser.add_argument("--count", type=int, default=96,
        help="(batch) readings per sensor — 96 = 24h @ 15-min (default: 96)")
    parser.add_argument("--connection-string", type=str, default=None,
        help="Azure Event Hub connection string (overrides env var)")

    args = parser.parse_args()

    if args.mode == "continuous":
        run_continuous(args.interval, args.connection_string)
    elif args.mode == "batch":
        run_batch(args.count, args.connection_string)
    elif args.mode == "sensor-master":
        path = export_sensor_master()
        print(f"\n✅ Sensor master: {path}")
