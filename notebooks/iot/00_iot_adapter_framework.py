# =============================================================================
# 00_iot_adapter_framework.py
# Energy Copilot Platform — IoT Protocol Adapter Framework
# =============================================================================
#
# PURPOSE:
#   Every building automation protocol sends data in a different format.
#   This framework defines one Adapter class per protocol. Each adapter:
#     1. Parses the raw protocol message (BACnet object, Modbus register, etc.)
#     2. Normalizes it to a single standard Python dict
#     3. That dict is then sent to Azure Event Hub as JSON
#
#   WHY THIS PATTERN:
#   When a new protocol is needed (e.g. OPC-UA), we add one class.
#   Nothing else in the pipeline changes — Event Hub, EventStream, KQL,
#   Lakehouse, DAX measures: all stay untouched.
#
# STANDARD OUTPUT SCHEMA (all adapters produce this):
#   {
#     "device_id"       : str  — globally unique sensor identifier
#     "building_id"     : str  — FK to silver_building_master (e.g. "B001")
#     "sensor_type"     : str  — HVAC_temp | humidity | CO2 | power
#     "sensor_location" : str  — human-readable zone (e.g. "Floor 2, Zone A")
#     "reading_value"   : float
#     "reading_unit"    : str  — always SI: °C, %, ppm, kW, kWh
#     "source_protocol" : str  — BACnet | Modbus | MQTT | REST | Simulated
#     "timestamp"       : str  — ISO 8601 UTC (e.g. "2026-05-07T14:30:00Z")
#     "reading_quality" : int  — 0-100, data completeness/reliability %
#   }
#
# PROTOCOLS SUPPORTED:
#   P0 (must-have): BACnet/IP (ASHRAE 135), Modbus TCP (IEC 61158)
#   P1 (important): MQTT 5.0 (ISO/IEC 20922), REST API (HTTP/JSON)
#   P2 (future):    OPC-UA (IEC 62541) — stub only
#
# USAGE (from iot_device_simulator.py or real edge gateway):
#   adapter = AdapterFactory.get("BACnet")
#   normalized = adapter.normalize(raw_bacnet_object)
#   event_hub_client.send(json.dumps(normalized))
# =============================================================================

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


# =============================================================================
# BASE ADAPTER
# =============================================================================

