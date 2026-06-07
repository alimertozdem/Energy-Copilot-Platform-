# EnergyLens Edge Gateway — Live OPC-UA / SCADA Ingestion (F-full)

The **live counterpart** to the protocol adapter library
(`notebooks/iot/00_iot_adapter_framework.py`). The adapter is a pure transform
(raw protocol message → standard event); this gateway is the **live session**
that connects to an OPC-UA server (a real SCADA/PLC or a simulator), subscribes
to monitored nodes, normalizes each value change via the shared `OpcUaAdapter`,
and forwards the standard event to a **sink** (Azure Event Hub in production).

This component runs on an **edge device or an always-on container** — it is not
a Fabric notebook. It is the piece that was deferred as "Phase 2.5 / F-full".

## Run modes

```bash
# 1) Self-test — no dependencies. Proves the adapter→sink pipeline.
python opcua_gateway.py --selftest

# 2) Simulated server — proves the live OPC-UA path end-to-end, no hardware.
pip install asyncua
python opcua_gateway.py --sim --seconds 6

# 3) Production — connect to a real OPC-UA server, forward to Event Hub.
pip install asyncua azure-eventhub
python opcua_gateway.py \
  --connect opc.tcp://plc.host:4840 \
  --nodes "ns=2;s=B005.Chiller1.COP" "ns=2;s=B001.AHU1.SupplyAirTemp" \
  --sink eventhub --eh-conn "<connection-string>" --eh-name "<hub-name>"
```

The Event Hub sink feeds the **same** ingestion path the rest of the platform
already uses (Event Hub → EventStream → KQL/Lakehouse → `silver_iot_normalized`
→ `gold_iot_realtime` / `gold_iot_fdd`). No downstream change is needed.

## What is verified vs. what needs your environment

- ✅ **Verified here:** `--selftest` (adapter pipeline) + Python syntax.
- ▶️ **Run in your environment** (`pip install` works there): `--sim` for the
  live OPC-UA loop, `--connect` for a real PLC.

## Config-driven deployment (per site)

Instead of long CLI flags, point the gateway at a per-site JSON config:

```bash
cp config.example.json config.frankfurt.json   # edit server_url + nodes
export OPCUA_PASSWORD=...        # secrets via env, never in the file
export EVENTHUB_CONN=...
python opcua_gateway.py --config config.frankfurt.json --seconds 0   # 0 = run forever
```

The config carries `server_url`, `security`, `username` + `password_env`,
`sink` (type + `eventhub_name` + `connection_env`), `batch`, `max_retries`, and
a `nodes` list. Each node may set `sensor_type` / `building_id` / `unit`
explicitly — these **override** the adapter's browse-name heuristic, which
matters because real PLC browse names are often cryptic. Nodes without overrides
fall back to the heuristic (browse name → sensor_type).

### OPC-UA client certificate (for `security`)

Secured OPC-UA channels need a client cert + key, and the cert must carry an
application URI in its SAN:

```bash
openssl req -x509 -newkey rsa:2048 -days 3650 -nodes \
  -keyout client-key.pem -outform der -out client-cert.der \
  -subj "/CN=EnergyLens Gateway/O=EnergyLens" \
  -addext "subjectAltName=URI:urn:energylens:gateway"
```

Then set `security` to e.g.
`"Basic256Sha256,SignAndEncrypt,/certs/client-cert.der,/certs/client-key.pem"`
and register the client cert as trusted on the server/PLC (vendor-specific).

## Testing & CI

```bash
python opcua_gateway.py --selftest    # adapter + batching + backoff + config (no deps)
python test_opcua_gateway.py          # same checks, standalone (no pytest needed)
pytest test_opcua_gateway.py -v       # CI form
```

`.github/workflows/edge-gateway-ci.yml` runs the self-test + pytest on every push
that touches `edge-gateway/`. None of these need `asyncua` or Azure — the
adapter pipeline and config loader are pure Python.

**Graceful shutdown:** on `SIGTERM` / `SIGINT` the gateway cancels its run loop,
disconnects the OPC-UA client, and flushes the buffered sink — so a container
stop (or Ctrl-C) never drops buffered events.

## Hardening status

**Done (Increment 1–2 — verified by `--selftest` + `py_compile`):**

- Live OPC-UA client + subscription (`--sim` simulator, `--connect` real server).
- Buffered batching sink (`--batch N`) — fewer Event Hub round-trips under load.
- Auto-reconnect with exponential backoff (`--max-retries`, `0` = retry forever).
- TLS + auth wiring (`--security "Policy,Mode,cert,key"`, `--user`, `--password`).
- Container-friendly adapter loading + `Dockerfile` (vendors the adapter into the image).
- Config-driven per-site deployment (`--config`) with per-node sensor_type/building_id overrides.
- Graceful shutdown (SIGTERM/SIGINT → flush buffer + clean disconnect).
- Tests (`test_opcua_gateway.py`) + GitHub Actions CI (`--selftest` + pytest).

