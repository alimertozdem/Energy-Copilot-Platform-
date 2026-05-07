# Page 8 — EventStream Setup Guide
**Energy Copilot Platform | IoT Real-Time Monitoring**
**Estimated time: ~45 minutes | Skill level: Intermediate**

---

## What You're Building

```
Python Simulator  →  Azure Event Hub  →  Fabric EventStream
                                               ↙            ↘
                                     KQL Eventhouse    Lakehouse (bronze_iot_raw)
                                          ↓                     ↓
                                   Power BI Cards       Notebook 11b (15min)
                                   (live, seconds)       → gold tables
                                                          → Power BI Trends
```

---

## STEP 0 — Prerequisites

Before starting, ensure you have:
- [ ] Active Microsoft Fabric trial (fabric.microsoft.com)
- [ ] Azure subscription (free tier works) — for Event Hub
- [ ] Python 3.10+ installed on your machine
- [ ] Installed: `pip install azure-eventhub python-dotenv`

---

## STEP 1 — Create Azure Event Hub

**Where:** portal.azure.com

### 1.1 Create Event Hub Namespace
1. Search → "Event Hubs" → Create
2. Fill in:
   - **Subscription:** your subscription
   - **Resource Group:** create new → `rg-energylens`
   - **Namespace name:** `energylens-iot` *(must be globally unique — add random suffix if taken)*
   - **Location:** West Europe (Germany North if available)
   - **Pricing tier:** Basic (free for trial, sufficient for our volume)
3. Click **Review + Create** → Create
4. Wait ~2 minutes for deployment

### 1.2 Create Event Hub (inside the Namespace)
1. Open the namespace → **+ Event Hub**
2. Fill in:
   - **Name:** `sensor-readings`
   - **Partition count:** 2 (sufficient for our 24 sensors)
   - **Retention:** 1 day
3. Create

### 1.3 Get Connection String (needed for simulator)
1. In the namespace → **Shared access policies** → **RootManageSharedAccessKey**
2. Copy **Connection string–primary key**
3. Save as environment variable:
   ```bash
   # Windows
   set EVENTHUB_CONNECTION_STRING="Endpoint=sb://energylens-iot.servicebus.windows.net/;SharedAccessKeyName=..."
   
   # Or create .env file in sample-data/ folder:
   EVENTHUB_CONNECTION_STRING=Endpoint=sb://energylens-iot.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=XXXXX
   ```

---

## STEP 2 — Create KQL Eventhouse in Fabric

**Where:** app.fabric.microsoft.com

### 2.1 Create Eventhouse
1. In Fabric workspace → **New** → **Eventhouse**
2. Name: `iot_eventhouse`
3. Wait for creation (~1 min)

### 2.2 Run KQL Schema Script
1. Inside `iot_eventhouse` → **New KQL Queryset**
2. Open file: `semantic-model/kql/iot_schema.kql`
3. Copy-paste the **entire file content** into the queryset
4. Click **Run All** (or run each section separated by blank lines)
5. Verify:
   ```kql
   .show tables
   // Should show: iot_hot_readings, iot_anomaly_alerts, iot_sensor_master
   ```

---

## STEP 3 — Create EventStream

**Where:** app.fabric.microsoft.com (same workspace)

### 3.1 Create EventStream
1. Fabric workspace → **New** → **Eventstream**
2. Name: `iot_sensor_stream`

### 3.2 Add Source — Azure Event Hub
1. In EventStream canvas → **Add Source** → **Azure Event Hub**
2. Fill in:
   - **Connection:** Create new connection
     - **Event Hub namespace:** `energylens-iot`
     - **Event Hub:** `sensor-readings`
     - **Authentication:** Shared Access Key
     - Key name: `RootManageSharedAccessKey`
     - Key value: (from Step 1.3)
   - **Consumer group:** `$Default`
   - **Data format:** JSON

### 3.3 Add Transformation — EventStream Transform
After the source, add a **Manage Fields** transform to:
- Keep all fields (pass-through)
- This is where you would add custom routing logic later

### 3.4 Add Destination 1 — KQL Eventhouse
1. Click **+** after the transform → **Destination** → **KQL Database**
2. Fill in:
   - **Workspace:** your workspace
   - **KQL Database:** `iot_eventhouse`
   - **Destination table:** `iot_hot_readings`
   - **Input data format:** JSON
   - **Mapping:** `iot_readings_mapping` *(created in Step 2.2)*
3. Click **Save**

### 3.5 Add Destination 2 — Lakehouse (Bronze)
1. Click **+** after the transform → **Destination** → **Lakehouse**
2. Fill in:
   - **Workspace:** your workspace
   - **Lakehouse:** your existing lakehouse (EnergyLens)
   - **Root folder:** Tables
   - **Delta table name:** `bronze_iot_raw`
   - **Input data format:** JSON
3. Click **Save**

### 3.6 Publish the EventStream
Click **Publish** (top right). Status should show **Running**.

---

## STEP 4 — Test with Simulator

