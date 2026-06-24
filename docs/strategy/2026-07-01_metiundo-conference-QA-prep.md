# EnergyLens — Conversation & Q&A Prep Pack
**Event:** metiundo "Energiewende konkret!", 1 July 2026, Berlin
**Purpose:** Answer questions confidently, speak the right English/German terms, and frame current limits honestly as deliberate, capacity-aware choices with a clear roadmap. You are an **energy engineer + founder** — this pack backs that identity.

> 🇹🇷 **Nasıl kullan:** Bölüm 2 (yöntem) + Bölüm 6 (sözlük) = "ne yaptığını bilen" havası. Bölüm 4 = her şirketle ne konuşacağın. Bölüm 5 = zor sorulara dürüst cevap. Ezber değil, mantığı kafanda otursun yeter.

---

## 1. EnergyLens in one minute

EnergyLens is a **data-light, hardware-free, estimation-first energy + EU-compliance intelligence layer for building portfolios** (commercial and residential, Germany first). It starts from data a building already has — bills, existing meter readings, the energy certificate (EPC), age/type/size — and produces energy intensity, carbon, compliance risk (EPBD/CRREM) and ranked retrofit measures with subsidy-adjusted ROI. **Every number is a range with its assumptions**, and is replaced by measured values as real data arrives.

**Five core focuses:** (1) hardware-free estimation engine, (2) energy efficiency & cost, (3) carbon & ESG (ESRS-E1-aligned), (4) compliance & regulatory risk — the wedge, (5) portfolio CapEx prioritization.

> 🇹🇷 **Not:** Bu odadaki lider kartın = uyumluluk + portföy-kararı + donanımsız tahmin. Flexibility/trading iddiası YOK; o oyuncuları tamamlıyorsun.

---

## 2. How it actually works — methods, assumptions, standards
*(This is the backbone. If someone asks "how do you calculate X without hardware?", answer from here.)*

### 2.1 The estimation engine
- **Inputs:** utility bills / annual consumption, building type, floor area (Wohn-/Nutzfläche), construction year, EPC, plus public building footprints (OSM/official) and public EPC data.
- **Method:** building **archetype profiles** (typical energy use by type + vintage) → a **provisional baseline EUI range** → corrected for **weather (degree-days)** and the actual bills you provide.
- **Output:** a defensible first picture as a **range + stated assumptions**, flagged "Estimated"; replaced by measured values as real data comes in.
- **Say it:** *"It's a physics- and archetype-based estimate, not a black box. You get a range with the assumptions written next to it, and it tightens as real data arrives."*

> 🇹🇷 **Not:** "Estimation-first" = sensör beklemeden, eldeki veriyle ilk tabloyu kurmak; her değer aralık + varsayım, ölçüm gelince yerini ölçülen değer alır.

### 2.2 Energy intensity & benchmarking
- **EUI = Energy Use Intensity = kWh/m²/year** (the core efficiency metric). Compared against archetype/peer bands and EPC classes.
- **Weather normalization:** consumption is normalized with **HDD (Heating Degree Days)** so a cold year doesn't look like waste. Formula pattern: `normalized = raw × HDD_normal / HDD_period`.
- **Standard:** EPC bands (Energieausweis A–H); archetype EUI bands (e.g. office ≈ 120–220 kWh/m²/yr — *indicative*).

> 🇹🇷 **Not:** EUI = binanın "yakıt tüketimi/100km"si. HDD ile düzeltme = soğuk yılı israp gibi göstermemek için.

### 2.3 HVAC & building envelope *(Page 7 / `gold_hvac_analytics`)*
- **Heating/cooling/ventilation split:** estimated with an **HDD/CDD proportional model** (ventilation ≈ fixed 15%) when no sub-meters exist.
- **Heat loss:** simplified **EN ISO 13370** transmission method: `U_composite × envelope_area × HDD × 24 / 1000`.
- **Insulation score (0–100):** composite U-value vs **GEG 2023** reference U-values (100 ≈ passive-house standard).
- **Heat pump:** **COP** (Coefficient of Performance, instantaneous) and **SCOP** (Seasonal COP, Oct–Apr rolling); only meaningful where a heat pump exists.
- **Envelope area:** currently estimated (square-plan, ~3-storey assumption) → tightens with real BIM/DWG or a quick survey.
- **Say it:** *"HVAC is an assessment layer — I estimate the heating/cooling split, transmission heat loss via ISO 13370, and an insulation score against GEG reference U-values, then flag renovation priority. I don't control systems; that's the operational layer."*

