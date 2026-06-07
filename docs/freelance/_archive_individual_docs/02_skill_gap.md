# Skill Gap & Self-Study Plan

**For:** Ali Mert Özdemir
**Date:** 2026-05-26
**Goal:** Be fluent enough in CSRD + Microsoft Fabric vocabulary to win freelance discovery calls in English with European clients.

> **Reading guide (tr):** Bu doküman İngilizce yazıldı çünkü müşteri toplantılarında bu cümleleri aynen kullanacaksın. Önemli yerlere Türkçe ipuçları parantez içinde ekledim. Her bölümün sonunda "Drill phrases" kısmı var — bunları yüksek sesle 3-5 kere oku, dilin alışsın. Önce sözcükleri tanı, sonra anlamı pekiştir, sonra cümleyi kuran kalıbı içselleştir.

---

## How to Use This Document

You already have:
- Energy domain (BSBI MSc, building energy systems)
- Microsoft Fabric Data Engineer certification
- A production platform (EnergyLens) you built end-to-end
- Power BI / DAX expertise (v56 measure library)

You **do not yet** have the *vocabulary* clients use in CSRD/ESG conversations, and you don't yet have the *Microsoft analytics sales language* (Direct Lake, Embedded, Copilot) that wins discovery calls.

This document closes those two gaps. **It is not about learning new skills from scratch — it is about translating what you already know into the words clients use.**

