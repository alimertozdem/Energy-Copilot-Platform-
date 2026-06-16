"""Built-in device template catalog (Tier-3 prefill) + normalized sensor vocab.

Picking a template prefills a device's connection defaults and seeds its point
map, so an integrator doesn't hand-enter every register. Register / object refs
are TYPICAL starting points -- the integrator verifies them against the device
manual (we never claim an exact map we can't guarantee; CLAUDE.md energy-logic
honesty rule).

sensor_type values use the normalized vocabulary the IoT pipeline expects
(CLAUDE.md Page 8 minimum set + extended), so mapped points route correctly
through the adapter framework.
"""
from app.schemas.connection import (
    DeviceTemplate,
    SensorTypeOption,
    TemplatePoint,
)

# Normalized sensor_type options (value, label, default unit). Single source of
# truth for the point-mapping dropdown + template authoring.
SENSOR_TYPES: list[SensorTypeOption] = [
    SensorTypeOption(value="building_kwh", label="Building power (total)", unit="kW"),
    SensorTypeOption(value="hvac_kwh", label="HVAC power", unit="kW"),
    SensorTypeOption(value="lighting_kwh", label="Lighting power", unit="kW"),
    SensorTypeOption(value="plug_load_kwh", label="Plug-load power", unit="kW"),
    SensorTypeOption(value="building_energy_kwh", label="Building energy (cumulative)", unit="kWh"),
    SensorTypeOption(value="heat_output_kwh", label="Heat output / delivered (thermal)", unit="kWh"),
    SensorTypeOption(value="heatpump_elec_kwh", label="Heat-pump electricity input", unit="kWh"),
    SensorTypeOption(value="HVAC_temp", label="Zone temperature", unit="°C"),
    SensorTypeOption(value="HVAC_supply_temp", label="HVAC supply temp", unit="°C"),
    SensorTypeOption(value="HVAC_return_temp", label="HVAC return temp", unit="°C"),
    SensorTypeOption(value="humidity", label="Humidity", unit="%"),
    SensorTypeOption(value="CO2", label="CO₂", unit="ppm"),
    SensorTypeOption(value="occupancy", label="Occupancy", unit="count"),
    SensorTypeOption(value="voltage", label="Voltage", unit="V"),
    SensorTypeOption(value="current", label="Current", unit="A"),
    SensorTypeOption(value="chiller_cop", label="Chiller COP", unit=None),
    SensorTypeOption(value="boiler_eff", label="Boiler efficiency", unit="%"),
    SensorTypeOption(value="pump_pressure", label="Pump pressure", unit="kPa"),
    SensorTypeOption(value="fan_rpm", label="Fan speed", unit="rpm"),
]

_TEMPLATES: list[DeviceTemplate] = [
    DeviceTemplate(
        key="schneider_pm5560",
        label="Schneider PowerLogic PM5560",
        protocol="modbus",
        description="3-phase power & energy meter (Modbus TCP). Verify register addresses against the PM5560 manual.",
        default_config={"host": "", "port": 502, "unit_id": 1},
        points=[
            TemplatePoint(point_ref="3060", sensor_type="building_kwh", unit="kW", label="Active power total"),
            TemplatePoint(point_ref="3204", sensor_type="building_energy_kwh", unit="kWh", label="Active energy delivered"),
            TemplatePoint(point_ref="3028", sensor_type="voltage", unit="V", label="Voltage L-N average"),
            TemplatePoint(point_ref="3000", sensor_type="current", unit="A", label="Current average"),
        ],
    ),
    DeviceTemplate(
        key="generic_modbus_kwh",
        label="Generic Modbus kWh meter",
        protocol="modbus",
        description="Single / 3-phase energy meter over Modbus TCP. Set the holding-register addresses for your model.",
        default_config={"host": "", "port": 502, "unit_id": 1},
        points=[
            TemplatePoint(point_ref="0", sensor_type="building_energy_kwh", unit="kWh", label="Total active energy"),
            TemplatePoint(point_ref="12", sensor_type="building_kwh", unit="kW", label="Active power"),
        ],
    ),
    DeviceTemplate(
        key="generic_bacnet_ahu",
        label="Generic BACnet AHU controller",
        protocol="bacnet",
        description="Air-handling-unit controller over BACnet/IP. Map the analog inputs to your unit's objects.",
        default_config={"device_instance": "", "host": "", "port": 47808},
        points=[
            TemplatePoint(point_ref="AI:1", sensor_type="HVAC_supply_temp", unit="°C", label="Supply air temp"),
            TemplatePoint(point_ref="AI:2", sensor_type="HVAC_return_temp", unit="°C", label="Return air temp"),
            TemplatePoint(point_ref="AI:3", sensor_type="CO2", unit="ppm", label="Return air CO2"),
            TemplatePoint(point_ref="AI:4", sensor_type="humidity", unit="%", label="Return air humidity"),
        ],
    ),
    DeviceTemplate(
        key="generic_mqtt_climate",
        label="Generic MQTT climate sensor",
        protocol="mqtt",
        description="Zone climate sensor publishing JSON over MQTT. point_ref is the JSON key in the payload.",
        default_config={"broker": "", "port": 1883, "base_topic": "building/+/climate"},
        points=[
            TemplatePoint(point_ref="temperature", sensor_type="HVAC_temp", unit="°C", label="Zone temperature"),
            TemplatePoint(point_ref="humidity", sensor_type="humidity", unit="%", label="Zone humidity"),
            TemplatePoint(point_ref="co2", sensor_type="CO2", unit="ppm", label="Zone CO2"),
        ],
    ),
]

_BY_KEY = {t.key: t for t in _TEMPLATES}


def list_templates() -> list[DeviceTemplate]:
    """All built-in device templates."""
    return list(_TEMPLATES)


def get_template(key: str) -> DeviceTemplate | None:
    """Look up a template by key, or None."""
    return _BY_KEY.get(key)
