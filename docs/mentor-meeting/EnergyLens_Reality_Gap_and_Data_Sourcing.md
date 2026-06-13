---
title: "EnergyLens — Reality Gap & Data-Sourcing Plan"
subtitle: "Carbon Accounting, EPC, CRREM, EU Regulation + the full data-honesty layer"
author: "Ali Mert Özdemir"
date: "2026-06-08"
---

# Purpose / Amaç

Companion to **`EnergyLens_Study_Reference_EN.pdf`** — specifically *Part II (Carbon
Accounting, EPC, CRREM & EU Regulation)* and *Part V (the honesty layer)*.

For **every** number in EnergyLens that is currently an *assumption / indicative / proxy*
value, this document gives three things:

1. **Now** — what the platform does today (the honest current state).
2. **Should be** — what the *real* standard or methodology requires, exactly.
3. **What to access** — the *real institution, dataset, API or agreement* we must connect
   to make the number production-grade — with the access route, the licence, and the cost.

All regulatory dates, factors and data-source facts below were **verified against primary
sources in June 2026** (sources listed in §C). Where a value is a range or still a draft, it
says so — nothing is invented.

> **tr — Bu doküman ne işe yarar:** Worksheet'te "şu an indikatif / varsayım / proxy" diye
> işaretlediğim her sayı için → (1) şu an ne yapıyoruz, (2) gerçekte tam olarak nasıl olmalı,
> (3) bunu gerçeğe çevirmek için **hangi kurumdan / API'den veri çekeriz veya hangi anlaşmayı
> yaparız** (erişim yolu + lisans + maliyet). Hocaya da, freelance müşterisine de aynı tabloyu
> gösterebilirsin. Önce kısa tablo (§A), sonra her satırın detayı (§B), sonra kaynak rehberi (§C),
> en sonda "ne söylemeli" (§D).

---

# §A — At-a-glance comparison table

> The short table. Read top-to-bottom: the first 6 rows are **Part II** (carbon / EPC / CRREM /
> regulation); rows 7–11 are the rest of the **honesty layer** (data realism across the platform).
> "Effort" = how hard it is for us to close the gap, not how important it is.