(tr: Hiçbir yeni teknik beceri öğrenmiyoruz. Zaten bildiğin şeylerin müşteri dilindeki karşılığını öğreniyoruz. Bu **en yüksek ROI**'li çalışma — birkaç saat içinde "uzman gibi konuşan" konuma geçiyorsun.)

Each section has:
- **What it is** — the definition you need
- **Why the client cares** — the pain point this maps to
- **Talking points** — sentences to use in calls and proposals
- **Drill phrases** — repeat aloud until they feel natural
- **Where to study (free)** — primary source
- **Time budget** — how many hours

Total time budget: **~30 hours over 4 weeks**, or 1–1.5 hours/day.

---

## PART A — Regulatory Vocabulary (ESG side)

This is where most of your freelance pricing power comes from. A client paying €4,500 for a "CSRD Quickstart" does not pay for SQL — they pay for the confidence that you understand their disclosure obligation. (tr: Müşteri SQL yazabilen 100 kişi bulur. Senin CSRD konuştuğunu görünce parayı sorgusuz öder.)

### A1. CSRD — Corporate Sustainability Reporting Directive

**What it is:**
An EU law that came into force in January 2024. It forces companies to publish detailed sustainability reports following a unified standard called **ESRS** (European Sustainability Reporting Standards). It replaces the older, weaker NFRD (Non-Financial Reporting Directive).

**Who must comply, and when:**
- **Wave 1** — Large public-interest companies, FY2024 reports filed in 2025 (already happening)
- **Wave 2** — Other large companies, FY2025 reports filed in 2026 *(your prime market — they are scrambling right now)*
- **Wave 3** — Listed SMEs, FY2026 reports filed in 2027
- **Wave 4** — Non-EU companies with EU turnover >€150M, from FY2028

(tr: Wave 2 = senin altın madenin. Bu şirketler 2026'da rapor vermek zorunda, çoğu hala Excel'de boğuluyor. CSRD dashboard alıcısı bu wave.)

**Why the client cares:**
- Non-compliance penalties (varies by member state, but Germany's Lieferkettengesetz precedent suggests fines up to 2% of global turnover)
- Investor pressure — funds will not buy non-CSRD-compliant company shares
- Bank lending tied to ESG scores (taxonomy regulation)
- They have to produce a report and **they don't know how**

**Talking points:**
> "Are you in Wave 1, Wave 2, or still waiting for Wave 3?" *— this single question tells you their urgency*
> "Which assurance level are you targeting — limited or reasonable?" *(limited is mandatory now, reasonable is mandatory from FY2028 — this signals you know the roadmap)*
> "Have you completed your double materiality assessment yet?" *(this is the foundation of CSRD reporting — if they have not, they cannot file)*

**Drill phrases (repeat aloud):**
1. "CSRD is the EU directive; ESRS is the standard; double materiality is the methodology — they sit together but they are different things."
2. "Your reporting obligation depends on which wave you fall under. Most mid-cap companies I work with are Wave 2, filing FY2025 numbers in 2026."
3. "I help clients translate ESRS datapoints into Power BI dashboards their auditor can sign off on."

**Where to study (free):**
- EFRAG ESRS standards landing page: search "EFRAG ESRS"
- KPMG "CSRD Insights" guides (PDF, free, very clear)
- PwC "Navigating the ESRS" cheat sheet

**Time:** 3 hours total

---

### A2. ESRS E1 — Climate Change Standard

**What it is:**
The most important of the 12 ESRS topical standards. E1 is the climate disclosure. If you sell *one* product, it sells ESRS E1 compliance.

E1 has **9 disclosure requirements (DR), numbered E1-1 to E1-9.** Memorize at least these four:

| Code | What it discloses | Maps to your EnergyLens |
|---|---|---|
| **E1-1** | Transition plan for climate change mitigation | Pages 4-5 (forecast, decision support) |
| **E1-5** | Energy consumption and mix | Pages 1-3 (consumption breakdown) |
| **E1-6** | Gross Scope 1, 2, 3 and Total GHG emissions | Page 6 (GHG dashboard) |
| **E1-9** | Anticipated financial effects of climate risks | Page 9 (battery ROI, scenario analysis) |

(tr: Bu eşleştirme tablosunu ezberle. Müşteri "ESRS E1-6 yapabiliyor musun?" diye sorduğunda kafanda direkt Page 6 belirsin. Bu refleks olmalı.)

**Why the client cares:**
- E1 is the most data-heavy ESRS standard — they need a *tool*, not a Word document
- Auditors are demanding traceable data lineage (every kg of CO₂ must be traceable to a source row)
- This is *exactly* where your Fabric medallion architecture (bronze→silver→gold) becomes the selling point — full lineage is a Fabric superpower

**Talking points:**
> "E1-6 requires you to disclose Scope 1, 2, and 3 separately, both market-based and location-based for Scope 2. Are your current numbers in that format?"
> "ESRS demands traceable methodology. My medallion architecture in Microsoft Fabric gives your auditor row-level lineage from raw bill to disclosed kg CO₂e."
> "We can pre-populate the E1-1 transition plan visualization from your historical baseline and target trajectory."

**Drill phrases:**
1. "Scope 2 must be reported both location-based and market-based. Most companies forget this and get flagged in audit."
2. "ESRS E1-6 is the disclosure; the GHG Protocol is the methodology. They reference each other but they are different documents."
3. "I do not just build a dashboard — I build a dashboard with traceable lineage from raw data to disclosed number."

**Where to study (free):**
- EFRAG ESRS E1 final standard PDF (~80 pages, scan the disclosure requirements section)
- Deloitte "ESRS E1 Implementation Guide" PDF
- One-pager from CDP comparing E1 to TCFD recommendations

**Time:** 5 hours

---

### A3. GHG Protocol Corporate Standard

**What it is:**
The **methodology** for calculating greenhouse gas emissions. Released by the World Resources Institute (WRI) and WBCSD. It defines Scope 1, 2, 3 and the rules for each.

Critically: ESRS E1 *references* the GHG Protocol. They are not the same document, but they go together.

(tr: ESRS sana **ne** raporlayacağını söyler, GHG Protocol **nasıl** hesaplayacağını söyler. İkisi farklı seviyelerde çalışır.)

**The three scopes — memorize cold:**

- **Scope 1 — Direct emissions** from sources the company owns or controls
  - Examples: Natural gas boilers, fleet vehicles, refrigerant leaks (HVAC), industrial process emissions
- **Scope 2 — Indirect emissions from purchased energy**
  - Electricity, steam, heating, cooling that the company *purchases*
  - Reported **two ways**: location-based (grid average emission factor) and market-based (supplier-specific factor, often from green certificates)
- **Scope 3 — All other indirect emissions** across the value chain
  - 15 categories. Most relevant for buildings: Category 1 (purchased goods), Category 6 (business travel), Category 7 (employee commuting), Category 13 (downstream leased assets)

**Why the client cares:**
- They often have Scope 1 + 2 calculated *roughly* in Excel
- Scope 3 is where they get stuck — 15 categories, many data sources, complex
- They have *no idea* about market-based vs location-based Scope 2 — and their auditor will flag this

**Talking points:**
> "Have you calculated market-based Scope 2 yet? It is mandatory under ESRS E1-6 starting with FY2025 reports."
> "Which Scope 3 categories are material for your business? Most building portfolios need at least Category 13 — downstream leased assets — modeled."
> "Refrigerant leaks are Scope 1 and they're routinely missed. Have your facility teams reported R-410A or R-32 refills?" *(this is a power move — shows you understand HVAC operations, not just spreadsheets)*

**Drill phrases:**
1. "Scope 1 is owned, Scope 2 is purchased, Scope 3 is everything else."
2. "Market-based Scope 2 uses your supplier's actual fuel mix. Location-based uses your country's grid average."
3. "Scope 3 has 15 categories. Most clients only need to model 4 or 5 that are material to their business."

**Where to study (free):**
- GHG Protocol Corporate Standard PDF (free download from ghgprotocol.org, ~110 pages but very readable)
- Scope 3 Standard (separate PDF, only read Chapter 5 which lists the 15 categories)
- One-pager: "Location-based vs Market-based Scope 2" — search this exact term

**Time:** 4 hours

---

### A4. EU Taxonomy + EPC + ISO 50001 (lighter touch)

These three you need to recognize and reference, but you do not need deep mastery.

**EU Taxonomy** (sustainable finance classification): A list of economic activities that count as "environmentally sustainable" for investor reporting. Comes up when clients talk about *which buildings qualify for green financing*.
> *Quick line in calls:* "Your taxonomy alignment percentage depends on building EPC ratings — A and B are typically aligned, C and below need substantial renovation."

**EPC — Energy Performance Certificate**: National rating from A to G for buildings, based on kWh/m²/year. Required at point of sale/rent across EU. Different methodologies per country (e.g., DENA in Germany, BREEAM/BER in Ireland).
> *Power line:* "I work with EPC ratings as area-weighted portfolio scores. EnergyLens Page 6 uses LOOKUPVALUE across the building dimension to weight by floor area, not just count buildings."

**ISO 50001 — Energy Management System** standard. Industrial framework for tracking energy performance. Defines **EnPI** (Energy Performance Indicator) and **EnB** (Energy Baseline) — terms that appear in many job postings.
> *Power line:* "Your EnPI should normalize for occupancy, weather (heating/cooling degree days), and production volume. Without that, kWh/m² alone is misleading."

**Time for all three:** 2 hours (just enough to recognize and namedrop)

---

## PART B — Microsoft Analytics Sales Vocabulary

This is the language that makes a client say "this person is technically credible and current."

### B1. Microsoft Fabric — the elevator pitch

You know Fabric internally. Now memorize how to *sell* it in one paragraph.

**The elevator pitch (memorize verbatim, English):**

> "Microsoft Fabric is a unified analytics platform — it combines data engineering, data warehousing, real-time analytics, data science, and Power BI on a single SaaS foundation. The big deal is OneLake — every workload reads and writes the same data layer, so you stop copying data between systems. For sustainability reporting, this matters because your ESRS audit trail stays in one place."

(tr: Bu paragrafı ezberle. Aynen söyle. Boğazından çıkana kadar tekrar et. Müşteri toplantısının ilk 3 dakikasında bunu söyleyince "vay bu adam Fabric biliyor" diyecek.)

**Key terms to drop naturally:**

- **OneLake** — the unified storage layer (one logical data lake across the org)
- **Lakehouse** — Fabric's table store; combines lake flexibility + warehouse semantics
- **Medallion architecture** — Bronze (raw) → Silver (cleaned, conformed) → Gold (business-ready)
- **DirectLake mode** — Power BI reads Parquet files directly from OneLake, no import, no DirectQuery latency
- **Capacity (F-SKU)** — Fabric's pricing unit (F2, F4, F8... F64). Mention F2 as "smallest viable for production POC."

### B2. DP-600 / DP-700 certifications

You hold DP-700 (Data Engineer). DP-600 (Analytics Engineer) is the *more sellable* cert for client-facing BI work — it covers Power BI, semantic modeling, DAX, plus Fabric.

**Do you need to take it?** Only if you have time. Studying for it (without taking the exam) gives you a confidence boost. Actual cert adds maybe 15% to perceived credibility on Malt.

**Free study path:**
- Microsoft Learn "DP-600 Learning Path" — 100% free, official
- Practice exam: search "DP-600 free practice questions" — Whizlabs, MeasureUp samples
- YouTube: "Pragmatic Works DP-600 study guide"

**Time:** 8-12 hours if you sit the exam. Skim 3-4 hours if just for sales credibility.

(tr: Sertifikayı almasak bile öğrenme yolundaki içeriği gez. Müşteri "DAX optimization yapıyor musun?" diye sorduğunda "evet, semantic model best practices'i tüm projelerde uyguluyorum" diyebilmen lazım.)

### B3. Direct Lake mode — the headline feature

This is *the* Fabric talking point because almost nobody understands it yet.

**One-sentence definition:**
> "Direct Lake lets Power BI query data directly from Delta Parquet files in OneLake — no import, no DirectQuery — so you get near-import performance with real-time data freshness."

**Why clients love it:**
- They've been stuck between slow DirectQuery and stale Import mode for years
- Direct Lake gives them both: fast and fresh
- It is a *visible* upgrade — they will pay for someone who configures it correctly

**Drill phrase:**
> "Most teams default to Import mode out of habit. Direct Lake gives you the same performance without the refresh schedule headache — and it's free if you're already on Fabric."

**Time:** 1 hour (read 2 Microsoft Learn pages + watch one Patrick LeBlanc video on Guy in a Cube)

---

### B4. Power BI Embedded + App-Owns-Data

If you sell to ESG consultancies (ICP-A), they want to *resell* your dashboard to their clients. That means embedding.

**Two flavors — know the difference:**

- **User-owns-data** — Each end user needs their own Power BI license. Simple, but client pays per user.
- **App-owns-data** — Service principal authenticates on behalf of users. End users do **not** need Power BI licenses. *This is what consultancies and SaaS resellers need.* Requires a Premium capacity (or PPU + workspace).

(tr: Müşterin başka müşterilerine dashboard satıyorsa **app-owns-data** lazım. Aksi halde her bir son kullanıcı için Power BI lisansı ödemek zorunda kalır. Bu konuyu bilmek = consultancy müşterilerle iş kazanmak.)

**Drill phrase:**
> "If you're white-labeling this dashboard to your clients, you'll want app-owns-data with a service principal — that way your clients don't need Power BI licenses. We need a Premium capacity or PPU workspace for the embed to work."

**Time:** 2 hours (Microsoft Learn "Embed Power BI content" + "Service principal authentication")

---

### B5. Copilot in Fabric / Power BI

Every client asks. You don't need to be a Copilot expert — you need to know what it does and where it doesn't.

**What it does (today, 2026):**
- Generates DAX measures from natural language ("show me YoY growth for revenue")
- Summarizes report pages ("what's notable on this page?")
- Generates Q&A insights ("which customer segment grew most this quarter?")
- Helps write semantic model documentation

**What it does NOT do (be honest):**
- Replace a real semantic model designer — it makes mistakes on complex relationships
- Build dashboards end-to-end from a CSV without curation
- Understand business context — still needs a human to validate

**Drill phrase:**
> "I use Copilot to accelerate measure scaffolding, then refine manually. It's good at 70% of the work but the last 30% is where the value sits."

**Time:** 1 hour (watch any recent Microsoft Reactor Copilot demo + Guy in a Cube episode)

---

### B6. Real-Time Intelligence (Eventhouse, EventStream, KQL)

You already built this for Page 8 (EnergyLens IoT). Memorize the *sales* angle.

**Sales angle:**
> "Most Power BI consultants stop at scheduled refreshes. With Fabric Real-Time Intelligence — EventStream feeding KQL Eventhouse plus a Power BI Direct Lake semantic model — you can show building energy data with sub-second latency. I built one for a 10-building portfolio with BACnet ingestion."

This is a flex that <0.1% of freelancers can pull off. Use it on Malt profile prominently.

**Time:** 0 hours of new study (you built it). Just memorize the sales line above.

---

## PART C — Discovery Call Frameworks

Knowing vocabulary is necessary but not sufficient. You also need a structure for the first call.

### C1. The 30-Minute Discovery Call Structure

```
0–5 min   — Build rapport. Find out their role and what triggered the project.
5–15 min  — Diagnose. Ask the 6 questions below.
15–25 min — Educate (briefly) + position your offering.
25–30 min — Define next step. Either propose or schedule scoping call.
```

### C2. The Six Diagnostic Questions (memorize)

Ask these in this order in every discovery call. Each one is calibrated.

1. **"Walk me through what you have today — what tools, what data sources, what's working and what's painful?"**
   *(Lets them vent. You learn the landscape. 3-4 minutes of their talking.)*

2. **"What triggered you to start looking for help right now?"**
   *(Reveals urgency. If they say "audit in 6 weeks" — high urgency, premium price. If they say "exploring options" — low urgency, longer sales cycle.)*

3. **"Are you in CSRD Wave 1, Wave 2, or not yet in scope?"** *(only ask if ESG context)*
   *(Quickly calibrates regulatory pressure.)*

4. **"Who is the end consumer of this report — the CFO, the sustainability officer, your auditor, your investors?"**
   *(Different consumers need different dashboards. CFO wants €cost. Auditor wants lineage. Investor wants trend.)*

5. **"What's your timeline and budget range?"**
   *(Ask directly. Most freelancers chicken out of this. If you don't ask, you'll quote in the dark.)*

6. **"What does 'done' look like for you in this engagement?"**
   *(Forces them to define success. Protects you from scope creep.)*

### C3. The "Position-and-Propose" Move (last 10 minutes)

Once you've diagnosed, transition with this exact sentence:

> "Based on what you've described, I think the best fit is one of two paths..."

Then offer two productized packages from positioning brief (P1-P4). Always two — not one, not three. Two options force a choice rather than yes/no.

(tr: Sadece bir teklif sunma — "evet/hayır" psikolojisine sürüklenir. İki teklif sun — müşteri "A mı B mi?" diye düşünür. Bu pazarlama psikolojisi temel taktiği. Genelde A'yı seçerler, ki o senin tercih ettiğin paket olur.)

---

## PART D — 4-Week Study Schedule

| Week | Daily time | Focus | Deliverable to yourself |
|---|---|---|---|
| **Week 1** | 1.5 hr | A1 (CSRD), A2 (ESRS E1), A3 (GHG Protocol) | Can answer any client question about Scope 1/2/3 unprompted |
| **Week 2** | 1.5 hr | A4 (Taxonomy/EPC/ISO 50001), B1 (Fabric pitch), B2 (DP-600 highlights) | Can deliver the Fabric elevator pitch in 60 seconds without notes |
| **Week 3** | 1.5 hr | B3 (Direct Lake), B4 (Embedded), B5 (Copilot), B6 (Real-Time) | Can demo each on screen-share if asked |
| **Week 4** | 1 hr | C1, C2, C3 (Discovery framework) + 3 mock calls | Run 3 mock discovery calls with yourself or a friend. Record. Listen back. |

**Total: ~30 hours over 4 weeks**, but **you only need Weeks 1+2+C2 before sending first proposals.** Weeks 3+4 happen in parallel with the first applications.

---

## PART E — Common Client Questions and Your Pre-Built Answers

Memorize these. You will get every one of them eventually.

### "What's your hourly rate?"
> "I work on fixed-scope packages where possible — that gives you cost certainty. For ad-hoc work, my opening rate is €60/hour. I'm flexible based on project scope and duration."

### "Do you have CSRD certification?"
> "There is no official 'CSRD certification' that exists today — the regulation is too new. I work with the actual EFRAG ESRS standards and the GHG Protocol methodology. I'm Microsoft Fabric Data Engineer certified, which is what underpins the technical delivery."

### "Can you do this in Tableau / Looker?"
> "I specialize in the Microsoft Fabric and Power BI stack. If you're locked into Tableau, I'd recommend a Tableau specialist — happy to refer one. If you have flexibility on the BI tool, I can show you why Fabric is significantly stronger for the lineage requirements CSRD demands."

### "We need this in 2 weeks. Can you do it?"
> "For a Scope 1/2/3 baseline dashboard with 2-3 data sources, 2 weeks is realistic with my P1 Quickstart package. If you need full ESRS E1 mapping across all 9 disclosures, that's a 4-week engagement. Let's scope what 'done' means for the 2-week version."

### "Can you work on our existing Power BI?"
> "Yes — I do a lot of remediation work. Typical pattern: 2-day audit, then a fixed-scope improvement sprint based on the audit findings. The audit alone is €1,200 and includes a written roadmap you keep regardless of next steps."

### "We have no Microsoft Fabric — should we get it?"
> "Not necessarily. Power BI Premium Per User is enough for many CSRD use cases. Fabric pays off when you have real-time data, multi-source integration, or you need OneLake's audit lineage. Let me look at your data sources before recommending."

### "We're a small company — can you make this affordable?"
> "I have a starter package — P2 Building KPI Dashboard at €1,800 for up to 5 buildings. That covers EnPI, kWh/m², and EPC mapping. If that's still too high, we can talk about a 1-day audit at €500 to scope something narrower."

(tr: Bu hazır cevapları ezberle. Müşteri telefonda sorduğunda hiç tereddüt etmemen lazım — fiyat sorusunda 3 saniye duraklamak güvensizlik sinyali verir. Aynayla pratik et.)

---

## PART F — Resources Checklist (Bookmark These)

**Regulatory (free PDFs):**
- EFRAG ESRS E1 final standard
- GHG Protocol Corporate Standard
- GHG Protocol Scope 3 Standard
- KPMG / PwC / Deloitte CSRD readiness guides

**Microsoft (free):**
- Microsoft Learn DP-600 path
- Microsoft Learn DP-700 path (refresh)
- Guy in a Cube YouTube channel
- Pragmatic Works YouTube
- Microsoft Fabric documentation (docs.microsoft.com/fabric)

**Industry context (free):**
- IEA Buildings Tracker (annual buildings energy outlook)
- BPIE (Buildings Performance Institute Europe) reports
- CDP disclosure guides

**Practice (free):**
- Reddit /r/PowerBI for live job questions
- Stack Overflow [microsoft-fabric] tag
- LinkedIn ESG/CSRD groups (read, don't post yet)

---

## Final Note

You don't need to know everything in this document before sending the first proposal. You need:

- **Day 1:** A1, A2, A3 + the 6 diagnostic questions
- **Day 7:** Add B1 (Fabric pitch) + B3 (Direct Lake) + B6 (Real-Time)
- **Day 14:** Everything else in passing fluency

Send the first proposals at Day 7. Refine the rest while live in the market. Don't wait to be perfect — perfect is the enemy of paid.

(tr: Hazırlık vs uygulamayı karıştırma. 7 gün ön çalışma yeterli — sonra teklif göndermeye başla. Eksiklerini canlı işlerde tamamlarsın.)