**Remaining (needs a real environment / pilot):**

- Run `--sim` / `--connect` live — needs `pip install asyncua` (PyPI was blocked in
  the dev sandbox, so only the dependency-free `--selftest` ran here).
- Real OPC-UA certificates + a per-site node-map config file.
- Hosting: Azure Container Apps (~€10–30/mo) or an on-prem edge device.
- Build / push the image (from repo root):
  `docker build -f edge-gateway/Dockerfile -t energylens-gateway .`

---

# EnergyLens Edge Gateway — Live Modbus TCP Ingestion (Tier 2, P0)

The **Modbus TCP** counterpart to `opcua_gateway.py`. Modbus is the most
widespread protocol on EU energy meters and legacy HVAC (DIN-rail meters are
almost always Modbus). Unlike OPC-UA (subscribe), Modbus is **poll-based**: the
gateway reads each configured holding register every `--interval` seconds,
normalizes via the shared `ModbusAdapter`, and forwards to the same sink → Event
Hub → EventStream → Lakehouse path. **No downstream change** — it produces the
identical standard event schema.

It reuses the verified sink / batching / backoff / graceful-shutdown
infrastructure from `opcua_gateway.py` (single source) and injects the
per-site **register map** (register → `sensor_type` + unit + scale) from config,
so the adapter is fully config-driven without touching the framework.

## Run modes

```bash
# 1) Self-test — no deps. Adapter+map, scaling, batching, backoff, config, platform-parse.
python modbus_gateway.py --selftest

# 2) Built-in MOCK device — no pymodbus. Proves the poll→adapter→sink loop.
python modbus_gateway.py --sim --seconds 6 --interval 1 --batch 50

# 3) Production — per-site config (devices, register map, sink). Secrets via env.
cp config.modbus.example.json config.modbus.frankfurt.json   # edit host + registers
export EVENTHUB_CONN=...
python modbus_gateway.py --config config.modbus.frankfurt.json --seconds 0   # 0 = forever

# 4) Platform-pull — fetch the device/point map straight from the web app.
export AGENT_TOKEN=...      # issued in the /connections "Edge agent" panel
python modbus_gateway.py --platform https://api.energylens.eu --building <UUID> \
  --sink eventhub --eh-conn "$EVENTHUB_CONN" --eh-name iot-raw --seconds 0

# 5) Ad-hoc single device.
pip install pymodbus
python modbus_gateway.py --connect --host 192.168.1.50 --unit-id 1 \
  --registers 3060:building_kwh:kW:1 3204:building_energy_kwh:kWh:0.01 --building-id B005
```

`point.register` is the Modbus **holding-register address** — verify it against
the device manual (the templates in the web app are typical starting points,
not guaranteed maps). `scale` converts the raw integer register to the standard
unit (e.g. Wh→kWh = 0.001; a ×0.1 temperature meter = 0.1).

## Platform-pull (convergence with the /connections page)

`--platform` pulls `GET /agent/config` from the EnergyLens backend, authenticated
with a **building-scoped agent token** (`X-Agent-Token`) — a separate credential
from a user login. The same devices + points you configure in the web UI drive
the gateway; no second config file to keep in sync. Only `protocol: "modbus"`
devices with numeric `point_ref`s are polled (others are skipped with a warning).

## Testing & CI

```bash
python modbus_gateway.py --selftest    # adapter + map + batching + backoff + config + platform (no deps)
python test_modbus_gateway.py          # standalone (no pytest)
pytest test_modbus_gateway.py -v       # CI form
```

`--connect` / `--config` / `--platform` live reads need `pip install pymodbus`
(blocked in the dev sandbox, so only the dependency-free `--selftest` + `--sim`
ran here). `azure-eventhub` is only needed for `--sink eventhub`.

---

# EnergyLens Edge Gateway — Live BACnet/IP Ingestion (Tier 2, P0, Germany)

The **BACnet/IP** (ASHRAE 135) gateway — the dominant protocol in German
commercial building automation (AHUs, chillers, heat pumps, controllers). It
mirrors `modbus_gateway.py`: poll the configured objects every `--interval`,
normalize via the shared `BacnetAdapter`, forward to the same sink → Event Hub
path. It reuses the sink / batching / backoff / graceful-shutdown infrastructure
from `opcua_gateway.py`.

`point_ref` is `"<objtype>:<instance>"` — `AI:1` (analogInput 1), `AV:3`
(analogValue 3), `BI:2` (binaryInput 2), `MSV:1` (multiStateValue 1). Because the
adapter guesses `sensor_type` from a free-text description, and our /connections
config carries an **explicit** sensor_type per object, the gateway **overrides**
the guess with the configured value after normalize (the adapter still does the
value/unit conversion — e.g. °F→°C — and quality).

