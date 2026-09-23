-- ============================================================================
-- 02_silver.sql  ·  CLEAN, CONFORMED, TYPED
-- ----------------------------------------------------------------------------
-- Every transformation below fixes ONE named real-world defect and is labelled
-- with its number so you can explain it out loud. Nothing is dropped silently:
-- rejected rows go to *_rejects with a reason.
--   Fabric equivalent: notebook 02_silver_transform.
-- ============================================================================


-- ****************************************************************************
-- THE ONE SQL CONCEPT THAT CATCHES EVERYONE: "AT TIME ZONE" GOES BOTH WAYS
-- ----------------------------------------------------------------------------
--   TIMESTAMP   AT TIME ZONE 'Europe/Berlin'  ->  TIMESTAMPTZ
--        "this naive wall clock IS Berlin local; give me the absolute instant"
--        Use this on METER data, which arrives as naive local time.
--
--   TIMESTAMPTZ AT TIME ZONE 'Europe/Berlin'  ->  TIMESTAMP
--        "I have an absolute instant; show me the Berlin wall clock"
--        Use this for DISPLAY and for grouping by local calendar day.
--
-- Same keyword, opposite directions, decided purely by the input type. Getting
-- it backwards silently shifts every value by 1-2 hours and your daily totals
-- still look plausible -- which is why it survives to production.
-- Postgres, Snowflake and BigQuery all behave this way. Fabric/Spark uses
-- to_utc_timestamp() / from_utc_timestamp() for the same two directions.
-- ****************************************************************************

-- ---------------------------------------------------------------- PARAMS
CREATE OR REPLACE MACRO p(k) AS (SELECT value FROM silver_params WHERE param = k);

-- ============================================================ 1. CUSTOMERS
-- Fixes: DEFECT 9 (MaLo-ID leading zero destroyed by Excel)
--        DEFECT 10 (dirty categoricals: case + trailing whitespace)
CREATE OR REPLACE TABLE silver_customers AS
SELECT
    -- DEFECT 9: the MaLo-ID is specified as ELEVEN digits. Pad it, do not trust
    -- the source. A naive join on the raw string loses 4 of 28 customers here.
    lpad(trim(malo_id), 11, '0')                        AS malo_id,
    trim(malo_id)                                       AS malo_id_as_received,
    length(trim(malo_id)) <> 11                         AS malo_id_was_malformed,
    customer_ref,
    -- DEFECT 10: normalise, then title-case, so "BERLIN ", "berlin", "Berlin"
    -- collapse to one value instead of three rows in every GROUP BY.
    upper(substr(trim(city),1,1)) || lower(substr(trim(city),2)) AS city,
    trim(dso_name)                                      AS dso_name,
    segment,
    TRY_CAST(pv_kwp              AS DOUBLE)             AS pv_kwp,
    TRY_CAST(battery_kwh         AS DOUBLE)             AS battery_kwh,
    TRY_CAST(has_heat_pump       AS INTEGER) = 1        AS has_heat_pump,
    TRY_CAST(has_ev              AS INTEGER) = 1        AS has_ev,
    TRY_CAST(annual_kwh_expected AS INTEGER)            AS annual_kwh_expected,
    tariff_type,
    TRY_CAST(contract_start AS DATE)                    AS contract_start,
    reporting_unit,
    -- controllable capacity = what the VPP can actually steer (assumption,
    -- stated explicitly rather than buried): battery power + HP + EV charger
    COALESCE(TRY_CAST(battery_kwh AS DOUBLE),0) * 0.5
      + CASE WHEN TRY_CAST(has_heat_pump AS INTEGER)=1 THEN 3.0 ELSE 0 END
      + CASE WHEN TRY_CAST(has_ev        AS INTEGER)=1 THEN 11.0 ELSE 0 END
                                                        AS controllable_kw
FROM bronze_customers;