### 4.1 Send Batch Data (backfill 24h)
```bash
cd sample-data
python iot_device_simulator.py --mode batch --count 96
```
Expected output:
```
2026-05-07T14:30:00 [INFO] Batch mode: 96 readings/sensor from ...
2026-05-07T14:30:02 [INFO] Generated 2304 readings | 227 anomalies (9.9%)
2026-05-07T14:30:05 [INFO] Sent 2304 readings to Event Hub.
```

### 4.2 Verify in KQL Eventhouse
Go to Fabric → `iot_eventhouse` → New KQL Queryset:
```kql
// Should show data arriving
iot_hot_readings
| count

// Should show anomalies auto-populated
iot_anomaly_alerts
| count

// Latest readings
iot_hot_readings
| top 10 by ingestion_time desc
| project ingestion_time, building_id, sensor_type, reading_value, is_anomaly
```

### 4.3 Export Sensor Master CSV
```bash
python iot_device_simulator.py --mode sensor-master
```
This creates `gold_iot_sensor_master.csv`. Upload to Fabric Lakehouse:
1. Fabric Lakehouse → Files → Upload → select `gold_iot_sensor_master.csv`
2. Right-click → **Load to Delta table** → name: `gold_iot_sensor_master`

### 4.4 Start Continuous Simulation (for live demo)
```bash
python iot_device_simulator.py --mode continuous --interval 15
```
This sends a reading every 15 seconds — Power BI will show live updates.

---

## STEP 5 — Import and Schedule Notebook 11b

### 5.1 Import Notebook
1. Fabric workspace → **New** → **Notebook**
2. Click **Import notebook** → select `notebooks/iot/11b_iot_processing.py`
3. Name: `11b_iot_processing`
4. Attach to your existing Lakehouse

### 5.2 Run Once Manually
Click **Run All** to verify it works end-to-end:
- Input: `bronze_iot_raw` (Delta table)
- Output: `gold_iot_realtime`, `gold_iot_daily_summary`

Expected: no errors, tables appear in Lakehouse

### 5.3 Schedule Every 15 Minutes
1. In the notebook → **Schedule** (top ribbon)
2. Fill in:
   - **Scheduled run:** On
   - **Repeat:** Every 15 minutes
   - **Start time:** now
3. Save schedule

---

## STEP 6 — Connect Power BI

### 6.1 Connect to KQL Eventhouse (for live cards C1-C4)
1. Power BI Desktop → **Get Data** → **Microsoft Fabric** → **KQL Database**
2. Cluster URL: found in Fabric Eventhouse → Overview → **Query URI**
   (looks like: `https://xxxxxxxx.z1.kusto.fabric.microsoft.com`)
3. Database: `iot_eventhouse`
4. Select tables: `iot_hot_readings`, `iot_anomaly_alerts`
5. Import mode: **DirectQuery** ← IMPORTANT for real-time behavior

### 6.2 Connect to Gold Tables (for trend visuals V1-V4)
These are already in your existing semantic model (DirectLake from Lakehouse).
After Notebook 11b runs, these tables will appear:
- `gold_iot_realtime`
- `gold_iot_daily_summary`

---

## STEP 7 — Validate

Run these checks before building the Power BI page:

```kql
// Check 1: Data is flowing (should have 2000+ rows after batch)
iot_hot_readings | count

// Check 2: All 6 buildings present
iot_hot_readings
| distinct building_id
| order by building_id

// Check 3: All 4 sensor types present
iot_hot_readings
| distinct sensor_type

// Check 4: Anomalies are populating
iot_anomaly_alerts | count
// Should be ~10% of iot_hot_readings count

// Check 5: High severity alerts exist
iot_anomaly_alerts
| where anomaly_severity == "High"
| count
// Should be > 0
```

---

## Troubleshooting

| Issue | Solution |
|---|---|
| EventStream shows "Disconnected" | Check Event Hub connection string, ensure firewall allows outbound |
| KQL table empty after sending | Check EventStream destination mapping name matches exactly |
| bronze_iot_raw not created | EventStream Lakehouse destination needs to have "Auto-create table" enabled |
| Notebook 11b fails | Run `%pip install` cell first, check Lakehouse attachment |
| Power BI shows no data | Confirm DirectQuery mode (not Import) for KQL connection |

---

## Architecture Summary (for stakeholder conversations)

**"How does this work?"**

> Every building sends sensor data (temperature, CO2, power) in real time to a cloud message broker called Azure Event Hub. Fabric EventStream reads those messages the moment they arrive and writes them in two places simultaneously: a KQL database for instant queries, and a data lake for long-term storage. Power BI reads both — the KQL database for live dashboard cards, and the data lake for historical trend charts.

**"Is this production-ready?"**

> Yes. The only difference between this and a live deployment is the data source: right now it's a Python simulator. When a real building connects their BACnet controller or MQTT sensor, they point it at the same Event Hub endpoint. Nothing else changes — not the database, not the dashboard, not any code.

**"What protocols do you support?"**

> BACnet/IP (German standard for HVAC), Modbus TCP (industrial/legacy), MQTT (modern IoT sensors), and REST API (cloud devices). OPC-UA coming in Phase 2.5 for premium automation systems.
