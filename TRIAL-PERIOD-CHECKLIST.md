# ⏰ 14-DAY TRIAL PERIOD CHECKLIST
**Trial Period:** 2026-05-07 → 2026-05-21 | **Deadline:** 2026-05-21 23:59

---

## 🔴 CRITICAL PATH (Must-Have)

These tasks MUST be completed before trial expires. Without them, project cannot continue.

### WEEK 1 (Days 1-7)

#### Day 1-2: Architecture & Data Model Finalization
- [ ] **Page 8 Data Model** — Review `page8-iot-realtime-design.md`
  - Approve: `gold_iot_realtime`, `gold_iot_sensor_master`, `gold_iot_daily_summary` schema
  - Finalize sensor types, thresholds, anomaly rules
- [ ] **Page 9 Data Model** — Review `page9-battery-strategy-design.md`
  - Approve: `gold_battery_dispatch`, `gold_battery_simulation`, `gold_battery_daily_summary`
  - Finalize 3 dispatch strategies, cost assumptions (€/kWh)
- [ ] **Energy logic review** (Mert)
  - Anomaly thresholds realistic? (e.g., CO₂ > 1500ppm = alert)
  - Payback calculations correct? (cost ÷ annual savings)
  - Battery lifespan assumptions (LFP 10yr, NCA 8yr)

#### Day 3-4: Dummy Data Generation
- [ ] **IoT data generator** (`sample-data/iot_sensor_generator.py`)
  - Generate 6 buildings × 4 sensors × 96 readings = 2,304+ rows
  - Inject 10% anomalies (spike, drift, threshold violations)
  - Output: `bronze_iot_raw.csv`
- [ ] **Battery data simulator** (`sample-data/battery_simulator.py`)
  - 3 scenarios × 6 buildings × 30 days = 540+ rows
  - 3 dispatch strategies (SC, PS, TOU)
  - Output: `gold_battery_dispatch.csv`, `gold_battery_simulation.csv`
- [ ] **Upload to Fabric** (bronze layer)
  - `bronze_iot_raw` table created
  - `bronze_battery_raw` table created

#### Day 5-6: Fabric Pipelines (Notebooks 11b & 12)
- [ ] **Notebook 11b** (`11b_iot_ingestion_and_agg.py`)
  - Input: `bronze_iot_raw`
  - Output: `gold_iot_realtime`, `gold_iot_sensor_master`, `gold_iot_daily_summary`
  - RUN & VALIDATE: all 3 tables have data, no nulls in key columns
- [ ] **Notebook 12** (`12_battery_dispatch_and_simulation.py`)
  - Input: `gold_kpi_daily` (consumption), battery readings
  - Output: `gold_battery_dispatch`, `gold_battery_simulation`, `gold_battery_daily_summary`
  - RUN & VALIDATE: all 3 tables, scenario data populated

#### Day 7: Backup & Startup Application
- [ ] **Startup Programs Application** (CRITICAL)
  - **Sign up:** https://startups.microsoft.com
  - **Apply for:** Microsoft for Startups Founders Hub
  - **Request:** Fabric capacity grants + Power BI Premium credits
  - **Timeline:** Expect response 2-4 weeks (before trial ends!)
- [ ] **Full Backup** (prevent trial data loss)
  - Export all Fabric notebooks as `.py` files → Git
  - Export Power BI `.pbix` → versioned backup
  - Export all sample data `.csv` files → `/sample-data`
  - COMMIT to GitHub with message: "Day 7 Backup — Pre-trial-end state"

---

### WEEK 2 (Days 8-14)

#### Day 8-9: Power BI DAX (Page 8-9 Measures)
- [ ] **Page 8 DAX** (v43-v45)
  - [ ] C1-C4 KPI cards (HVAC status, temp variance, CO₂, alerts)
  - [ ] V1 24h temperature trend (line chart)
  - [ ] V2 sensor network status (heatmap)
  - [ ] V3 temp vs humidity (scatter)
  - [ ] V4 real-time readings (table)
  - **Test:** Each measure returns realistic values (no errors, no blanks)