-- ============================================================== 2. PRICES
-- Fixes: DEFECT 1a (duplicate publications), DEFECT 6 (DST).
-- KEY LESSON: the file carries ts_utc. Use it. Never reconstruct an absolute
-- instant from a naive local string -- 2025-03-30 02:15 local does not exist
-- and 2025-10-26 02:15 local happens twice.
CREATE OR REPLACE TABLE silver_prices AS
WITH typed AS (
    SELECT
        -- the string ends in 'Z', i.e. it IS UTC. strptime returns a NAIVE
        -- timestamp, so we must tell SQL which zone it belongs to: 'UTC'.
        strptime(ts_utc, '%Y-%m-%dT%H:%M:%SZ') AT TIME ZONE 'UTC' AS ts_utc,
        ts_local                                AS ts_local_raw,
        bidding_zone,
        TRY_CAST(price_eur_mwh AS DOUBLE)       AS price_eur_mwh
    FROM bronze_prices
    WHERE TRY_CAST(price_eur_mwh AS DOUBLE) IS NOT NULL
),
-- TECHNIQUE: ROW_NUMBER() + QUALIFY is the canonical dedup. Partition by the
-- business key, order by whatever makes one row authoritative, keep rn = 1.
deduped AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY ts_utc, bidding_zone
                                 ORDER BY price_eur_mwh) AS rn
    FROM typed
    QUALIFY rn = 1
)
SELECT
    ts_utc,
    -- correct, unambiguous local time derived FROM utc
    ts_utc AT TIME ZONE 'Europe/Berlin'                  AS ts_local,
    bidding_zone,
    price_eur_mwh,
    price_eur_mwh / 10.0                                 AS spot_ct_kwh,
    price_eur_mwh < 0                                    AS is_negative_price,
    CAST(ts_utc AT TIME ZONE 'Europe/Berlin' AS DATE)    AS local_date,
    EXTRACT(hour FROM ts_utc AT TIME ZONE 'Europe/Berlin') AS local_hour
FROM deduped;

-- PROOF that DST is handled, done PROPERLY: never hardcode "92" or "100".
-- Build the complete expected grid from UTC, let the calendar tell you how many
-- quarter-hours each LOCAL day contains, then compare reality against it.
-- A 23-hour day and a day with 4 missing MTUs both have 92 rows -- only the
-- expected-vs-actual comparison can tell them apart.
CREATE OR REPLACE TABLE silver_price_calendar AS
SELECT ts_utc,
       CAST(ts_utc AT TIME ZONE 'Europe/Berlin' AS DATE) AS local_date
FROM (SELECT UNNEST(generate_series(
        TIMESTAMP '2024-12-31 23:00:00',
        TIMESTAMP '2025-12-31 22:45:00',
        INTERVAL 15 MINUTE)) AT TIME ZONE 'UTC' AS ts_utc);

CREATE OR REPLACE TABLE qa_price_days AS
SELECT
    cal.local_date,
    COUNT(*)                                       AS expected_mtu,
    COUNT(pr.ts_utc)                               AS actual_mtu,
    COUNT(*) - COUNT(pr.ts_utc)                    AS missing_mtu,
    CASE COUNT(*) WHEN 92 THEN '23h  DST spring forward'
                  WHEN 100 THEN '25h  DST fall back'
                  WHEN 96 THEN '24h  normal'
                  ELSE '?? unexpected' END          AS day_length,
    CASE WHEN COUNT(*) = COUNT(pr.ts_utc) THEN 'complete'
         ELSE 'INCOMPLETE - publication gap' END    AS completeness
FROM silver_price_calendar cal
LEFT JOIN silver_prices pr USING (ts_utc)
GROUP BY 1 ORDER BY 1;

-- The two DST days, isolated by the calendar itself rather than by hardcoding:
CREATE OR REPLACE TABLE qa_dst_check AS
SELECT * FROM qa_price_days WHERE expected_mtu <> 96;

