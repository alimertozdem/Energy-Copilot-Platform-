# BSBI Outreach — Mail Şablonları

**Hedef:** İki BSBI iletişimini hızlı başlatmak.
**Format:** İngilizce (BSBI uluslararası kurum).
**Strateji:** Supervisor → advisor letter / mentorship → **EXIST başvurusu için zorunlu**. Facility Manager → ücretsiz pilot → ilk müşteri case study.

---

## 1. SUPERVISOR MAİLİ — Advisor / Reference Talebi

**Önemli:** Hocan zaten LinkedIn'den olumlu yanıt vermiş. Bu mail o sıcaklığı **resmi e-posta kanalına taşıma** ve **somut talep** yapma maili. EXIST için kritik.

### Subject satırı (3 alternatif):

1. `Following up on our LinkedIn chat — EnergyLens project & EXIST application`
2. `EnergyLens platform — supervisor/advisor relationship & reference letter request`
3. `Quick follow-up: EnergyLens, EXIST Gründerstipendium, and your potential mentorship`

→ Önerim: **#1** (LinkedIn referansı verir, sıcak başlangıç)

### Mail gövdesi (kopyala-yapıştır + kişiselleştir):

```
Dear Professor [SOYADI],

Thank you for the warm reply on LinkedIn a few days ago — it really meant a lot. As I mentioned briefly there, I have been building a project called **EnergyLens**, a Microsoft Fabric-native energy intelligence platform for European commercial buildings, and I would like to share where it stands and ask for your guidance on next steps.

**What EnergyLens does (in two sentences):**
EnergyLens unifies energy data from multiple buildings into a live, multi-source platform with built-in EU regulatory compliance scoring (CRREM 2030, EnEfG, EU Battery Regulation 2023/1542). It pairs a 9-page Power BI analytics layer with a Next.js + FastAPI web application and an AI Copilot that uses LLM tool use to answer natural-language questions over the Microsoft Fabric Lakehouse.

**Current state (April–May 2026):**
- 10 representative buildings (Germany, Turkey, Austria, Netherlands), 3.5 years of data, ~693,000 data points
- 57 Lakehouse tables across Bronze/Silver/Gold layers
- Web application live with three-provider authentication, /portfolio, /buildings/[id], and /copilot pages
- AI Copilot with six production tools, server-sent-events streaming, conversation persistence
- Microsoft DP-600 certification (Implementing Analytics Solutions Using Microsoft Fabric)
- All built solo, end-to-end, in roughly five weeks

I have attached / linked below:
- A 90-second founder intro video: [YOUTUBE_LINK_FOUNDER]
- A ~3.5-minute product demo video: https://youtu.be/0IiqssHYtkY
- A one-page executive summary (PDF, attached) — happy to share the full architecture document, GTM strategy, or revenue model if useful

**Why I am writing now — two specific requests:**

1. **EXIST Gründerstipendium application.** EXIST requires a university affiliation and an academic mentor/supervisor letter. Given that EnergyLens has grown directly out of my M.Sc. work, I would be honored if you could serve as the academic mentor on the application. This would mean (a) one or two short conversations between now and submission to align scope, and (b) a brief letter of support from BSBI for the application package. I can prepare a draft of the letter for your review based on what is typically required.

2. **Project advisory going forward.** Independent of EXIST, I would value an ongoing advisory relationship — periodic check-ins (monthly or quarterly) where I can share progress and learn from your guidance on energy management and academic angles. No formal commitment needed, just openness to occasional input.

If either of these is of interest, I would love to schedule a short call — 20 to 30 minutes — at your convenience. I am happy to come to campus or do it virtually, whichever is easier for you.

Thank you again for your time and your earlier message. Looking forward to your reply.

Warm regards,
Ali Mert Özdemir
M.Sc. Energy Management, BSBI Berlin (June 2026 graduation)
Microsoft DP-600 Certified
LinkedIn: https://www.linkedin.com/in/alimertozdemir96/
GitHub: https://github.com/alimertozdem
energylens.eu
```