| # | Item | Now (what we do) | Should be (the real standard) | What we must access — who · route · cost | Effort |
|---|------|------------------|-------------------------------|-------------------------------------------|--------|
| 1 | **Scope 3 emissions** | `(Scope1+Scope2) × 8%` screening, flagged `scope3_disclosure_grade = False` | GHG Protocol **Scope 3 Standard** — calculate the *material* categories from activity data × emission factors (buildings: **Cat 13** downstream leased / tenant energy, **Cat 1** embodied carbon, **Cat 2** capital goods) | Tenant/sub-meter energy data (**building owner**, contractual) · emission-factor DB: **DESNZ/DEFRA** (free), **ADEME Base Empreinte** (free), **ecoinvent** (paid), **EXIOBASE** (free spend-based) · or **Climatiq** API (freemium) | High |
| 2 | **Market-based Scope 2** | Supplier-factor column exists but no contract data → equals location-based | GHG Protocol **Scope 2 Guidance** dual reporting: market-based from **supplier-specific factor / Guarantees of Origin**; **residual mix** for untracked supply | Each building's **electricity contract + GoO certificates** (utility/supplier) · **AIB European Residual Mix** for the residual factor (free, annual) | Medium |
| 3 | **Scope 1 (gas + refrigerant)** | Gas proxied from heating-share if no meter; **refrigerant leakage excluded** | Metered fuel × fuel factor; refrigerant **fugitive = annual top-up (kg) × GWP** (IPCC AR5/AR6). EU **F-Gas Reg 2024/573** governs logs/leak checks | Gas meter / utility bills (**owner**) · **refrigerant service logs / F-Gas logbook** (HVAC contractor) · GWP values **IPCC AR6** (free) · fuel factors **DEFRA/DESNZ** (free) | Medium |
| 4 | **Grid emission factors** (non-DE/TR) | DE (**UBA 363 g/kWh, 2024**) + TR (**0.442**) real & year-indexed; other countries IEA placeholder | Official annual **location-based** factor per country | **EEA** "GHG emission intensity of electricity" (free, per-country, EU) · **IEA Emission Factors** (paid, global) · **ElectricityMaps** (live/operational, freemium+commercial) | Low |
| 5 | **EPC ratings** | Synthetic `energy_certificate` for B001–B010 | Actual EPC from the building's **Energieausweis** / national register | **UK EPC Open Data** (free API/bulk) · **DE**: no central register yet → due **~May 2026** (EPBD Art 22); until then per-building from owner/issuer · **EU Building Stock Observatory** (aggregate only) | Medium |
| 6 | **CRREM pathways** | Indicative 1.5 °C anchors in one swappable module | Official **CRREM v2 pathways + emission factors**, compared on **Scope 1+2** basis | **CRREM Library** — open-access from ~**1 Jul 2026** (free pathways + factors + Misalignment-Year guidance) · embedding into a **commercial product sold to clients** = **CRREM License Partner** agreement | Low (data) / Med (commercial embed) |
| 7 | **Regulatory facts/dates** | "Current as of mid-2026"; Battery Reg mis-numbered **2023/1670** in app | Verified, sourced, and the app number corrected to **2023/1542** | **EUR-Lex** (free) · **EFRAG** (ESRS) · national transposition trackers — see §B7 for the verified list | Low |
| 8 | **Underlying building data** | Consumption/solar/battery **synthetic** for 10 buildings; weather/price/grid-CO₂ **real** | Metered data from a **real pilot building** | A pilot (e.g. **BSBI campus**) · smart-meter feed (DE **Smart Meter Gateway** / utility portal) · **BMS export** (BACnet/Modbus) · utility-bill API | High |
| 9 | **HVAC split** | Heating/cooling/ventilation **modeled** (type coeff × HDD/CDD) | **Sub-metered** HVAC circuits | Building **sub-meters / BMS points** (facility) — a Tier-3 upsell | Medium |
| 10 | **Forecast accuracy** | MAPE is **in-sample** | **Rolling-origin cross-validation** (Prophet `cross_validation`) | Nothing external — **code/method fix** (more history helps) | Low |
| 11 | **Battery ROI savings** | **Upper-bound** (all discharge valued at peak tariff) | Price each discharged kWh by **the hour it displaces** (hourly dispatch vs hourly price) | **ENTSO-E** hourly day-ahead prices (free — we already pull this) — code/method fix | Low–Med |

> **tr — tabloyu nasıl kullan:** Hocaya tek sayfa olarak göster. Sol taraf "dürüst şu an", orta
> "gerçek standart", sağ "neye erişmemiz lazım". En kritik 3 satır: **1 (Scope 3)**, **2 (market-based
> S2)**, **6 (CRREM)** — bunlar enerji/ESG akademisyeninin ilk soracağı yerler. Satır 7 (regülasyon)
> bir **düzeltme** içeriyor: app'te **2023/1670 yazan yerleri 2023/1542** yap.

---

# §B — Detailed reference (per item)

Each item: **the gap in one line**, **what "real" means**, **the exact source + how to connect**,
and **the honest sentence to say**.

## B1 — Scope 3 emissions

**The gap.** We report Scope 3 as a flat **8 % of (Scope 1 + Scope 2)** and explicitly flag it
`scope3_disclosure_grade = False`. This is a *screening placeholder*, not a disclosure number.

**What "real" means.** The **GHG Protocol Corporate Value Chain (Scope 3) Standard** defines
15 categories. You do **not** report all 15 — you do a *materiality screen*, then calculate the
material ones from **activity data × emission factor**. For a building portfolio the material
categories are almost always:

- **Category 13 — Downstream leased assets** (the energy your *tenants* use in space you own
  and lease out). For most landlords this is the **single biggest** Scope 3 bucket.
- **Category 1 — Purchased goods & services** and **Category 2 — Capital goods** (the *embodied*
  carbon of construction materials and major refits).
- Plus Cat 5 (waste), Cat 6 (business travel), Cat 7 (commuting) where data exists.

**Exact sources + how to connect:**

- **Activity data** (the hard part): tenant electricity/heat consumption — obtained via
  **green-lease clauses**, tenant sub-metering, or the utility. This is a *data-access agreement*,
  not an API.