-- ======================================================= 3. CALENDAR SPINE
-- TECHNIQUE: you cannot detect a MISSING row by querying the rows you have.
-- Generate the complete expected grid, then LEFT JOIN reality onto it.
CREATE OR REPLACE TABLE silver_calendar AS
SELECT ts_utc,
       ts_utc AT TIME ZONE 'Europe/Berlin'               AS ts_local,
       CAST(ts_utc AT TIME ZONE 'Europe/Berlin' AS DATE) AS local_date
FROM (SELECT UNNEST(generate_series(
        TIMESTAMP '2025-01-31 23:00:00',
        TIMESTAMP '2025-04-30 22:45:00',
        INTERVAL 15 MINUTE)) AT TIME ZONE 'UTC' AS ts_utc);

-- ============================================================== 4. METER
-- Fixes: DEFECT 1b duplicates · 3 NULLs · 4 decimal comma · 5 mixed timestamp
--        formats · 6 DST · 7 kW-vs-kWh · 8 negative sign · 11 orphan MaLos
CREATE OR REPLACE TABLE stg_meter AS
SELECT
    lpad(trim(malo_id), 11, '0')                        AS malo_id,
    interval_start_local                                AS ts_raw,
    -- DEFECT 5: two timestamp formats in one column. COALESCE the parsers -
    -- try the strict one first, fall back to the German one.
    COALESCE(
        TRY_CAST(interval_start_local AS TIMESTAMP),
        TRY_STRPTIME(interval_start_local, '%d.%m.%Y %H:%M')
    )                                                   AS ts_local_naive,
    -- DEFECT 4: German decimal comma makes the column TEXT. Normalise, then cast.
    TRY_CAST(replace(trim(value), ',', '.') AS DOUBLE)  AS value_num,
    trim(value)                                         AS value_raw,
    unit,
    -- DEFECT 3: '' and NULL both mean "no value". Classify, do not guess.
    CASE WHEN NULLIF(trim(status),'') IS NULL THEN 'UNKNOWN' ELSE trim(status) END AS status,
    source
FROM bronze_meter;

-- Reject table FIRST, so nothing disappears without a documented reason.
CREATE OR REPLACE TABLE silver_meter_rejects AS
SELECT s.*, 
       CASE
         WHEN s.ts_local_naive IS NULL             THEN 'R1_unparseable_timestamp'
         WHEN s.value_num IS NULL                  THEN 'R2_null_or_unparseable_value'
         WHEN c.malo_id IS NULL                    THEN 'R3_orphan_malo_not_in_master'
       END AS reject_reason
FROM stg_meter s
LEFT JOIN silver_customers c USING (malo_id)
WHERE s.ts_local_naive IS NULL OR s.value_num IS NULL OR c.malo_id IS NULL;

CREATE OR REPLACE TABLE silver_meter AS
WITH valid AS (
    SELECT s.*, c.reporting_unit, c.segment, c.tariff_type, c.dso_name, c.city,
           c.controllable_kw, c.pv_kwp, c.battery_kwh
    FROM stg_meter s
    JOIN silver_customers c USING (malo_id)          -- inner join drops orphans (logged above)
    WHERE s.ts_local_naive IS NOT NULL AND s.value_num IS NOT NULL
),
-- DEFECT 6: convert naive local -> absolute UTC exactly once, here.
-- Meter window is Feb-Apr so the only DST event is the spring gap, which the
-- source correctly never emits. We still assert it below in qa_meter_gaps.
tz AS (
    SELECT *,
           ts_local_naive AT TIME ZONE 'Europe/Berlin' AS ts_utc
    FROM valid
),
-- DEFECT 1b: dedup re-sent MSCONS rows on the business key (malo, interval).
dedup AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY malo_id, ts_utc
                                 ORDER BY CASE status WHEN 'V' THEN 1
                                                      WHEN 'E' THEN 2 ELSE 3 END,
                                          value_num) AS rn
    FROM tz
    QUALIFY rn = 1
)
SELECT
    malo_id, ts_utc,
    ts_utc AT TIME ZONE 'Europe/Berlin'                 AS ts_local,
    CAST(ts_utc AT TIME ZONE 'Europe/Berlin' AS DATE)   AS local_date,
    -- DEFECT 7: three customers report AVERAGE POWER (kW) over the interval,
    -- not ENERGY (kWh). Energy = average power x 0.25 h. This is the single
    -- most common analytical error in the industry and it inflates those
    -- customers' consumption by exactly 4x if you miss it.
    CASE WHEN reporting_unit = 'KW' THEN value_num * 0.25 ELSE value_num END
                                                        AS kwh_reported,
    -- DEFECT 8: negative values are PV export that leaked into the import
    -- register. Do NOT clamp them to zero silently - split the registers, so
    -- the energy still balances and the anomaly stays visible.
    GREATEST(CASE WHEN reporting_unit='KW' THEN value_num*0.25 ELSE value_num END, 0) AS kwh_import,
    ABS(LEAST(CASE WHEN reporting_unit='KW' THEN value_num*0.25 ELSE value_num END, 0)) AS kwh_export_leaked,
    status,
    status = 'E'                                        AS is_substitute_value,  -- Ersatzwert
    reporting_unit, segment, tariff_type, dso_name, city,
    controllable_kw, pv_kwp, battery_kwh
