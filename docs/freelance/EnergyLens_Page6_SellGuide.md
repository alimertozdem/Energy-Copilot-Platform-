---
title: "EnergyLens — Page 6 (Sustainability & GHG): the sell-it study guide"
subtitle: "Read every visual · know every formula · answer every client question"
author: "Ali Mert Özdemir"
date: "2026-06-10"
---

# How to use this guide

This is your **single source of truth for Page 6** — the sustainability / GHG / ESRS E1 page.
After reading it once you can: read any visual on the page out loud, explain how each number is
calculated, name the standard behind it, and answer the questions a client or an auditor will
ask — without hesitating. That hesitation is the only thing standing between you and the deal.

> **tr:** Bu doküman Page 6'yı *satabilmen* için. Amaç: müşteri "bu sayı nasıl çıktı?", "market mi
> location mı?", "Scope 3'ü nasıl buldun?" dediğinde bir saniye bile duraksamadan cevap verebilmen.
> İngilizce ana metin (müşteriyle İngilizce konuşacaksın); her bölümde **tr:** ile kısa Türkçe ipucu.

**Golden rule of selling this page:** you are not selling a dashboard, you are selling
**confidence that the numbers are correct and the methodology is defensible.** Anyone can drag a
field onto a chart. Almost nobody can explain market-based Scope 2 or a CRREM stranding year. That
explanation *is* the product.

---

# 1. What Page 6 is, in one breath

Page 6 turns a building portfolio's energy data into a **CSRD / ESRS E1-aligned carbon report**:
the full Scope 1 / 2 / 3 footprint, the mandatory dual (location + market) Scope 2 view, the
CRREM decarbonisation / stranding risk, the EPC compliance grade, and a prioritised action list —
all with traceable lineage from a raw factor to a disclosed kg of CO₂.

**Who reads this page (and what they want first):**

- **Sustainability / ESG manager** — "Is my Scope 1/2/3 report-ready? Both Scope 2 methods?"
- **External auditor / assurance provider** — "Can I trace every number to a source? Is the method right?"
- **CFO / asset manager** — "What's my carbon cost and which buildings are a stranding liability?"
- **ESG consultancy (your best client)** — "Can I resell this as a productised CSRD dashboard?"

> **tr:** Page 6 = ESG/CSRD raporlama sayfası. İlk bakan kişi "Scope 1/2/3 hazır mı, iki Scope-2
> metodu da var mı, hangi binam stranded?" diye sorar. Sen bunların hepsine görselle cevap veriyorsun.

---

# 2. The vocabulary you must own (the standards behind the page)

Memorise the difference, because clients test it in the first five minutes.

**GHG Protocol — the *method* (HOW you calculate).** Published by WRI + WBCSD. Splits emissions
into three scopes. This is the calculation rulebook.

- **Scope 1 — direct:** what *you* burn/leak. Gas boilers, fleet diesel, **refrigerant leaks**.
- **Scope 2 — purchased energy:** the grid electricity / heat you buy. Reported **two ways**
  (see §4).
- **Scope 3 — everything else in the value chain:** 15 categories. For buildings the material ones
  are **Cat 13 (tenant energy)**, **Cat 1 (embodied carbon of materials)**, **Cat 3 (fuel & energy
  upstream)**, and Cat 5/6/7 (waste / travel / commuting).

**ESRS E1-6 — the *disclosure* (WHAT you must report).** Part of the EU's CSRD. Requires gross
Scope 1, 2, 3 and total, with Scope 2 shown **both location- and market-based**. ESRS *references*
the GHG Protocol — they go together but are different documents.

**CRREM — Carbon Risk Real Estate Monitor.** A science-based decarbonisation pathway (allowed
kg CO₂/m²/yr falling year by year to stay within 1.5/2 °C). The year a building's intensity crosses
above the curve is its **stranding year** — when it risks becoming a regulatory/market liability.
CRREM compares on a **Scope 1+2** basis (it excludes Scope 3).

