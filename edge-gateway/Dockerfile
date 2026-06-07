# EnergyLens Edge Gateway — live OPC-UA + Modbus ingestion
#
# Build from the REPO ROOT so the shared adapter can be vendored into the image:
#   docker build -f edge-gateway/Dockerfile -t energylens-gateway .
#
# Run (smoke tests, no server needed):
#   docker run --rm energylens-gateway --selftest                       # OPC-UA
#   docker run --rm --entrypoint python energylens-gateway modbus_gateway.py --selftest
#
# Run (production):
#   # OPC-UA -> Event Hub:
#   docker run --rm energylens-gateway \
#     --connect opc.tcp://plc.host:4840 --nodes "ns=2;s=B005.Chiller1.COP" \
#     --sink eventhub --eh-conn "<conn>" --eh-name iot-raw --batch 100
#   # Modbus -> Event Hub (platform-pull, config from the /connections web UI):
#   docker run --rm -e AGENT_TOKEN="<token>" -e EVENTHUB_CONN="<conn>" \
#     --entrypoint python energylens-gateway modbus_gateway.py \
#     --platform https://api.energylens.eu --building <UUID> \
#     --sink eventhub --eh-conn "$EVENTHUB_CONN" --eh-name iot-raw --seconds 0
FROM python:3.12-slim

WORKDIR /app

# 1) dependencies (asyncua + pymodbus + azure-eventhub)
COPY edge-gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) vendor the shared adapter — load_adapter() prefers ./iot_adapter_framework.py
COPY notebooks/iot/00_iot_adapter_framework.py ./iot_adapter_framework.py

# 3) the gateways (modbus_gateway imports opcua_gateway for the shared sink infra)
COPY edge-gateway/opcua_gateway.py .
COPY edge-gateway/modbus_gateway.py .
COPY edge-gateway/bacnet_gateway.py .
COPY edge-gateway/mqtt_gateway.py .
COPY edge-gateway/rest_gateway.py .
COPY edge-gateway/run_agent.py .
COPY edge-gateway/config.example.json .
COPY edge-gateway/config.modbus.example.json .
COPY edge-gateway/config.bacnet.example.json .
COPY edge-gateway/config.mqtt.example.json .
COPY edge-gateway/config.rest.example.json .

# Default entrypoint = OPC-UA gateway; override for Modbus:
#   --entrypoint python ... modbus_gateway.py ...
ENTRYPOINT ["python", "opcua_gateway.py"]
CMD ["--selftest"]