- [ ] **Page 9 DAX** (v46-v52)
  - [ ] C1-C4 KPI cards (annual savings, payback, CO₂, efficiency)
  - [ ] V1 30-day SoC trend (area chart)
  - [ ] V2 charge/discharge daily (stacked bar)
  - [ ] V3 scenario comparison (table)
  - [ ] V4 ROI gauge (annual savings %)
  - [ ] V5 cost vs payback (scatter bubble)
  - **Test:** Scenarios rank logically (best = top right in V5)

#### Day 10-11: Power BI UI (Page 8-9 Binding)
- [ ] **Page 8 Layout**
  - Place C1-C4 cards (top row)
  - Place V1 (wide, center-top)
  - Place V2 + V3 (side-by-side, middle)
  - Place V4 (full-width, bottom)
  - [ ] Bind all visuals to DAX measures
  - [ ] Add slicers: building_id, sensor_type, date range
  - [ ] Color scheme: consistent with Pages 1-7 (blue for IoT)

- [ ] **Page 9 Layout**
  - Place C1-C4 cards (top row)
  - Place V1 (wide, center-top)
  - Place V2 + V4 (side-by-side, middle)
  - Place V3 (full-width, middle-bottom)
  - Place V5 (full-width, bottom)
  - [ ] Bind all visuals to DAX measures
  - [ ] Add slicers: building_id, scenario_id, date range
  - [ ] Color scheme: consistent (green for battery/positive)

#### Day 12: Full Validation (All 9 Pages)
- [ ] **Pages 1-7 Spot Check**
  - [ ] Each page loads without error (< 5 seconds)
  - [ ] Slicers work (building, date, metric filters)
  - [ ] No `--` values in KPI cards (unless intentional BLANK)
  - [ ] Visual colors consistent across pages
  - [ ] DAX measures return realistic data ranges

- [ ] **Page 8 Validation**
  - [ ] C1 HVAC status text is present ("Normal", "Low", "High")
  - [ ] C4 active alerts > 0 (verify anomaly detection)
  - [ ] V1 shows 24-hour temperature trend (not flat)
  - [ ] V2 heatmap shows sensor uptime 85-100%
  - [ ] V4 table shows action_recommended text (not blank)

- [ ] **Page 9 Validation**
  - [ ] C1 annual savings €800-2500 range realistic
  - [ ] C2 payback 5-10 years (LFP scenarios)
  - [ ] C3 CO₂ reduction > 0
  - [ ] V1 shows SoC variation (not flat 50%)
  - [ ] V3 scenarios ranked by score (highest at top)
  - [ ] V5 scatter shows cost vs payback trade-off visually

#### Day 13: Documentation & Version Control
- [ ] **README Updates**
  - Add Page 8 & 9 descriptions to main README
  - Link to `page8-iot-realtime-design.md` and `page9-battery-strategy-design.md`

- [ ] **DAX Documentation**
  - Create `dax-measures-page8.md` (v43-v45 explanations)
  - Create `dax-measures-page9.md` (v46-v52 explanations)
  - Include: measure name, formula, assumptions, expected range

- [ ] **Data Model Documentation**
  - Create `data-model-iot.md` (page8 schema)
  - Create `data-model-battery.md` (page9 schema)
  - Include: table names, columns, relationships, assumptions

- [ ] **GitHub Commit**
  - Commit message: "Complete Pages 8-9 DAX, layout, documentation (Day 13)"
  - Push all files (`.pbix`, notebooks, `.py` scripts, `.md` docs)

#### Day 14: Final Checks & Preparation for Post-Trial
- [ ] **Startup Status Check**
  - Confirm Microsoft application submitted ✅
  - If approved: document approval date, grant amount
  - If pending: note expected response date (may be after trial)

- [ ] **Fabric Trial Extension** (optional, try Microsoft support)
  - Contact Azure support: "Startup program in progress, can trial be extended?"
  - Mention: application submitted, needs validation time
  - Success rate: ~30%, worth trying