FROM dedup;

-- Gap report: expected grid vs delivered rows, per customer.
CREATE OR REPLACE TABLE qa_meter_gaps AS
SELECT c.malo_id, cust.segment, cust.dso_name,
       COUNT(*)                                          AS expected_intervals,
       COUNT(m.malo_id)                                  AS delivered_intervals,
       COUNT(*) - COUNT(m.malo_id)                       AS missing_intervals,
       ROUND(100.0 * COUNT(m.malo_id) / COUNT(*), 2)     AS completeness_pct,
       ROUND(100.0 * COUNT(*) FILTER (WHERE m.is_substitute_value)
             / NULLIF(COUNT(m.malo_id),0), 2)            AS substitute_value_pct
FROM (SELECT malo_id FROM silver_customers) c
CROSS JOIN silver_calendar cal
LEFT JOIN silver_meter m ON m.malo_id = c.malo_id AND m.ts_utc = cal.ts_utc
JOIN silver_customers cust ON cust.malo_id = c.malo_id
GROUP BY 1,2,3
ORDER BY completeness_pct;

-- ========================================================== 5. MaKo EVENTS
CREATE OR REPLACE TABLE silver_mako_events AS
SELECT
    lpad(trim(malo_id), 11, '0')                 AS malo_id,
    trim(dso_name)                               AS dso_name,
    stage,
    TRY_CAST(event_ts AS TIMESTAMP)              AS event_ts,
    NULLIF(trim(message_type),'')                AS message_type,
    NULLIF(trim(error_code),'')                  AS error_code,
    NULLIF(trim(note),'')                        AS note,
    -- TECHNIQUE: LAG gives you the previous event per customer, so you can
    -- measure the LATENCY of each hop instead of only the end-to-end total.
    LAG(stage)    OVER (PARTITION BY malo_id ORDER BY TRY_CAST(event_ts AS TIMESTAMP)) AS prev_stage,
    DATEDIFF('day',
        LAG(TRY_CAST(event_ts AS TIMESTAMP)) OVER (PARTITION BY malo_id ORDER BY TRY_CAST(event_ts AS TIMESTAMP)),
        TRY_CAST(event_ts AS TIMESTAMP))         AS days_since_prev_event
FROM bronze_mako;

-- ASSERTION: no meter row may fall inside the DST spring-forward gap
-- (2025-03-30 02:00-03:00 local simply does not exist). If this table is not
-- empty, the source system is emitting impossible timestamps.
CREATE OR REPLACE TABLE qa_meter_dst_gap_assert AS
SELECT malo_id, ts_raw, ts_local_naive
FROM stg_meter
WHERE ts_local_naive >= TIMESTAMP '2025-03-30 02:00:00'
  AND ts_local_naive <  TIMESTAMP '2025-03-30 03:00:00';