### Kişiselleştirme yerleri:

- `[SOYADI]` → hocanın gerçek soyadı
- `[YOUTUBE_LINK_FOUNDER]` → founder video YouTube link'i (henüz vermedin, link'i bul ve yapıştır)
- "On LinkedIn a few days ago" → eğer 1 hafta+ olduysa "last week" veya tarih net ver
- Eğer hoca özel bir alandan ise (örnek: HVAC, building energy modeling, sustainability), o alana **1-2 cümle bağ kur**: "Given your expertise in [X], your guidance on Y would be particularly valuable" gibi

### Ekleyeceğin dosyalar:

- `02_executive_summary.md` → PDF'e dönüştür → ekle (Word'e import edip File → Export → PDF, veya online md-to-pdf)
- Founder + demo video link'leri mail gövdesinde

### Gönderme zamanı:

- **Salı veya Çarşamba sabah** (9:00-11:00 arası) — akademik mail engagement en yüksek olduğu zaman
- Pazartesi gönderme: hafta sonu emaillerine bulanır
- Cuma öğleden sonra gönderme: hafta sonuna saplanır

### Follow-up:

- **7 iş günü** içinde cevap gelmezse: kısa nazik follow-up
  - Subject: `Re: Following up on our LinkedIn chat — EnergyLens project`
  - Gövde: "Dear Professor X, just wanted to gently follow up on my message from [tarih]. No rush — I know this is a busy time. Happy to wait, just wanted to make sure my mail didn't get lost. Best, Mert"
- 14 gün+ cevap yok: LinkedIn DM ile dürtebilirsin

---

## 2. FACILITY / SUSTAINABILITY MANAGER MAİLİ — Pilot Teklif

**Hedef:** BSBI kampüsünün enerji datasını ücretsiz pilot olarak kullanmak. Karşılığında EnergyLens'in ilk **case study**'si.

### Önce kim — araştır:

LinkedIn'de ara:
- `"BSBI" facility manager`
- `"BSBI" sustainability`
- `"BSBI" operations director`
- `"Berlin School of Business and Innovation" facility`

BSBI website'ında "Sustainability" veya "Campus" sayfasında isim olabilir. Bulamazsan generic mail: `facility@berlinsbi.com` veya `sustainability@berlinsbi.com` (önce doğrula).

### Subject satırı:

`Free pilot proposal: real-time energy intelligence for BSBI campus — M.Sc. capstone project`

### Mail gövdesi:

```
Dear [İSİM] / Dear BSBI Facility Team,

I am Ali Mert Özdemir, a current M.Sc. Energy Management student at BSBI (June 2026 graduation), and I am writing with a specific proposal that I believe could benefit the BSBI campus directly.

**Short version:** I have built a Microsoft Fabric-native energy intelligence platform called EnergyLens, and I would like to offer BSBI a **free six-month pilot** — connecting your campus energy data to my live platform, giving your team real-time visibility into consumption, anomalies, CRREM compliance status, and HVAC efficiency. In return, I would ask only for your willingness to be a named case study reference once we have meaningful results.

**What EnergyLens does:**
- Real-time energy KPIs across one or many buildings (kWh, EUI, cost, CO₂)
- EU regulatory compliance tracking (CRREM 2030 stranding pathways, EnEfG, EPC scoring, CSRD-ready ESG reports)
- Anomaly detection with estimated euro cost impact ("HVAC overshoot last night cost approximately €47")
- HVAC and building envelope retrofit prioritization
- An AI Copilot that answers questions in natural language ("which BSBI building used the most energy last month?")

**What I need from BSBI for the pilot:**
1. Read-only access to campus energy meter data (15-minute interval kWh, ideally also gas/heating if metered)
2. Basic building information (floor area, year built, primary use)
3. One designated contact person for a 30-minute monthly check-in
4. Permission to use BSBI as a named case study once results are validated

**What you get in return:**
- Free six-month pilot, no hidden costs, no commitment
- A live multi-building dashboard your facility team can use daily
- A formal end-of-pilot report quantifying identified savings opportunities and compliance risks
- Direct contribution to a current BSBI M.Sc. capstone project (academic value)
- First customer slot at preferential pricing if you decide to continue beyond the pilot

**Why this is low-risk:**
- The platform already runs end-to-end with synthetic data from ten reference buildings — no development risk on the BSBI side
- All data stays in the Microsoft cloud with row-level security (your data, your access)
- I have built every layer of the platform solo, am Microsoft DP-600 certified, and have full M.Sc. supervisor support on the academic side

I have a short product demo video here: https://youtu.be/0IiqssHYtkY (3.5 minutes). Happy to share the executive summary, architecture document, or revenue model on request.

If this is of interest, I would love a 20-minute call to walk through the platform and discuss what BSBI data is feasible to connect. Could we find a time in the next two weeks?

Thank you for considering this. Looking forward to your reply.

Best regards,
Ali Mert Özdemir
M.Sc. Energy Management, BSBI Berlin
Microsoft DP-600 Certified
[YOUR_EMAIL] | LinkedIn: linkedin.com/in/alimertozdemir96
energylens.eu | github.com/alimertozdem
```