- **Emission factors** (the easy part):
  - **UK DESNZ / DEFRA "Greenhouse gas reporting: conversion factors"** — free, updated annually,
    the de-facto global default for activity-based factors.
  - **ADEME Base Empreinte / Base Carbone** (France) — free, official, large database.
  - **ecoinvent** — the gold-standard LCA database for embodied carbon (Cat 1/2) — **paid licence**
    (~€for a commercial seat).
  - **EXIOBASE** — free environmentally-extended input-output DB for **spend-based** estimates.
  - **Climatiq** — a commercial **API** that aggregates DEFRA/IEA/etc. — freemium, good for a
    productized integration.

**Say this:** *"Scope 3 is currently an 8 % screening placeholder, clearly flagged as not
disclosure-grade. To make it real I model the material categories — Category 13 tenant energy
and Category 1 embodied carbon — from activity data times DEFRA/ADEME factors. The blocker is
not the method, it's getting tenant data via green-lease clauses."*

> **tr:** Scope 3 = şu an %8 screening (etiketli, disclosure değil). Gerçeği: GHG Protocol Scope 3
> Standardı, sadece *material* kategoriler (binalarda **Kat 13 kiracı enerjisi** + **Kat 1 gömülü
> karbon**). Faktör kolay (DEFRA/ADEME ücretsiz, ecoinvent paralı); zor olan kiracı verisi (yeşil
> kira sözleşmesi).

## B2 — Market-based Scope 2

**The gap.** The engine has a `supplier_ef` column, but with no real contract data it returns the
**location-based** number twice.

**What "real" means.** The **GHG Protocol Scope 2 Guidance** requires **dual reporting**:
*location-based* (grid average) **and** *market-based* (your actual procurement). Market-based uses,
in order of preference: a **supplier-specific** emission factor, an **Energy Attribute Certificate**
(in Europe a **Guarantee of Origin, GoO**), or — for the electricity you *didn't* cover with a
certificate — the **residual mix**.

**Exact sources + how to connect:**

- **Supplier factor / GoOs** — from each building's **electricity supply contract** and the
  **Guarantee-of-Origin certificates** the utility issues. This is a per-building document, not an API.
- **AIB European Residual Mix** (Association of Issuing Bodies) — the **authoritative** residual-mix
  factor for European countries, **published free every year** at `aib-net.org/facts/european-residual-mix`,
  and explicitly aligned to the GHG Protocol market-based requirement.

**Say this:** *"The market-based mechanism is built; it just needs each building's supply contract
and its Guarantees of Origin. For the uncovered portion I use the AIB residual mix, which is the
European reference factor for exactly this purpose. Until I have the contracts, market-based equals
location-based — and I say so."*

> **tr:** Market-based S2 mekanizması hazır; gerçek tedarikçi sözleşmesi + **GoO sertifikası** lazım,
> kalanı için **AIB Residual Mix** (ücretsiz, yıllık, Avrupa referansı). Sözleşme gelene kadar
> location-based'e eşit — bunu dürüstçe söyle.

## B3 — Scope 1 (gas + refrigerant)

**The gap.** Where there's no gas meter we *proxy* Scope 1 from a heating-share of electricity, and
we **exclude refrigerant leakage entirely**. Refrigerants (R-410A, R-32) have very high global-warming
potential and are the classic *forgotten* Scope 1 source.

**What "real" means.**

- **Stationary combustion** (gas/oil boilers): metered fuel use × a fuel emission factor.
- **Fugitive / refrigerant emissions:** `annual_refrigerant_topup_kg × GWP`. The top-up mass is the
  refrigerant a contractor adds to recharge a system — i.e. what *leaked*. **GWP** comes from **IPCC**
  (AR5 or AR6 100-year values; e.g. R-410A ≈ 2088). The EU **F-Gas Regulation (EU) 2024/573**
  (in force 11 Mar 2024) mandates leak checks and logbooks — so the data *exists* on site.

**Exact sources + how to connect:**

- **Gas/fuel data:** the building's **gas meter / utility bills** (owner).
- **Refrigerant data:** the **F-Gas logbook / maintenance records** held by the HVAC service
  contractor (mandatory under 2024/573).
- **GWP values:** **IPCC AR6** (free, authoritative).
- **Fuel factors:** **DEFRA/DESNZ** (free).

**Say this:** *"Scope 1 is solid where there's a gas meter. The honest gap is refrigerant fugitive
emissions — I exclude them today rather than fake them. The data exists: the F-Gas logbook the
contractor must keep under EU 2024/573, multiplied by the IPCC GWP. That's a clean next step."*