**EPC — Energy Performance Certificate.** National A+→G rating (kWh/m²/yr). Compliance / MEPS signal.

**Disclosure-grade vs estimate — the honesty concept.** A number is *disclosure-grade* when it's
real measured data × a sourced factor with full lineage (Scope 1 & 2 here). It's an *estimate* when
it relies on screening factors or benchmarks (Scope 3 here). You **always label estimates** — that
honesty is what an auditor and an academic reward.

> **tr:** **ESRS = NE raporlayacağın, GHG Protocol = NASIL hesaplayacağın.** İkisi farklı seviye.
> CRREM Scope 1+2 bazında çalışır (Scope 3 hariç). "Disclosure-grade" = gerçek veri × kaynaklı
> faktör; "estimate" = benchmark/tahmin → her zaman etiketle.

---

# 3. The data engine behind every number (lineage — your credibility weapon)

Every number on Page 6 comes from **two gold tables**, fed by a **sourced reference layer**:

- `gold_ghg_scope` — one row per building × month, with every scope/sub-component as a column
  (`scope1_gas/diesel/refrigerant`, `scope2_location/market`, `scope3_cat1/3/5/6/7/13`, totals,
  method flags, `scope3_disclosure_grade`).
- `gold_ghg_breakdown_long` — the same data **unpivoted** into a `scope` × `category` dimension, so
  one measure (`Emissions tCO2e`) drives the drillable category visuals.
- **Reference layer (single source of truth):** `ref_grid_emission_factors` (UBA, EEA),
  `ref_residual_mix` (AIB), `ref_fuel_factors` (DEFRA), `ref_refrigerant_gwp` (IPCC),
  `ref_embodied_carbon` (RICS/LETI) — each row carries source + URL + year.

**The sentence that wins trust:** *"Every disclosed kg of CO₂ traces back through a sourced,
year-indexed factor to a raw consumption row — that's the row-level lineage an auditor needs, and
it's exactly what Microsoft Fabric's medallion architecture gives me."*

**The honest provenance line (say it before they ask):** *"The operational data here is synthetic
demo data for 10 representative buildings — flagged `synthetic_demo`. The methodology and every
emission factor are real. The moment a client's real meter/contract data lands, it replaces the
same tables and the numbers become that building's actual footprint — the engine doesn't change."*

> **tr:** İki gold tablo (`gold_ghg_scope` + `gold_ghg_breakdown_long`) + kaynaklı referans katmanı.
> Satış cümlesi: "Her kg CO₂ ham satıra kadar izlenebilir" (lineage). Dürüstlük cümlesi: "operasyonel
> veri sentetik, metodoloji+faktör gerçek; pilot gelince aynı tabloyu değiştir, motor değişmez."

---

# 4. The top KPI cards — read / tell / calc / know

### GHG Intensity (kgCO₂/m²/yr) · e.g. 490.8

- **Read:** portfolio carbon per square metre of conditioned floor area.
- **Tells:** efficiency benchmark — lets you compare a small office to a huge datacenter fairly.
- **Calc:** `(Scope 1 + Scope 2) tCO₂ × 1000 / conditioned_area_m²`. **Scope 1+2 only** (operational)
  — deliberately *excludes* Scope 3, so it matches the CRREM basis.
- **Know:** datacenters/hospitals are naturally very high (2000+); offices ~50–150. A high portfolio
  number usually means a few heavy assets, not a calculation error.
- **Say:** *"Intensity is Scope 1+2 per m² — the same basis as CRREM, so the two visuals are consistent."*

> **tr:** m² başına karbon (S1+2). CRREM ile aynı baz olması önemli — Scope 3 KATMA.

### EPC Portfolio Grade · e.g. D

- **Read:** the portfolio's energy-performance grade, A+ (best) to G (worst).
- **Tells:** regulatory exposure — under the EPBD/MEPS, the worst grades must be renovated by
  2030/2033.