> 🇹🇷 **Not:** Bizim HVAC = değerlendirme (hangi bina kötü, önce hangisi). Green Fusion = kontrol (sistemi fiilen çalıştırıyor). Bunu karıştırma.

### 2.4 Carbon & ESG
- **Scopes:** Scope 1 (on-site combustion, refrigerants), Scope 2 (purchased electricity/heat), Scope 3 (upstream).
- **Scope 2 two ways:** **location-based** (grid average) vs **market-based** (contracts/residual mix). DE grid ≈ **363 g CO₂/kWh (2024, UBA)**; DE **residual mix** is much higher (~0.7 kg/kWh) — matters for market-based.
- **Reporting:** **ESRS-E1-aligned** / voluntary **VSME**. *(Always say "ESRS-E1-aligned," never "CSRD-compliant.")*

> 🇹🇷 **Not:** Location vs market-based ayrımı sorulabilir — location = şebeke ortalaması, market-based = senin sözleşmen/residual mix. İkisini bil.

### 2.5 Compliance & regulatory risk *(the wedge)*
- **EPBD** + national **GEG (Gebäudeenergiegesetz)**: minimum energy performance standards (MEPS) tightening around **2030 / 2033**.
- **CRREM:** decarbonization pathways → the year a building **"strands"** (falls below the carbon target). *(CRREM pathways/factors are open-access; embedding in a commercial product needs a CRREM License Partner.)*
- **EU Taxonomy:** building eligibility by EPC/efficiency (thresholds under revision).
- **Carbon pricing on buildings:** **nEHS** today (~55–65 €/t), **EU ETS2** starting **~2028** → the rising "cost of doing nothing."
- **GEG §71a:** building-automation requirement (this is what Green Fusion is TÜV-certified for — you screen for it, you don't certify).
- **Residential:** **HeizkostenV / HKVO** monthly consumption info (**UVI**) mandatory from **1 Jan 2027** (with a ~3% billing-cut penalty for non-compliance); cost allocation typically **70/30** (consumption/area).

> 🇹🇷 **Not:** "Cost of doing nothing" = uyum yapmamanın yükselen maliyeti (ceza + karbon fiyatı + değer kaybı). Senin satış mantığının kalbi bu.

### 2.6 Retrofit ROI & subsidies
- **Ranked measures** with payback + a **MACC** (Marginal Abatement Cost Curve) view: cheapest CO₂ savings first.
- **Subsidy-adjusted ROI:** **BAFA** heat-pump funding (base ~30%, up to ~70% with bonuses) and **KfW/BEG** programs reduce net CapEx.
- **Retrofit physics:** savings from a measure ≈ `ΔU × area × degree-days ÷ system efficiency` (Energieberater-style).

> 🇹🇷 **Not:** "Subvansiyon-ayarlı ROI" = sübvansiyonu düşünce gerçek geri-dönüş süresi. BAFA/KfW'yi anmak seni ciddi gösterir.

### 2.7 Forecasting — why rule/physics-based (for now)
- Current forecast/estimate is **deterministic (archetype + degree-days + bills)**, not trained ML — **on purpose**: it's **transparent, auditable and explainable**, which is exactly what compliance and investment decisions need. A black-box ML number is a liability in a compliance report.
- **ML comes later, data-first:** once real multi-building data exists (from pilots), ML is added **only where it beats the rule-based baseline** (e.g. consumption disaggregation, anomaly detection). Short-term load/flex forecasting (the ML-heavy kind) is The Mobility House's core, not ours.
- **Say it:** *"It's deterministic and transparent by design — for compliance you need numbers you can defend. I'll add ML later on real data, only where it clearly beats the physics baseline."*

> 🇹🇷 **Not:** "ML kullanıyor musun?" gelirse savunmaya geçme — şeffaflık bilinçli bir seçim, de. Asıl darboğaz model değil, gerçek veri.

---

## 3. Current state vs. roadmap *(honest, capacity-aware framing)*
*Use this whenever something isn't fully automated — turn a limit into a deliberate choice + a plan.*

| Topic | Today (bootstrapped, ~€0) | With a pilot / funding / capacity |
|---|---|---|
| **Compute** | Static snapshots; gold tables mirrored to Postgres; Microsoft Fabric used for batch only | Always-on Fabric capacity (F-SKU); live refresh |
| **Real-time / IoT** | Off (€0); architecture ready ("decoupled" — Azure Event Hubs + hot store) | Switch on **per paying IoT customer** (scale cost, not upfront burn) |
| **Climate/HDD** | Placeholder factor (1.0) on some paths | Wire real HDD per postal code (DWD Open Data / Open-Meteo) |
| **Data connectors** | Generic bill/CSV/Excel ingest; vendor exports mapped manually | Productized connectors (Techem/ista/Aareon) once it's a repeated paying pattern |
| **EPC** | Customer-provided / manual entry | Automated import as the DE central EPC register matures |
| **Deep BI** | Founder-run "bridge" into my Fabric | Customer self-serve, embedded |
| **Data realism** | Synthetic/sample data, every output QA'd by hand | Real-building data from pilots → tighter, validated models |

- **Say it:** *"Right now I run it lean — Fabric for batch, real-time switched off — because compute capacity is a real cost and I keep burn at zero until a paying customer needs it. The decoupled architecture is already there; I switch on the real-time layer per customer. It's a deliberate cost choice, not a missing piece."*

> 🇹🇷 **Not:** Bu tablo senin en güçlü kozun — "param/kapasitem yok" demek yerine "bilinçli olarak €0 tutuyorum, mimari hazır, müşteri gelince açıyorum" diyorsun. Olgun founder havası.

---

## 4. Per-company playbook
*Each: their angle · likely questions + your answers · what they'll probe (calc/standard) · now→future · TR note.*

### 4.1 metiundo (host) — Dennis Nasrun, CEO
**Their angle:** smart-metering-as-a-service; they own the data/hardware layer (electricity/gas/heat/water), €40M (Octopus), hiring.
**Likely questions & answers:**
- *"How do you work without a smart meter installed?"* → "Estimation-first: archetype + degree-days + bills + EPC, as ranges. When your meters come online, measured values replace the estimates."
- *"How would you use our data?"* → "You own the data pipe; I'm the compliance and decision layer on top — EPBD/CRREM, retrofit prioritization. Your data makes my layer sharper; my layer makes your data more valuable to the owner."
- *"What's your data architecture?"* → "Medallion — bronze/silver/gold on a lakehouse, building_id as the key, per-building and per-unit grain."
**They'll probe:** data model cleanliness, MsbG / iMSys / Smart Meter Gateway awareness, market communication.
**Now→future:** "Today I ingest exports/CSV and bridge into Fabric; with funding I'd take a structured API feed from a metering partner and switch on the real-time path."
> 🇹🇷 **Not:** metiundo = partner + işveren. "Rakip değilim, üst katmanım" mesajı net olsun. CV değil, ilgi göster + LinkedIn.

### 4.2 Green Fusion — Paul Hock, MD
**Their angle:** AI heating optimization + control, GreenBox hardware, GEG §71a TÜV-certified, ~16% measured savings, €12M.
**Likely questions & answers:**
- *"Do you control heating?"* → "No — I assess and screen. I tell the owner which buildings to prioritize; you optimize and run them. Different layers."
- *"How do you estimate HVAC without sub-meters?"* → "HDD/CDD proportional split, transmission heat loss via ISO 13370, insulation score against GEG reference U-values — all as ranges, replaced by measured data where it exists (including yours)."
- *"What about §71a?"* → "I flag it at portfolio level; I'm decision-support, not a certified building-automation system. That's your strength."
**They'll probe:** whether you claim to control (don't), COP/SCOP understanding, GEG §71a.
**Collaboration line:** *"You control and optimize; I sit one layer above with screening and EPBD/CRREM compliance. I hand you a prioritized target list, you execute, I track the compliance impact — complementary, not competing."*
**Now→future:** "Envelope/heat-loss is estimated from geometry assumptions today; with a survey or your operational data it becomes measured."
> 🇹🇷 **Not:** En yakın "rakip" ama en iyi işbirliği/işveren adayı. Rakip tonu YOK — tamamlayıcı + hayran + meraklı.