> **tr:** Scope 1 gaz sayacı varsa sağlam. Açık: **soğutucu gaz kaçağı** (şu an hariç — uydurmuyorum).
> Gerçeği: yıllık dolum (kg) × **IPCC GWP**; veri zaten **F-Gas logbook**'ta (EU 2024/573 zorunlu kılıyor).

## B4 — Grid emission factors (countries beyond DE/TR)

**The gap.** Germany (**UBA**, year-indexed: 2022 = 433, 2023 = 386, **2024 = 363 g CO₂/kWh**) and
Turkey (**0.442**) are real and sourced. Other countries are **IEA placeholders**.

**What "real" means.** A per-country, **annual, location-based** factor, ideally consumption-based
(includes imports/T&D losses) for disclosure.

**Exact sources + how to connect (pick by need):**

- **EEA — "Greenhouse gas emission intensity of electricity generation"** — **free**, official,
  per-country for Europe (the EU average fell ~9 % in 2024 vs 2023). Best free option to replace
  placeholders across the EU.
- **IEA Emission Factors** — global, monthly/quarterly for 50+ countries — **paid subscription**
  (single/multi-user; the licence forbids third-party work — relevant if reselling).
- **ElectricityMaps** — **live / operational** grid intensity via API (freemium for non-commercial,
  commercial licence for production). Use for *operational* insight, **not** for the annual disclosure
  factor.

> **Keep the two apart:** the **disclosure** factor stays annual-official (UBA/EEA/IEA). **Live**
> ElectricityMaps is for operational dashboards only — auditors want the fixed annual number.

> **tr:** DE (UBA 363, 2024) + TR (0.442) gerçek; diğerleri placeholder. Ücretsiz çözüm = **EEA**
> (Avrupa, ülke-bazlı). Global için **IEA** (paralı). Canlı için **ElectricityMaps** — ama disclosure
> faktörü **yıllık-resmî** kalmalı.

## B5 — EPC ratings

**The gap.** The `energy_certificate` (A+→G) for the 10 demo buildings is **synthetic**.

**What "real" means.** The building's **actual EPC** (in Germany the *Energieausweis*, issued under
GEG by a qualified issuer), pulled from a national register where one exists.

**Exact sources + how to connect:**

- **UK — EPC Open Data** (`epc.opendatacommunities.org`) — **free**, official, bulk download + API
  for England & Wales (Scotland separate). The cleanest open EPC dataset in Europe — good for a UK demo.
- **Germany — no central register yet.** Germany is the only large EU state without an EPC database;
  one is **due ~May 2026** under **EPBD Article 22**, which also requires free access to the full EPC
  for owners/tenants/managers. Until it's live, EPC is a **per-building** document from the owner or issuer.
- **EU Building Stock Observatory** — **free** but **aggregate** (national stock statistics), not
  per-building — useful for benchmarks, not for a specific building's rating.
- Going forward, EPBD Art 22 forces every member state's EPC database to be accessible and to feed
  the BSO annually — so per-country EPC access will improve through 2026–2027.

> **tr:** EPC şu an sentetik. Gerçeği: binanın **Energieausweis**'i. **UK** ücretsiz açık veri (demo
> için ideal). **Almanya'da merkezi kayıt yok → ~Mayıs 2026** (EPBD Md. 22) geliyor; o zamana kadar
> bina-bazlı sahibinden. **EU BSO** sadece toplu istatistik.

## B6 — CRREM pathways

**The gap.** Our decarbonization pathways are **indicative 1.5 °C anchors**, isolated in one module
(`PATHWAY_ANCHORS`) so they can be swapped for official values.

**What "real" means.** The **official CRREM v2 pathways + emission factors**, with the comparison done
on the correct scope (**CRREM uses Scope 1+2**, excludes Scope 3 — EnergyLens was already corrected to
compare on this basis).

**Exact sources + how to connect — note the 2026 change:**

- The **free CRREM Excel tool retires 1 July 2026**. It is being replaced by an **open-access "CRREM
  Library"**: the **pathways, emission factors and Misalignment-Year computation guidance are published
  free** for open use. So the *raw data* to compute a correct stranding year becomes **freely available**.