## Run modes

```bash
python bacnet_gateway.py --selftest        # adapter + override + parse + config + platform (no deps)
python bacnet_gateway.py --sim --seconds 6 # built-in MOCK device (no BAC0)
python bacnet_gateway.py --config config.bacnet.frankfurt.json --seconds 0
export AGENT_TOKEN=...                      # issued in the /connections "Edge agent" panel
python bacnet_gateway.py --platform https://<api-host> \
  --sink eventhub --eh-conn "$EVENTHUB_CONN" --eh-name iot-raw --seconds 0
pip install BAC0
python bacnet_gateway.py --connect --host 192.168.1.60 --device-instance 1001 \
  --objects AI:1:HVAC_supply_temp:degC AI:3:CO2:ppm --building-id B001
```

`--connect` / `--config` / `--platform` live reads need `pip install BAC0`
(blocked in the dev sandbox, so only the dependency-free `--selftest` + `--sim`
ran here). `--platform` pulls only `protocol: "bacnet"` devices with valid
object refs from `/agent/config`.

## Testing & CI

```bash
python bacnet_gateway.py --selftest
python test_bacnet_gateway.py          # standalone (no pytest)
pytest test_bacnet_gateway.py -v       # CI form
```

---

# EnergyLens Edge Gateway — Live MQTT + REST Ingestion (Tier 2, P1)

The two **P1** protocols complete the interoperability matrix — every adapter in
`notebooks/iot/00_iot_adapter_framework.py` now has a live gateway.

**MQTT** (`mqtt_gateway.py`, subscribe-based, ISO/IEC 20922) — for smart meters
and wireless/cloud sensors. Subscribes to each device's base topic; every JSON
message yields one event per configured point (`point_ref` = a key in the
payload). `pip install paho-mqtt`.

**REST** (`rest_gateway.py`, poll-based, HTTP/JSON) — the catch-all for cloud
sub-meters and vendor APIs. GETs each endpoint every interval; `point_ref` is a
field or dotted path in the response (e.g. `data.meter.power`). **stdlib only**
(urllib) — no extra dependency for the HTTP read.

Both reuse the shared sink / batching / backoff / graceful-shutdown, are
config-driven, and support `--platform` (pull `protocol:"mqtt"` / `"rest_api"`
devices from `/agent/config`). The MQTT/REST adapters already honour explicit
`sensor_type` / `building_id` / `unit`, so the config passes straight through.

```bash
python mqtt_gateway.py --selftest      # / --sim    (mock broker, no paho)
python rest_gateway.py --selftest      # / --sim    (mock endpoint, no network)

python mqtt_gateway.py --config config.mqtt.frankfurt.json --seconds 0
python rest_gateway.py --platform https://<api-host> --agent-token "$AGENT_TOKEN" \
  --sink eventhub --eh-conn "$EVENTHUB_CONN" --eh-name iot-raw --seconds 0
```

## Protocol matrix (all live)

| Protocol  | Gateway              | Priority | Pattern   | Live dep    |
|-----------|----------------------|----------|-----------|-------------|
| BACnet/IP | `bacnet_gateway.py`  | P0 (DE)  | poll      | BAC0        |
| Modbus TCP| `modbus_gateway.py`  | P0       | poll      | pymodbus    |
| MQTT      | `mqtt_gateway.py`    | P1       | subscribe | paho-mqtt   |
| REST/HTTP | `rest_gateway.py`    | P1       | poll      | stdlib      |
| OPC-UA    | `opcua_gateway.py`   | P2       | subscribe | asyncua     |

All five share the adapter framework, the sink/batching/backoff infra, the
`--platform` config bridge, and a dependency-free `--selftest` + `--sim`.

---

# Unified Agent Launcher — one command per building

`run_agent.py` runs a building's WHOLE mixed-protocol fleet from a single
`/agent/config` pull. It groups the building's devices by protocol and runs each
gateway (Modbus, BACnet, MQTT, REST) concurrently against one shared sink — so a
site with a Modbus meter, a BACnet AHU and an MQTT sensor needs one process, not
three.

```bash
python run_agent.py --selftest      # dispatch logic (no deps)
python run_agent.py --sim           # built-in mixed fleet, all mock (no deps)

export AGENT_TOKEN=...               # issued in the /connections "Edge agent" panel
python run_agent.py --platform https://<api-host> \
  --sink eventhub --eh-conn "$EVENTHUB_CONN" --eh-name iot-raw --seconds 0
```

Install only the protocol libraries the building actually uses (`pymodbus`,
`BAC0`, `paho-mqtt`; REST is stdlib). OPC-UA keeps its own command
(`opcua_gateway.py`) — it uses a node-id model rather than the device/point map.