### 4.3 Rheinwohnungsbau — Benjamin Gaidel (your most strategic contact)
**Their angle:** housing company, ~6,200 rental units (Düsseldorf/Duisburg/Meerbusch/Berlin); already energy-forward (Green Fusion heating, sector-coupling pilots).
**Likely questions & answers:**
- *"What would you give us across 6,200 units?"* → "A portfolio view: EUI and carbon per building, EPBD/MEPS risk, CRREM stranding year, and a ranked retrofit list with BAFA/KfW subsidy-adjusted ROI — i.e. which buildings to act on first."
- *"Do you replace Techem/ista?"* → "No, I sit above them and can use their export. I don't do the billing; I do the portfolio decision and compliance layer."
- *"How accurate is it?"* → "Estimated with ranges now; it tightens with your real data, and I hand-check every figure before it reaches you."
**They'll probe:** HKVO/UVI 2027, EPBD timelines, subsidy logic, effort required from them.
**Discovery (don't sell — ask):** *"With EPBD coming, what's hardest across your portfolio — knowing which buildings to act on first, the data, or the funding case?"*
**Now→future:** "A pilot would be me running a screening from your existing data; with funding I automate the connectors so it's self-serve."
> 🇹🇷 **Not:** Bu odadaki EN değerli sohbet. Satma, keşfet. Pilot = sana gerçek veri + referans; onlara düşük-eforlu EPBD/CapEx netliği.

### 4.4 BET Consulting — Leon Bücher
**Their angle:** large energy consultancy (100+ staff); his talk = smart-meter (iMSys) cost-benefit in multi-family + regulation to 2030.
**Likely questions & answers:**
- *"How could this help our advisory?"* → "Fast multi-building screening with transparent assumptions and branded, exportable reports — a tool that answers 'which building, why' quickly, even on incomplete data. White-label is on the table."
- *"What methods/standards?"* → "Archetype EUI, HDD normalization, ISO 13370 heat loss, GEG U-values, CRREM pathways, ESRS-E1 — all transparent and auditable."
- *"ML or rule-based?"* → "Rule/physics-based and transparent by design — better for advisory and compliance defensibility."
**They'll probe:** methodological rigor, standards, where your numbers come from.
**Now→future:** "White-label/multi-tenant is partly built; I'd harden it for a consulting partner."
> 🇹🇷 **Not:** BET = pazar istihbaratı + olası white-label/freelance/iş. Onlar metodoloji sorar; Bölüm 2'yi iyi bil.

### 4.5 The Mobility House — Sven Böhme, Head of Trading
**Their angle:** V2G + flexibility trading on energy markets ("invisible power plant"); now pure-play flexibility (sold fleet/charging to Edenred).
**Likely questions & answers:**
- *"Do you do flexibility/trading?"* → "No — that's your core. I'm the upstream building data and decision layer. The link is identifying flexibility potential early from a building's existing data."
**They'll probe:** whether you understand flexibility markets (aFRR/FCR, spot/intraday) — mostly listen and learn here.
> 🇹🇷 **Not:** İnce örtüşme, düşük öncelik. Öğren, iddia atma. "Monetizasyon/esneklik" temasını anlamak için iyi.

### 4.6 ZIA — Aygül Özkan (keynote, MD, former minister)
**Their angle:** Germany's main real-estate association. Keynote: "regulatory pressure vs economic opportunity" = your exact thesis.
**Approach:** nothing to sell; reference a concrete keynote point, connect on LinkedIn. Credibility + member network (housing companies).
- *Question if you get a moment:* "You framed it as regulatory pressure vs opportunity — for smaller housing portfolios, which side actually makes them act first?"
> 🇹🇷 **Not:** Çok kıdemli, kalabalık. Hedef = kısa+saygılı + LinkedIn. Uzun sohbet bekleme.

---

## 5. Tough / awkward questions — honest answers
- *"Do you have customers / real data?"* → "Not yet — the platform is built and live, running on realistic synthetic data, and I'm lining up the first pilots. That's exactly why a portfolio like yours is interesting to me."
- *"You're solo?"* → "Yes, for now. I built the full platform myself — domain plus engineering. I'm open to the right partner who brings distribution."
- *"Isn't this just a dashboard?"* → "The dashboard is the surface. The value is the estimation engine and the compliance/decision layer underneath — EPBD/CRREM risk and subsidy-adjusted prioritization."
- *"Aren't you competing with [metiundo / Green Fusion]?"* → "No — they own the data / control layer; I'm the compliance and portfolio-decision layer above. Complementary."
- *"Do customers need a Microsoft Fabric account?"* → "No. They upload existing data; the heavy analytics run on my side. App-owns-data."
- *"Why should I trust the numbers?"* → "Every figure is a range with its assumptions, and I hand-check outputs on a new building before they're used. It's screening/decision-support, not stamped certification."
> 🇹🇷 **Not:** Hiçbirinde savunmaya/özür moduna geçme. Dürüst + net + kısa. "Solo + sentetik veri" = zayıflık değil, dürüstçe söylenince olgunluk.

---

## 6. Glossary — terms you'll hear (own these)

**Energy / buildings**
- **EUI** — Energy Use Intensity, kWh/m²/yr. *(TR: enerji yoğunluğu)*
- **HDD / CDD** — Heating/Cooling Degree Days; weather normalization basis. *(TR: ısıtma/soğutma derece-gün)*
- **U-value** — heat transfer through a building element, W/m²K (lower = better insulated). *(TR: ısı geçirgenlik)*
- **COP / SCOP** — (Seasonal) Coefficient of Performance of a heat pump (heat out ÷ electricity in). *(TR: ısı pompası verim katsayısı)*
- **Sub-metering** — measuring consumption per unit/zone, not just the whole building.
- **Load profile / peak shaving / load shifting** — shape of demand over time, and reducing/moving peaks.

**German regulatory**
- **GEG** — Gebäudeenergiegesetz (Building Energy Act); **§71a** = building-automation duty.
- **EPBD** — EU Energy Performance of Buildings Directive; source of **MEPS** (minimum standards).
- **Energieausweis** — the EPC (energy certificate), classes A–H.
- **HeizkostenV / HKVO** + **UVI** (unterjährige Verbrauchsinformation) — monthly consumption info, mandatory from 2027.
- **MsbG / iMSys / Smart Meter Gateway** — metering law / intelligent metering system / the secure gateway.
- **Messstellenbetreiber** — metering point operator (what metiundo is).
- **BAFA / KfW / BEG** — German subsidy bodies/programs for efficiency & heat pumps.
- **Mieterstrom** — landlord-to-tenant on-site (PV) electricity model.

**Carbon / ESG**
- **Scope 1/2/3** — direct / purchased-energy / value-chain emissions.
- **Location-based vs market-based** — grid-average vs contract/residual-mix Scope 2.
- **Residual mix** — emission factor after green contracts are removed (higher).
- **CRREM** — Carbon Risk Real Estate Monitor; decarbonization pathways & **stranding** year.
- **ESRS-E1 / CSRD / VSME** — EU sustainability reporting standard / directive / voluntary SME standard. *(Say "ESRS-E1-aligned," not "CSRD-compliant.")*
- **EU Taxonomy** — classification of "green" activities/assets.
- **ETS2 / nEHS** — EU/national carbon pricing reaching buildings (~2028 / today).
- **CO2KostAufG** — German law splitting the CO₂ cost between landlord and tenant.

**Flexibility / market (this event's theme)**
- **Flexibility** — ability to shift/shed load or feed in, sold on energy markets.
- **Sektorkopplung** — sector coupling (heat + power + mobility together).
- **V2G** — Vehicle-to-Grid; using EV batteries as grid storage.
- **aFRR / FCR** — automatic frequency restoration / frequency containment reserve (balancing markets).
- **Spot / intraday** — wholesale electricity markets (day-ahead / within-day).
- **"Datengold" / Erlöspotenzial** — the event's framing: data as the asset; revenue potential.

**Tech / data**
- **Medallion (bronze/silver/gold)** — raw → cleaned → business-ready data layers.
- **Microsoft Fabric / lakehouse / DirectLake** — the data platform / storage / fast query mode.
- **RLS** — row-level security (each customer sees only their data).
- **App-owns-data embed** — the customer doesn't need their own BI/Fabric license.

> 🇹🇷 **Not:** Hepsini ezberleme; konuşmada GEÇENLERİ tanı + 4-5 tanesini rahat kullan (EUI, HDD, U-value, Scope 2 location/market, CRREM stranding, GEG §71a). Bu kadarı "ne yaptığını biliyor" izlenimi için yeter.