- [ ] **Cost Estimate for Post-Trial**
  - **Scenario A (Startup wins):** €0/month ✅
  - **Scenario B (Fallback P1):** €32/month
  - **Scenario C (Hybrid):** €32/month + €10-20/month storage
  - Decide: which scenario acceptable for next 3 months?

- [ ] **Final Backup & Archive**
  - Export final `.pbix` with all 9 pages complete
  - Export all Python scripts (sample data, pipelines)
  - Export all markdown docs
  - Create release branch: `release/v1.0-trial-complete`
  - COMMIT with message: "Trial complete — all 9 pages ready for production setup"

- [ ] **Power BI Publish Settings**
  - Note current workspace settings (capacity, refresh schedule)
  - Document which reports are "production-ready"
  - Check: is scheduling disabled (to avoid costs on trial)?

---

## 🟢 HIGH-PRIORITY (Should Complete)

These tasks improve quality but won't block launch if missed.

#### Performance Testing
- [ ] Measure report load time: Page 1 vs Page 8 vs Page 9
  - Goal: all < 5 seconds on 6 buildings, 30-day data
  - If > 10s: may need DAX optimization (aggregation tables)

#### Color Consistency
- [ ] Apply `theme-factory` skill to standardize colors across all 9 pages
  - Goal: consistent palette (blues for monitoring, greens for positive, reds for alerts)

#### Slicer Configuration
- [ ] Edit interactions (slicers should affect correct visuals)
  - Example: Page 8 `building_id` slicer should filter V1-V4 but not affect Page 1-7
  - Test: select building → visuals update, no cross-page affects

---

## 🟡 NICE-TO-HAVE (Can Skip If Running Out of Time)

These are polish items:

- [ ] Add bookmark views (e.g., "24h Alert Summary", "30-day SoC Overview")
- [ ] Create on-screen instructions (text boxes explaining each visual)
- [ ] Add drill-through buttons (e.g., click building name → detail page)
- [ ] Create print-friendly layout (landscape, margins set)

---

## 📊 TRACKING

### Progress Template (Track Daily)

```
[Date]              | [Task] | [Owner] | [Status] | [Notes]
2026-05-08          | Page 8 data model finalize | Mert | ✅ Done | Approved 3 schema, threshold: CO₂ > 1500ppm
2026-05-09          | IoT dummy data generator | Claude | ✅ Done | 2304 rows generated, 10% anomalies
...
```

### Red Flags (Alert If Happening)

⚠️ **If Fabric notebook errors:**
- Stop immediately, debug (don't continue blind)
- Error pattern typically: schema mismatch or missing column
- Check: bronze table has all expected columns?

⚠️ **If Power BI measure returns `--` or ERROR:**
- May be data type mismatch (text vs number)
- May be missing relationship (table not connected)
- Check: all tables in data model?

⚠️ **If Startup program response delays:**
- Plan **Scenario B (€32/month P1)** as fallback immediately
- Trial ends 2026-05-21, cannot wait for approval
- Apply to capacity immediately on Day 14

---

## 🎯 SUCCESS CRITERIA (Trial End)

**Trial is successful if:**

✅ All 9 pages complete in Power BI
✅ Page 8-9 have 5+ visuals each, validated data
✅ No `--` or ERROR values in KPI cards
✅ All DAX measures documented
✅ All code (notebooks, scripts) in GitHub with comments
✅ Startup program application submitted (pending or approved)
✅ Fallback capacity budget (€32/month) identified & approved
✅ Team understands post-trial capacity strategy

**If any of above = ❌, trial is NOT successful → cannot proceed to web app.**

---

## 📞 SUPPORT CONTACTS

If stuck:

| Issue | Contact | Response Time |
|---|---|---|
| Fabric pipeline error | Microsoft Fabric support (Azure portal) | 24-48h |
| Power BI DAX issue | Power BI community forum or Microsoft support | 24-72h |
| Startup program status | startups@microsoft.com | 5-10 business days |
| Emergency capacity request | Azure support (escalate as "startup with time-critical need") | 1-2h |