- **But** embedding CRREM pathways/methodology **into a commercial platform sold to clients** still
  requires a **CRREM License Partner** agreement (`crrem.org/license-partners`). Nearly every major real-estate
  ESG platform is a License Partner.
- **Practical plan:** use the open CRREM Library values to replace our indicative anchors now (correct
  data, isolated module); take the **License Partner** step when EnergyLens is sold commercially.

**Say this:** *"My pathways are indicative today. CRREM is opening its dataset as a free library mid-2026,
so I'll swap in the official curves — they drop into one isolated module. For commercial resale I'd take
the CRREM License Partner agreement, which is the standard route every ESG platform uses."*

> **tr:** Pathway'ler indikatif. **CRREM Library (1 Tem 2026, ücretsiz)** ile resmî eğrileri tek modüle
> takarım. **Ticari satışta License Partner** anlaşması (sektör standardı). Karşılaştırma **Scope 1+2**.

## B7 — Regulatory facts (verified June 2026) + the one correction

This is what an academic will check. All verified against primary sources this month:

- **CSRD / Omnibus I** — the simplification directive was **published in the EU Official Journal on
  26 February 2026** (Council adoption 24 Feb 2026; in force ~18 Mar 2026). It **narrows mandatory scope**
  to companies with **> 1,000 employees AND > €450 m net turnover**; the **listed-SME wave is removed**;
  the new scope applies for **financial years from 1 January 2027**. **Consequence for positioning:**
  many mid-caps the old material called "Wave 2, filing FY2025 in 2026" are now **outside mandatory
  scope** — so position EnergyLens as **"ESRS-E1-aligned report-ready support"** and point smaller firms
  to the **voluntary VSME** standard. Do **not** say "everyone must comply."
- **EPBD recast — Directive (EU) 2024/1275** — in force 28 May 2024; **national transposition due
  29 May 2026**. **Non-residential MEPS:** member states set national standards by **1 January 2027**;
  worst-performing **16 % renovated by 2030**, **26 % by 2033**; new buildings **zero-emission from 2030**.
- **EU Battery Regulation — Regulation (EU) 2023/1542** ⚠️ **the app says "2023/1670" in places — fix it.**
  Industrial carbon-footprint declaration applies from **18 Feb 2026**; the **digital Battery Passport
  via QR from 18 Feb 2027** (industrial/EV/LMT > 2 kWh).
- **EU Taxonomy — Activity 7.7 "Acquisition and ownership of buildings."** Original Climate Delegated
  Act: pre-2021 buildings qualify (climate-mitigation substantial contribution) with **EPC A** *or*
  **top-15 % of national stock** by operational primary energy demand; full alignment also needs **DNSH +
  minimum safeguards**. **2026 draft revision** loosens this to **EPC D or top-50 %** — *draft, verify on
  adoption.* Never claim "Taxonomy-aligned" — only an **indicative alignment signal** for the SC criterion.
- **EU F-Gas — Regulation (EU) 2024/573** (in force 11 Mar 2024): leak checks, recovery, logbooks — the
  basis for refrigerant Scope 1 (B3).
- **EnEfG** (Germany): ISO 50001 / audit for ≥ 250 employees; energy-management system if annual final
  energy **> 7.5 GWh**. **GEG §71:** heating installed from 2024 must be **≥ 65 % renewable** (a heat pump
  satisfies it); min U-values (wall ≤ 0.24, roof ≤ 0.20, window ≤ 1.30 W/m²K).

**Access:** all of the above are on **EUR-Lex** (free full text) and **EFRAG** (ESRS standards, free).

> **tr:** En kritik: **CSRD kapsamı daraldı** (>1000 çalışan & >€450M, FY2027) → "herkese zorunlu" DEME,
> "report-ready / VSME" de. **Battery Reg numarasını app'te 2023/1542 yap.** Taxonomy 7.7 2026 taslağı
> gevşetiyor (EPC D / top-50%, taslak). Hepsi **EUR-Lex**'te ücretsiz.

## B8 — Underlying building data (synthetic → real)

**The gap.** Building-level **consumption / solar / battery** data is **synthetic** for B001–B010.
The *external* signals are already real: **Open-Meteo/DWD** weather (211k real hourly rows feeding real
HDD/CDD), **ENTSO-E** prices, **ElectricityMaps** grid CO₂.

**What "real" means.** Metered time-series from at least one **real building**.

**Exact sources + how to connect:**