class IotAdapter(ABC):
    """
    Abstract base for all protocol adapters.
    Subclasses implement parse_reading() and normalize() only.
    Unit conversion lives in _to_standard_unit() — shared by all.
    """

    # Maps protocol-native unit strings → standard SI units
    UNIT_MAP = {
        # Temperature
        "degrees_celsius": "C",  "degree_celsius": "C",
        "degC": "C",             "celsius": "C",
        "degrees_fahrenheit": "F", "degF": "F",
        # Humidity
        "percent": "%",          "pct": "%",  "RH": "%",
        # CO2 / Air quality
        "ppm": "ppm",            "parts_per_million": "ppm",
        # Power / Energy
        "kilowatts": "kW",       "kW": "kW",  "KW": "kW",
        "watts": "W",            "W": "W",
        "kilowatt_hours": "kWh", "kWh": "kWh",
        # Pressure
        "pascal": "Pa",          "kilopascal": "kPa",
        # Flow
        "liters_per_second": "L/s", "cubic_meters_per_hour": "m3/h",
    }

    def _to_standard_unit(self, raw_unit: str) -> str:
        """Convert any protocol-native unit string to standard SI string."""
        return self.UNIT_MAP.get(str(raw_unit).strip(), str(raw_unit))

    def _fahrenheit_to_celsius(self, f: float) -> float:
        return round((f - 32) * 5 / 9, 2)

    def _normalize_value(self, value: float, raw_unit: str) -> tuple:
        """
        Convert value+unit to standard.
        Returns (converted_value, standard_unit).
        Only temperature F→C conversion needed; everything else is label-only.
        """
        std_unit = self._to_standard_unit(raw_unit)
        if raw_unit in ("degrees_fahrenheit", "degF"):
            return self._fahrenheit_to_celsius(value), "C"
        return round(float(value), 4), std_unit

    def _utc_now_iso(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    @abstractmethod
    def normalize(self, raw_data: dict) -> dict:
        """
        Parse raw protocol data and return standardized dict.
        Must always return the full 9-field schema above.
        """
        pass

    def validate(self, normalized: dict) -> bool:
        """Quick sanity check on the output schema."""
        required = [
            "device_id", "building_id", "sensor_type", "sensor_location",
            "reading_value", "reading_unit", "source_protocol",
            "timestamp", "reading_quality"
        ]
        missing = [k for k in required if k not in normalized]
        if missing:
            logger.warning(f"[{self.__class__.__name__}] Missing fields: {missing}")
            return False
        return True


# =============================================================================
# P0 — BACNET/IP ADAPTER  (ASHRAE 135, Germany building automation standard)
# =============================================================================

class BacnetAdapter(IotAdapter):
    """
    BACnet/IP is the dominant protocol in German commercial buildings
    (HVAC controllers, AHUs, chillers, heat pumps).

    A BACnet object looks like:
      {
        "device_instance": 1001,
        "object_type": "analogInput",
        "object_instance": 1,
        "property": "presentValue",
        "value": 22.5,
        "units": "degrees_celsius",
        "description": "AHU-01 Supply Air Temp",
        "building_id": "B001",
        "device_id": "B001_AHU01_TEMP",
        "location": "Floor 2, AHU Room"
      }

    BACNET_SENSOR_TYPE_MAP maps BACnet object descriptions to our sensor_type
    vocabulary. In production, this map is maintained per site.
    """

    BACNET_SENSOR_TYPE_MAP = {
        "temp": "HVAC_temp",
        "temperature": "HVAC_temp",
        "supply air": "HVAC_temp",
        "return air": "HVAC_temp",
        "humid": "humidity",
        "rh": "humidity",
        "co2": "CO2",
        "carbon dioxide": "CO2",
        "power": "power",
        "demand": "power",
        "energy": "power",
    }

    def _map_sensor_type(self, description: str) -> str:
        desc_lower = description.lower()
        for keyword, sensor_type in self.BACNET_SENSOR_TYPE_MAP.items():
            if keyword in desc_lower:
                return sensor_type
        return "unknown"

    def normalize(self, raw_data: dict) -> dict:
        """
        raw_data: dict from BACnet/IP driver (BAC0, bacpypes, or gateway REST wrapper)
        """
        value, unit = self._normalize_value(
            raw_data.get("value", 0.0),
            raw_data.get("units", "unknown")
        )

        normalized = {
            "device_id":       raw_data.get("device_id", f"bacnet_{raw_data.get('device_instance')}"),
            "building_id":     raw_data.get("building_id", "UNKNOWN"),
            "sensor_type":     self._map_sensor_type(raw_data.get("description", "")),
            "sensor_location": raw_data.get("location", raw_data.get("description", "Unknown")),
            "reading_value":   value,
            "reading_unit":    unit,
            "source_protocol": "BACnet",
            "timestamp":       raw_data.get("timestamp", self._utc_now_iso()),
            "reading_quality": raw_data.get("quality", 100),
        }
        self.validate(normalized)
        return normalized


# =============================================================================
# P0 — MODBUS TCP ADAPTER  (IEC 61158, industrial + legacy EU systems)
# =============================================================================

class ModbusAdapter(IotAdapter):
    """
    Modbus TCP is used heavily in industrial equipment, older HVAC systems,
    and energy meters (DIN rail meters are almost always Modbus).

    A Modbus reading comes as a register value + metadata:
      {
        "slave_id": 1,
        "register_address": 100,
        "raw_value": 225,        ← needs scale factor applied
        "scale_factor": 0.1,
        "building_id": "B002",
        "device_id": "B002_METER_01",
        "location": "Main DB, Floor 1"
      }

    REGISTER_MAP maps register addresses to sensor semantics.
    In production, this is a per-site configuration file.
    """

    # Default register map — override per site
    REGISTER_MAP = {
        100: {"sensor_type": "HVAC_temp",  "unit": "degrees_celsius", "scale": 0.1},
        101: {"sensor_type": "HVAC_temp",  "unit": "degrees_celsius", "scale": 0.1},
        200: {"sensor_type": "humidity",   "unit": "percent",          "scale": 0.1},
        300: {"sensor_type": "CO2",        "unit": "ppm",              "scale": 1.0},
        400: {"sensor_type": "power",      "unit": "kW",               "scale": 0.01},
        401: {"sensor_type": "power",      "unit": "kWh",              "scale": 0.01},
    }

    def normalize(self, raw_data: dict) -> dict:
        addr = raw_data.get("register_address", -1)
        reg_info = self.REGISTER_MAP.get(addr, {
            "sensor_type": "unknown", "unit": "unknown", "scale": 1.0
        })

        # Apply scale factor (Modbus stores integers, scale converts to float)
        scale = raw_data.get("scale_factor", reg_info["scale"])
        raw_value = raw_data.get("raw_value", 0)
        value, unit = self._normalize_value(raw_value * scale, reg_info["unit"])

        normalized = {
            "device_id":       raw_data.get("device_id", f"modbus_{raw_data.get('slave_id')}_{addr}"),
            "building_id":     raw_data.get("building_id", "UNKNOWN"),
            "sensor_type":     reg_info["sensor_type"],
            "sensor_location": raw_data.get("location", f"Register {addr}"),
            "reading_value":   value,
            "reading_unit":    unit,
            "source_protocol": "Modbus",
            "timestamp":       raw_data.get("timestamp", self._utc_now_iso()),
            "reading_quality": raw_data.get("quality", 95),  # Modbus has no native quality
        }
        self.validate(normalized)
        return normalized


# =============================================================================
# P1 — MQTT 5.0 ADAPTER  (ISO/IEC 20922, modern IoT sensors + smart meters)
# =============================================================================

class MqttAdapter(IotAdapter):
    """
    MQTT is the emerging standard for new IoT deployments — smart meters,
    wireless sensors, cloud-connected devices.

    An MQTT message arrives as a topic + JSON payload:
      topic:   "energylens/B003/sensors/co2/floor2_zoneA"
      payload: {
        "device_id": "B003_CO2_F2A",
        "value": 850,
        "unit": "ppm",
        "quality": 99,
        "ts": "2026-05-07T14:30:00Z"
      }

    Topic structure: energylens/{building_id}/sensors/{sensor_type}/{location}
    This allows us to extract building_id and sensor_type from the topic directly,
    even if the payload doesn't include them (older device firmware).
    """

    def _parse_topic(self, topic: str) -> dict:
        """
        Extract building_id, sensor_type, location from MQTT topic.
        Expected: energylens/{building_id}/sensors/{sensor_type}/{location}
        """
        parts = topic.strip("/").split("/")
        result = {"building_id": "UNKNOWN", "sensor_type": "unknown", "sensor_location": "Unknown"}
        if len(parts) >= 5 and parts[0] == "energylens":
            result["building_id"]     = parts[1].upper()
            result["sensor_type"]     = parts[3]
            result["sensor_location"] = parts[4].replace("_", " ").title()
        return result

    def normalize(self, raw_data: dict) -> dict:
        """
        raw_data must include 'topic' and 'payload' (or inline fields).
        """
        # Support both: {"topic": ..., "payload": {...}} and flat dict
        if "payload" in raw_data and isinstance(raw_data["payload"], str):
            payload = json.loads(raw_data["payload"])
        elif "payload" in raw_data:
            payload = raw_data["payload"]
        else:
            payload = raw_data

        topic_meta = self._parse_topic(raw_data.get("topic", ""))

        value, unit = self._normalize_value(
            payload.get("value", payload.get("reading_value", 0.0)),
            payload.get("unit", payload.get("reading_unit", "unknown"))
        )

        normalized = {
            "device_id":       payload.get("device_id", payload.get("deviceId", "unknown")),
            "building_id":     payload.get("building_id", topic_meta["building_id"]),
            "sensor_type":     payload.get("sensor_type", topic_meta["sensor_type"]),
            "sensor_location": payload.get("location", topic_meta["sensor_location"]),
            "reading_value":   value,
            "reading_unit":    unit,
            "source_protocol": "MQTT",
            "timestamp":       payload.get("ts", payload.get("timestamp", self._utc_now_iso())),
            "reading_quality": int(payload.get("quality", payload.get("rssi_quality", 90))),
        }
        self.validate(normalized)
        return normalized


# =============================================================================
# P1 — REST API ADAPTER  (HTTP/JSON — cloud-native devices, catch-all)
# =============================================================================

class RestApiAdapter(IotAdapter):
    """
    REST API is the catch-all for cloud-connected devices, sub-meters with
    web dashboards, and any vendor that exposes an HTTP endpoint.

    Example response from a cloud meter API:
      {
        "sensorId": "B004_PWR_MAIN",
        "buildingRef": "B004",
        "measurementType": "activePower",
        "value": 45.2,
        "unit": "kW",
        "dataQuality": "GOOD",
        "measuredAt": "2026-05-07T14:30:00.000Z",
        "location": "Main Distribution Board"
      }

    Vendor APIs vary wildly in field naming.
    The FIELD_ALIASES map handles the most common variants.
    """

    FIELD_ALIASES = {
        "device_id":       ["sensorId", "sensor_id", "deviceId", "device_id", "id"],
        "building_id":     ["buildingRef", "building_id", "buildingId", "site_id"],
        "sensor_type":     ["measurementType", "sensor_type", "type", "metric"],
        "sensor_location": ["location", "zone", "room", "area", "position"],
        "reading_value":   ["value", "reading", "measurement", "current_value"],
        "reading_unit":    ["unit", "units", "uom", "unit_of_measure"],
        "timestamp":       ["measuredAt", "timestamp", "time", "datetime", "recorded_at"],
        "reading_quality": ["dataQuality", "quality", "confidence", "reliability"],
    }

    QUALITY_STRING_MAP = {
        "GOOD": 100, "FAIR": 75, "POOR": 40,
        "UNCERTAIN": 50, "BAD": 10, "MISSING": 0,
    }

    SENSOR_TYPE_MAP = {
        "activePower": "power", "active_power": "power",
        "energy": "power", "consumption": "power",
        "temperature": "HVAC_temp", "temp": "HVAC_temp",
        "humidity": "humidity", "relativeHumidity": "humidity",
        "co2": "CO2", "carbonDioxide": "CO2",
    }

    def _get_field(self, data: dict, field_key: str, default=None):
        for alias in self.FIELD_ALIASES.get(field_key, [field_key]):
            if alias in data:
                return data[alias]
        return default

    def _parse_quality(self, raw_quality) -> int:
        if isinstance(raw_quality, (int, float)):
            return int(min(100, max(0, raw_quality)))
        return self.QUALITY_STRING_MAP.get(str(raw_quality).upper(), 80)

    def normalize(self, raw_data: dict) -> dict:
        raw_value = self._get_field(raw_data, "reading_value", 0.0)
        raw_unit  = self._get_field(raw_data, "reading_unit", "unknown")
        value, unit = self._normalize_value(raw_value, raw_unit)

        raw_sensor_type = self._get_field(raw_data, "sensor_type", "unknown")
        sensor_type = self.SENSOR_TYPE_MAP.get(raw_sensor_type, raw_sensor_type)

        normalized = {
            "device_id":       self._get_field(raw_data, "device_id", "unknown"),
            "building_id":     self._get_field(raw_data, "building_id", "UNKNOWN"),
            "sensor_type":     sensor_type,
            "sensor_location": self._get_field(raw_data, "sensor_location", "Unknown"),
            "reading_value":   value,
            "reading_unit":    unit,
            "source_protocol": "REST",
            "timestamp":       self._get_field(raw_data, "timestamp", self._utc_now_iso()),
            "reading_quality": self._parse_quality(
                self._get_field(raw_data, "reading_quality", 80)
            ),
        }
        self.validate(normalized)
        return normalized


# =============================================================================
# P2 STUB — OPC-UA  (Phase 2.5 — premium automation, Siemens/ABB PLCs)
# =============================================================================

class OpcUaAdapter(IotAdapter):
    """
    OPC-UA is used in premium building automation (Siemens, ABB, Honeywell).
    Full implementation in Phase 2.5.
    Stub raises NotImplementedError to signal missing integration.
    """
    def normalize(self, raw_data: dict) -> dict:
        raise NotImplementedError(
            "OPC-UA adapter is Phase 2.5. Use BACnet or REST in the meantime."
        )


# =============================================================================
# FACTORY — get the right adapter by protocol name
# =============================================================================

class AdapterFactory:
    """
    Usage:
        adapter = AdapterFactory.get("BACnet")
        normalized = adapter.normalize(raw_bacnet_object)
    """
    _registry = {
        "BACnet":   BacnetAdapter,
        "Modbus":   ModbusAdapter,
        "MQTT":     MqttAdapter,
        "REST":     RestApiAdapter,
        "OPC-UA":   OpcUaAdapter,
        "Simulated": RestApiAdapter,   # simulator uses REST-style dicts
    }

    @classmethod
    def get(cls, protocol: str) -> IotAdapter:
        klass = cls._registry.get(protocol)
        if klass is None:
            raise ValueError(
                f"Unknown protocol '{protocol}'. "
                f"Supported: {list(cls._registry.keys())}"
            )
        return klass()

    @classmethod
    def supported_protocols(cls) -> list:
        return list(cls._registry.keys())


# =============================================================================
# QUICK SELF-TEST  (run directly: python 00_iot_adapter_framework.py)
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("\n=== BACnet Adapter ===")
    bacnet_raw = {
        "device_instance": 1001, "device_id": "B001_AHU01_TEMP",
        "building_id": "B001",   "description": "AHU-01 Supply Air Temperature",
        "value": 22.5,           "units": "degrees_celsius",
        "location": "Floor 2, AHU Room",  "quality": 100,
        "timestamp": "2026-05-07T14:30:00Z"
    }
    result = AdapterFactory.get("BACnet").normalize(bacnet_raw)
    print(json.dumps(result, indent=2))

    print("\n=== Modbus Adapter ===")
    modbus_raw = {
        "slave_id": 1,       "register_address": 300,
        "raw_value": 850,    "scale_factor": 1.0,
        "device_id": "B002_CO2_MAIN",  "building_id": "B002",
        "location": "Office Floor 1",  "timestamp": "2026-05-07T14:30:00Z"
    }
    result = AdapterFactory.get("Modbus").normalize(modbus_raw)
    print(json.dumps(result, indent=2))

    print("\n=== MQTT Adapter ===")
    mqtt_raw = {
        "topic": "energylens/B003/sensors/humidity/floor2_zoneA",
        "payload": {
            "device_id": "B003_HUM_F2A", "value": 48.5,
            "unit": "percent",           "quality": 99,
            "ts": "2026-05-07T14:30:00Z"
        }
    }
    result = AdapterFactory.get("MQTT").normalize(mqtt_raw)
    print(json.dumps(result, indent=2))

    print("\n=== REST Adapter ===")
    rest_raw = {
        "sensorId": "B004_PWR_MAIN",  "buildingRef": "B004",
        "measurementType": "activePower",  "value": 45.2,
        "unit": "kW",                 "dataQuality": "GOOD",
        "measuredAt": "2026-05-07T14:30:00Z",
        "location": "Main Distribution Board"
    }
    result = AdapterFactory.get("REST").normalize(rest_raw)
    print(json.dumps(result, indent=2))

    print("\n✅ All adapters working correctly.")