- **Calc:** **area-weighted** across buildings: `Σ(area × EPC_score) / Σ(area)` — *not* a plain
  average. (A plain average is a classic audit failure: a 50 m² building must not count the same as
  a 50,000 m² one.)
- **Know:** EPC ratings come from the national register / the building's Energieausweis. In the demo
  they're representative.
- **Say:** *"The portfolio grade is area-weighted, so it reflects where the floor area actually is —
  the way an auditor expects."*

> **tr:** EPC notu **alan-ağırlıklı** (düz ortalama denetim hatası). MEPS riski sinyali.

### Scope 1 / 2 / 3 split (multi-row card) · e.g. 3.0K / 35.5K / 29.8K tCO₂e

- **Read:** the headline footprint composition — how much of total emissions is each scope.
- **Tells:** *where the carbon is.* Here Scope 2 (purchased electricity) dominates, Scope 1 is small
  (mostly gas), Scope 3 is large (embodied + tenant + upstream).
- **Calc:** three measures — `Scope 1 Total`, `Scope 2 Location`, `Scope 3 Total (est.)`. They sum to
  the **Total GHG (location)** card — always reconcile these.
- **Know:** for most building portfolios **Scope 3 is the biggest bucket** in reality (tenant energy);
  here it's an estimate, clearly flagged.
- **Say:** *"This is the composition an ESRS E1-6 reader wants first — and notice Scope 3 is material,
  which is why we model it by category, not as a flat percentage."*

> **tr:** Footprint kompozisyonu. Üç sayı = Total GHG location ile tutmalı. Gerçekte Scope 3 (kiracı)
> en büyük kovadır.

### Total GHG — location (68.4K) vs market (88.9K) tCO₂e

- **Read:** the same total footprint computed two ways for Scope 2.
- **Tells:** the **ESRS E1-6 dual-reporting** story. Market > location here because most supply is
  *unbacked* → priced at the dirtier **residual mix** (see §5).
- **Calc:** `Scope1 + Scope2(location or market) + Scope3`. Only the Scope 2 component differs.
- **Know:** a green-contract building flips it the other way (market << location). The portfolio shows
  both — that's correct.
- **Say:** *"Both numbers are mandatory under ESRS E1-6. The gap is the real story: it shows how much
  of your supply is backed by green contracts versus exposed to the residual mix."*

> **tr:** Aynı toplam, iki Scope-2 metodu. Market > location = tedarik çoğunlukla sözleşmesiz →
> residual mix (daha kirli). İkisi de ESRS zorunlu.

### CO₂ Carbon Levy · e.g. €143,650

- **Read:** the estimated annual carbon-cost exposure of the portfolio.
- **Tells:** the **financial** translation of emissions — what carbon pricing (EU ETS / the coming
  ETS2 for buildings) could cost.
- **Calc:** `emissions tCO₂ × carbon_price €/t` (EU ETS ~€60–80/t range).
- **Know:** this is what makes a CFO care — it turns "kg CO₂" into euros. Label it an estimate; the
  exact price and which scheme applies vary.
- **Say:** *"This is the CFO line — it prices your carbon at the ETS rate, so decarbonisation becomes
  a cost-avoidance number, not just a compliance one."*

> **tr:** Emisyonun €karşılığı (ETS fiyatı). CFO'yu ilgilendiren kart — karbonu euroya çevirir.

### CRREM Stranding Yr · e.g. Stranded

- **Read:** the year the portfolio's intensity crosses above the CRREM pathway (or "Stranded" if
  already past it).
- **Tells:** **asset-value risk** — a stranded asset loses value / faces forced retrofit.
- **Calc:** compare `carbon_intensity (S1+2 / m²)` to the type/region CRREM curve; the crossing year
  is the stranding year.