- A **pilot building** — the cleanest path (e.g. the **BSBI campus**, which doubles as the EXIST/academic story).
- **Smart-meter data:** in Germany via the **Smart Meter Gateway** rollout / the utility's customer portal;
  elsewhere via the DSO/utility API.
- **BMS export:** **BACnet/Modbus** points from the building automation system (the IoT adapters already exist).
- **Utility-bill ingestion:** CSV/API from the energy supplier.

> **Honest framing:** synthetic *operational* data is normal and legitimate for a pre-customer demo — the
> *methods, factors and external signals are real*. State it plainly; an academic respects "synthetic
> operational layer, real methodology and real external data."

> **tr:** Bina tüketim/solar/batarya **sentetik** (henüz müşteri yok); hava/fiyat/grid-CO₂ **gerçek**.
> Gerçeğe geçiş = **pilot bina** (BSBI kampüsü), **akıllı sayaç** / **BMS export** / fatura API'si.

## B9 — HVAC heating/cooling/ventilation split

**The gap.** The split is **modeled** from a building-type coefficient × the weather shape (HDD/CDD),
so an office's HVAC share is essentially pinned by its type. A facilities engineer spots this instantly.

**Should be:** **sub-metered** HVAC circuits (or dedicated BMS energy points).

**Access:** building **sub-meters / BMS metering points** (facility hardware) — frame as a **Tier-3
upsell**: *"modeled split using the HDD/CDD method — sub-metering refines this."*

> **tr:** HVAC split modellenmiş (sub-metered değil). Gerçeği: **alt-sayaç / BMS noktası** (Tier-3 upsell).

## B10 — Forecast accuracy metric

**The gap.** Forecast error (MAPE) is computed **in-sample** — testing the model on its own training
data, which flatters accuracy.