### Kişiselleştirme:

- `[İSİM]` → bulduğun yönetici ismi
- `[YOUR_EMAIL]` → alimertozdem@gmail.com
- Eğer BSBI'da sustainability/ESG raporu varsa (website'da ara) → ona kısa atıf: "I noticed BSBI's commitment to [X] in your sustainability section — EnergyLens directly supports tracking and reporting against these goals"

### Strateji:

- **Önce supervisor mailini gönder, 3-5 gün bekle**, hocadan yanıt geldikten sonra facility manager mailini gönderirken **"As discussed with Professor X, who is supervising this work..."** diye dropla. Bu BSBI içinde sosyal proof yaratır.
- Hocanın yanıtı gecikirse: 7 gün sonra facility manager mailini paralel gönder (daha fazla bekleme)

### Follow-up:

- **10 iş günü** içinde cevap yoksa: tek nazik dürtüş
- 20 gün+ yok: LinkedIn DM veya başka bir kontakttan tavsiye iste

---

## Gönderim sırası — net plan

| Gün | Aksiyon | Süre |
|---|---|---|
| **Yarın (2026-05-30)** | Supervisor mailini gönder (Salı sabah ideal) | 15 dk düzenleme + gönder |
| **+3 gün (2026-06-02)** | Hocadan yanıt gelmediyse: bekle, kontrol etme | — |
| **+5 gün (2026-06-04)** | Yanıt geldiyse: kısa teşekkür + Zoom önerisi | 10 dk |
| **+7 gün (2026-06-05)** | Yanıt yine yoksa: LinkedIn'de nazik DM | 5 dk |
| **+8 gün** | Hoca onayladıysa: Facility Manager mailini "as discussed with Prof. X" ile gönder | 15 dk |
| **Hoca onaylamadıysa** | Facility Manager mailini bağımsız gönder (paragraftan "supervisor" referansını çıkar) | 15 dk |

---

## Önemli notlar

- **Mailde "free pilot" kelimesi çok güçlü** — facility manager'lar bedava şeyleri sevmez (genelde "bedava = kalitesiz"). O yüzden mail'de "no cost, no commitment, fully managed by me" ile dengele.
- **"M.Sc. capstone" çerçevesi akademik açıdan koruyucu** — "öğrenci projesi" demek facility manager için risk düşürür (vendor lock yok).
- **BSBI içinde sosyal sermaye:** Supervisor → kabul → arkadaşına anlat → facility manager dolaylı duyar → mail geldiğinde "tanıdık" hisseder. Bu yüzden supervisor ÖNCE.
- **Şablonu birebir kopyala-yapıştır YAPMA** — 2-3 cümleyi senin kendi sesinde yeniden yaz. Otantiklik fark edilir.

---

*v1.0 — 2026-05-29 — Hocan LinkedIn'de olumlu yanıt verdi, fırsat açık*