- **Know:** REITs and asset managers care intensely about this. The pathways here are **indicative**
  1.5 °C anchors, not the licensed CRREM v2 dataset (CRREM opens a free Library mid-2026; embedding it
  commercially needs a License Partner agreement).
- **Say:** *"Stranding is the investor's number. My pathways are indicative today; the official CRREM
  curves drop into one isolated module when I take the License Partner step."*

> **tr:** Stranding = atıl-varlık riski (yatırımcı sayısı). Eğri **indikatif** (resmî CRREM v2 değil;
> ticari gömme için License Partner). Karşılaştırma S1+2 bazında.

### EU Carbon Score (27.1) · ESRS E1 data coverage % (100%) · Scope 3 status ("Estimated")

- **EU Carbon Score:** a **platform-defined composite** (0–100): EUI vs benchmark, CO₂ intensity,
  renewable share, compliance. Present it as *"our internal benchmark score,"* never an official rating.
- **ESRS E1 data coverage %:** the share of E1 datapoints you have *data* for — not a claim of
  audit-readiness. Keep it paired with the "Estimated" caption so coverage ≠ disclosure-grade.
- **Scope 3 status caption:** the honesty flag. Reads "Estimated" because Scope 3 is a category-
  structured estimate, not disclosure-grade.

> **tr:** EU Carbon Score = bizim iç skorumuz (resmî değil — öyle sun). Coverage % = veri kapsamı,
> "denetime hazır" demek DEĞİL. "Estimated" = Scope 3 dürüstlük etiketi.

---

# 5. The six main visuals — read / tell / calc / know / say

### V1 · Carbon Intensity vs CRREM Pathway & annual GHG trend (line)

- **Read:** two lines over time — your portfolio's carbon intensity (S1+2, kg CO₂/m²) and the CRREM
  2 °C pathway. Where your line sits *above* the pathway, you're stranded.
- **Tells:** the trajectory — are you decarbonising fast enough to stay under the curve?
- **Calc:** intensity per year vs the pathway value per year (type/region).
- **Know:** the pathway *falls* every year (the allowance tightens); staying flat means you strand
  later as the curve drops to meet you.
- **Say:** *"The pathway tightens annually — so even flat performance eventually strands. This visual
  shows the year that happens."*

> **tr:** Senin yoğunluk çizgin vs CRREM eğrisi. Eğri her yıl düşer; üstünde kaldığın yıl = stranded.

### V2 · CRREM Status by Building (table, worst-first)

- **Read:** per building — current intensity, the pathway value, and STRANDED / On track. Sorted so
  the worst offenders are at the top (Frankfurt Datacenter 2238, Klinikum 760, …).
- **Tells:** *which buildings drag the portfolio down* — the retrofit priority list.
- **Calc:** per-building intensity vs that building's pathway.
- **Know:** datacenters/hospitals are structurally high-intensity — "stranded" there often means
  "needs on-site generation / heat recovery," not "close it."
- **Say:** *"This is your action triage — the top three rows are where 80% of the stranding risk and
  the retrofit budget should go."*

> **tr:** Bina-bazlı stranded/on-track, en kötü başta = yenileme öncelik listesi. Datacenter/hastane
> doğal olarak yüksek — "stranded" = müdahale gerek, "kapat" değil.

### V3 · Emissions by building & category (stacked column + Scope 1/2/3 button)

- **Read:** per building, emissions broken into **categories**, filtered by the Scope button. Pick
  Scope 3 → the six Scope 3 categories; Scope 1 → gas/diesel/refrigerant; Scope 2 → electricity.