**Should be:** **rolling-origin cross-validation** (Prophet's `cross_validation`) so the reported MAPE is
out-of-sample and honest.

**Access:** none external — a **code/method fix**; more history per building improves it.

> **tr:** MAPE in-sample → **rolling-origin cross-validation**. Dış veri gerekmez, kod düzeltmesi.

## B11 — Battery ROI savings

**The gap.** Savings are an **upper bound** — all discharged energy is valued at the **peak tariff** and
the demand saving is proportional to energy, not to peak-kW. So payback looks optimistic.

**Should be:** price each discharged kWh by **the hour it actually displaces** (hourly dispatch against
the hourly price curve), and value demand-charge savings on the actual peak-kW reduction.

**Access:** **ENTSO-E** hourly day-ahead prices (free — already pulled) — a **method/code fix**, not new data.

> **tr:** Batarya ROI **upper-bound** (hepsi peak tarifeden). Gerçeği: her deşarj kWh'ını **yerine geçtiği
> saatin fiyatıyla** değerle (ENTSO-E saatlik — zaten var). Kod düzeltmesi.

---

# §C — Data-source directory (institution · what · access · cost)

Quick reference — the real institutions, grouped. Use this when the professor asks *"where would the
data come from?"* or when scoping a freelance build.

### Emission factors & carbon accounting

- **UK DESNZ / DEFRA — GHG conversion factors** — activity-based factors (fuel, refrigerant, travel). **Free**, annual. *(global default)*
- **ADEME — Base Empreinte / Base Carbone** (FR) — large official factor DB. **Free**.
- **ecoinvent** — LCA database for **embodied carbon** (Scope 3 Cat 1/2). **Paid licence**.
- **EXIOBASE** — environmentally-extended input-output (spend-based Scope 3). **Free**.
- **Climatiq** — API aggregating DEFRA/IEA/etc. for productized integration. **Freemium**.
- **IPCC (AR5/AR6)** — refrigerant & gas **GWP** values. **Free**.
- **GHG Protocol** — the Corporate, Scope 2 and Scope 3 **standards + calculation guidance**. **Free** (`ghgprotocol.org`).
- **AIB — European Residual Mix** — **market-based Scope 2** residual factor. **Free**, annual (`aib-net.org`).

### Grid emission factors (electricity)

- **UBA (Umweltbundesamt)** — Germany annual grid factor (**363 g/kWh, 2024**). **Free**.
- **EEA** — per-country EU electricity carbon intensity. **Free**.
- **IEA — Emission Factors** — global, 50+ countries, monthly/quarterly. **Paid subscription** (resale-restricted).
- **ElectricityMaps** — **live** grid intensity API. **Freemium** (non-commercial) / **commercial licence** for production.
- **TEİAŞ** (TR) — Turkish grid operator; single canonical factor (~0.442). *(less granular than UBA)*

### Prices & weather

- **ENTSO-E Transparency Platform** — EU day-ahead/hourly electricity prices + generation. **Free** API (email `transparency@entsoe.eu`, subject "Restful API access").
- **DWD Open Data** — official German weather, **free incl. commercial** (legal mandate). *Use this for the commercial build.*
- **Open-Meteo** — free **non-commercial** only (CC BY 4.0, < 10k calls/day); **commercial = paid subscription or self-host** the open-source. *(we use it now; switch to DWD/self-host for sale)*
- **EPİAŞ / EXIST — Şeffaflık Platformu** (TR) — Turkish day-ahead market prices. **Free**.
- **MGM** (TR) — Turkish state meteorology. Weather for Turkish buildings.

### EPC, buildings & decarbonization

- **UK EPC Open Data** (`epc.opendatacommunities.org`) — free EPC dataset (England & Wales) + API.
- **Germany central EPC register** — **due ~May 2026** (EPBD Art 22); until then per-building Energieausweis.
- **EU Building Stock Observatory** — free **aggregate** building-stock + EPC statistics.
- **CRREM Library** — open-access pathways + emission factors from **~1 Jul 2026** (free); **License Partner** for commercial embedding (`crrem.org`).

### Regulation (primary text)

- **EUR-Lex** — full text of every directive/regulation (CSRD/Omnibus, EPBD 2024/1275, Battery 2023/1542, F-Gas 2024/573, Taxonomy). **Free**.
- **EFRAG** — the ESRS standards (incl. ESRS E1) + the voluntary **VSME**. **Free**.

### Real building data (to replace synthetic)

- **Pilot building / BSBI campus** — metered consumption.
- **Smart-meter feeds** — DE Smart Meter Gateway / utility portals; DSO APIs elsewhere.
- **BMS export** — BACnet/Modbus (adapters already built).

---

# §D — What to say (professor + freelance clients)

**The honesty framing (memorize the shape, not the words):**

1. *"The methodology and the external data are real; the operational layer is synthetic until a pilot.
   Here's exactly what I'd connect to make each number production-grade."* — then point at §A.
2. *"Scope 1/2 are auditable today with row-level lineage from a sourced factor to the disclosed kg.
   Scope 3 is a flagged screening estimate, and market-based Scope 2 is built but waiting on supplier
   data — I label both honestly rather than overstate."*
3. *"CRREM is indicative now; the official curves become a free open library in mid-2026 and drop into
   one module, with a License Partner agreement for commercial resale."*
4. *"I keep the disclosure factor annual-official and use live grid data only for operational insight —
   because that's what an auditor expects."*

**Why this wins with an academic:** naming the *exact* gap and the *exact* source to close it is the
strongest possible credibility signal. An academic rewards "I know precisely what isn't real yet and
precisely how to fix it" far more than a polished claim that everything is finished.

**Freelance angle (same content, commercial spin):** this table *is* a productized scope-of-work. Each
"What to access" cell is a paid integration you can quote — "connect your AIB residual mix + GoOs for
audit-ready market-based Scope 2," "wire your DEFRA factors for Scope 3 Cat 13," "swap in licensed CRREM
curves." You sell *closing the gap*, building by building.

> **tr — özet:** Hocaya güç veren şey "her şey bitti" demek değil, **"neyin gerçek olmadığını ve onu
> kapatmak için tam olarak hangi kaynağa bağlanacağımı biliyorum"** demek. Aynı tablo freelance'te
> **satış kapsamı**: her "neye erişmemiz lazım" hücresi ücretlendirebileceğin bir entegrasyon.

---

*Verified June 2026 against EUR-Lex, EFRAG, UBA, EEA, IEA, AIB, CRREM Foundation, DWD, Open-Meteo,
DESNZ/DEFRA, ADEME, ENTSO-E and the UK EPC register. Regulatory dates — re-check on EUR-Lex right
before the meeting; the EU Taxonomy 7.7 loosening (EPC D / top-50 %) is a 2026 draft, not yet adopted.*