- **Tells:** *what kind* of emissions each building has — the composition that drives the right action
  (e.g. high Cat 13 → engage tenants; high Cat 1 → it's embodied, a one-off).
- **Calc:** one measure `Emissions tCO2e = SUM(gold_ghg_breakdown_long[value_tco2])`, split by the
  `category` dimension; the Scope button slices the `scope` dimension.
- **Know:** Scope 3 categories are **estimates** (embodied benchmark, headcount-based, tenant proxy) —
  the `data_grade` field separates "core" from "estimated." Cat 3 (fuel & energy upstream) is the one
  Scope 3 category computed from *real* consumption, so it's the most defensible.
- **Say:** *"Because category is a real dimension, you drill from any scope into its components — and
  I flag which parts are measured versus estimated, so nothing is overstated."*

> **tr:** Scope butonuyla kategori-bazlı kompozisyon. Tek ölçü + `category` boyutu. Scope 3 kategorileri
> tahmin; **Cat 3** gerçek tüketimden hesaplanır (en savunulabilir). `data_grade` core/estimated ayırır.

### V4 · Scope 2 — Location vs Market-based (ESRS E1-6) (clustered column)

- **Read:** per building, two bars — location-based and market-based Scope 2.
- **Tells:** the **dual-reporting** story and the procurement quality of each building. A building with
  a green contract shows market << location; an unbacked one shows market > location (residual mix).
- **Calc:** location = `grid_kwh × grid_factor`. Market factor follows the **GHG Protocol hierarchy**:
  `supplier-specific (GoO/PPA) → residual mix → location`. The residual mix is *higher* than the grid
  average (e.g. Germany 0.725 vs 0.363 kg/kWh) because once the green attributes are sold as GoOs, the
  *remaining* mix is dirtier.
- **Know:** this is the single most common audit failure — companies use the grid average for unbacked
  supply instead of the residual mix. Getting it right is a genuine differentiator.
- **Say:** *"Market-based isn't just 'green tariff = lower.' With no contract, the correct factor is the
  residual mix, which is dirtier than the grid average. Most tools get this wrong; mine follows the GHG
  Protocol hierarchy."*

> **tr:** İki bar = location vs market. Market faktörü: sözleşme(GoO) → **residual mix** → location.
> Residual location'dan YÜKSEK (DE 0.725 vs 0.363). En sık denetim hatası — sen doğrusunu yapıyorsun.

### V5 · CO₂ Emission Trend (annual) (line)

- **Read:** total emissions, net carbon footprint, and total savings over the years.
- **Tells:** the decarbonisation trajectory and the impact of interventions (solar, efficiency).
- **Calc:** annual aggregation of total CO₂; net = gross − avoided (solar etc.); savings = avoided.
- **Know (gotcha):** if the latest year is a **partial year**, the line drops sharply and looks like
  emissions crashed — filter to complete years or label the partial one.
- **Say:** *"Net footprint is gross minus what your on-site generation avoided — it's the number that
  improves when you act."*

> **tr:** Yıllık toplam/net/tasarruf. **Dikkat:** son yıl yarımsa çizgi çakılır, yanlış okunur — tam
> yıllara filtrele.

### V6 · Priority Actions & Incentives (cards)

- **Read:** recommended action per selected building + matched funding programme + risk flag.
- **Tells:** the **decision-support** layer — turns the diagnosis into "do this, here's the grant."
- **Calc:** rule-based recommendations ranked by priority/savings, matched to incentives (KfW, BAFA,
  YEKA, EEG) by country and measure.
- **Know:** this is what moves the page from "reporting" to "advisory" — and advisory is what clients
  pay retainers for.
- **Say:** *"Reporting tells you the problem; this row tells you the cheapest fix and the grant that
  pays for part of it. That's the difference between a dashboard and a decision tool."*

> **tr:** Bina-bazlı öneri + eşleşen teşvik. Sayfayı "raporlama"dan "danışmanlık"a taşır — retainer
> burada satılır.

---

# 6. The ten questions a client (or auditor) will ask — and your answers

1. **"Is Scope 2 location and market both there?"** → Yes (V4). Market follows the GHG Protocol
   hierarchy with the residual mix as the no-instrument fallback.
2. **"How do you do Scope 3?"** → Category-based for the material ones (Cat 13 tenant, Cat 1 embodied,
   Cat 3 fuel & energy upstream, Cat 5/6/7). Flagged as an estimate, not disclosure-grade.
3. **"Is this Scope 3 disclosure-grade?"** → No, and I label it. Cat 3 is real-method on real
   consumption; the rest are benchmark/activity estimates until I get tenant & supplier data.
4. **"Did you include refrigerants in Scope 1?"** → Yes — the F-Gas logbook top-up × IPCC GWP. The
   most-forgotten Scope 1 source.
5. **"Are your grid factors current and sourced?"** → Year-indexed: UBA for Germany (0.363/2024),
   EEA for the rest, TEİAŞ for Turkey — each with source + URL.
6. **"Is this CRREM official?"** → The curves are indicative 1.5 °C anchors today, isolated in one
   module; official CRREM v2 swaps in via the License Partner step / the free CRREM Library.
7. **"Can you guarantee CSRD compliance?"** → No tool can — the auditor issues assurance. I provide
   **ESRS-E1-aligned, report-ready** numbers with full lineage that make the audit fast.
8. **"Where does the data come from?"** → Real building data via meters/bills/BMS; external signals
   (weather, prices, grid CO₂) from free official APIs; factors from the sourced reference layer.
9. **"What's your EPC methodology?"** → Area-weighted across the portfolio, not a plain average.
10. **"Can I resell this to my clients?"** → Yes — it's a productised template; we adapt the silver
    tables to each client's data, the engine and the model stay the same.

> **tr:** Bu 10 soruyu ezberle — müşteri/auditor ilk yarım saatte sorar. Her birinde dürüst + net
> cevap güven verir.

---

# 7. What to say — and what NOT to say (claims discipline)

**Say:** "ESRS-E1-aligned reporting support." "Auditable Scope 1 & 2 with row-level lineage."
"Method-correct market-based Scope 2 (residual mix)." "Indicative CRREM pathways." "Estimated,
category-structured Scope 3."

**Never say:** "CSRD-compliant" / "audited" / "guaranteed accurate" / "Taxonomy-aligned" /
"official CRREM." These are overclaims that an academic will catch and that create
**greenwashing / legal risk** — the opposite of what wins the deal.

**Why this wins:** naming the exact gap and the exact source to close it is the strongest possible
credibility signal. "I know precisely what isn't real yet and precisely how to fix it" beats
"everything is finished" every time — with a professor *and* with a paying client.

> **tr:** "ESRS-E1-aligned / report-ready" de; "CSRD-compliant / audited / guaranteed" DEME. Aşırı
> iddia = greenwashing/hukuk riski. Dürüst sınır söylemek en güçlü güven sinyali.

---

# 8. One-page recap (print this)

- Page 6 = the ESRS E1 carbon report: Scope 1/2/3 + dual Scope 2 + CRREM + EPC + actions.
- ESRS = what to report; GHG Protocol = how; CRREM = stranding (S1+2 basis); EPC = compliance.
- Scope 1 = gas + diesel + **refrigerant**. Scope 2 = location **and** market (residual-mix fallback).
  Scope 3 = Cat 1/3/5/6/7/13, **estimated and labelled**.
- Intensity, CRREM and the multi-row split are **Scope 1+2**; totals add Scope 3.
- Market > location ⇒ unbacked supply on the residual mix (the dual-reporting story).
- Lineage = every kg traces to a sourced factor (your credibility).
- Honesty = label every estimate; "support, not assurance"; the auditor signs, not the tool.

> **tr:** Bu son sayfayı yazıcıdan çıkar, toplantı öncesi 2 dakika oku. Hepsi burada.

---

*EnergyLens — a Microsoft Fabric-native energy-intelligence & ESG-reporting platform for commercial
buildings. This guide describes Page 6 (Sustainability & GHG). Methodology and factors are real and
sourced; demo operational data is synthetic and flagged, swappable for real client data with no
engine change.*
