# EXIST-Gründungsstipendium — Başvuru Planı (v2.0)

**Güncelleme:** 2026-06-13 — v1.0'ı (2026-05-29) supersede eder. Değişen: host/mentör gerçeği, doğru paket tutarı (~€45K solo), güncel app durumu, dürüstlük katmanı.
**Hedef:** EXIST-Gründungsstipendium, bir Berlin EXIST-ağı üniversitesi üzerinden.
**Paket (solo):** ~€45.000 / 12 ay.
**Başvuru:** Rolling — sabit deadline yok (fon dönemi 2027 sonu). Host belirlenince submit.
**Statü (2026-06-13):** Host arayışı fazı (Chelabi + Berlin ağlarına paralel outreach).

---

## 0. v1.0'dan beri NE DEĞİŞTİ

- ❌ ~€65K → ✅ **~€45K (solo):** stipend €30K + material **€10K (solo tavanı)** + coaching €5K. v1'deki €30K material aslında 3-kişilik EKİP tavanıymış.
- ❌ "BSBI Transfer Office host eder" → ✅ **BSBI EXIST ağında değil** (Berlin ağı = B!GRÜNDET; BSBI üye değil). Host, bir Berlin üniversitesinin startup ofisi olacak.
- ❌ "Chelabi resmî EXIST mentörü" → ✅ Mentör **host üniversiteden** olur; **Chelabi = akademik danışman / referans / tez bağı** (host izin verirse co-mentor).
- ✅ Solo'ya izin var (max 3 kişi) — doğrulandı.
- ✅ App Mayıs sonu–Haziran'da büyüdü (compliance hub, billing, audit, PDF, glossary, a11y, e2e, alerts).
- ✅ Dürüstlük katmanı (Reality-Gap dokümanı) eklendi.
- ✅ Batarya regülasyon numarası düzeltildi: **2023/1542**.

## 1. EXIST-Gründungsstipendium nedir (doğrulanmış)

Federal BMWE programı (ESF eş-finansman), üniversite/araştırma kurumu üzerinden yürür.

- **Stipend:** M.Sc. mezunu €2.500/ay × 12 = **€30.000** (vergisiz Stipendium).
- **Material:** solo **€10.000** (ekip 2+ için €30.000).
- **Coaching:** **€5.000**.
- **Süre:** 12 ay. **Ekip:** max 3 kişi; **solo'ya izin var.**
- **Çocuk eki:** çocuk başına €150/ay (varsa).
- **Solo toplam ≈ €45.000.**

**Eligibility (Mert):** M.Sc. (Haz 2026) · Almanya ikamet + kalma niyeti · innovation/knowledge-based ürün · DP-600 · çalışan prototip · diploma menşei önemli değil. **Açık kalan:** host kurum + host mentör.

## 2. Süreç (resmî, doğrulanmış)

1. **Host:** EXIST-ağı bir üniversite *başvuran taraftır*; Gründungsservice + mentor + çalışma alanı + ücretsiz altyapı sağlar.
2. **Mentor:** host kurumdan akademisyen; başvuruyu destekler.
3. **Paket:** startup ofisiyle birlikte idea sketch + CV + innovation + pazar/iş modeli + finansman + 12-ay plan.
4. **Submit:** kurum, **easy-Online** üzerinden **Projektträger Jülich (PtJ)**'ye gönderir. **Founder self-submit yapamaz.**
5. **Değerlendirme:** ~2-3 ay (innovation, founder yeterliliği, fizibilite).
6. **Onay → Stipendienvertrag**; ödeme **kuruma** (sana aktarılır).
7. **12 ay milestone:** erken coaching/roadmap · ~5. ay ara iş planı · ~10. ay final iş planı + Gründerpersönlichkeit semineri · hedef UG kuruluşu.

**Ön-kontrol:** EGS-Check (`exist.de/tools/exist-egs-check.html`, 2 dk).
**Referanslar:** Handbuch EGT (10.05.2026) + Richtlinie EGS (18.04.2023), exist.de.

## 3. Host stratejisi (PENDING — outreach sürüyor)

BSBI host olamadığı için bir Berlin EXIST-ağı üniversitesi host olacak. Dış founder kabul ediliyor (orada okumamış olsan bile); bir "üniversiteyle bağ" (örn. akademik iş birliği) gerekir.

| Öncelik | Host | Neden |
|---|---|---|
| 1 | **HWR Berlin — Startup Incubator Berlin** | Devlet üniversitesi, işletme odaklı, dış founder'a açık, solo-dostu sinyali |
| 2 | **Science & Startups** (FU/TU/HU/Charité) | EXIST'i fiilen yürütür; TU teknoloji açısı (not: ekibi tercih edebilir) |
| 3 | **ASH Berlin Start-up Center** | Ağ üyesi (yedek) |

Outreach metinleri: `EXIST_Network_Inquiry.md` (ağlar) + `EXIST_Host_Mentor_Request.md` (Chelabi).

## 4. Mentör (PENDING)

Resmî mentör host üniversiteden olur. Chelabi = akademik danışman + referans + tez bağı (host izin verirse co-mentor). Chelabi'ye "Berlin devlet üniv. bağın/önerin var mı?" diye sor — mentör bulma sürecinde merkezde kalsın.

## 5. Güncel app durumu (başvuruda "ne yapıldı")

Solo, uçtan uca (Nis–Haz 2026):

- **Fabric medallion** (Bronze→Silver→Gold), OneLake, ~57 tablo, tek-kaynaklı referans katmanı (emisyon faktörü/tarife).
- **9-sayfa Power BI raporu** (tüketim, bina, anomali, forecast, karar-destek, sürdürülebilirlik/GHG, HVAC, gerçek-zamanlı IoT, batarya ROI), DirectLake.
- **Web app** (Next.js + FastAPI + Postgres): 3-sağlayıcı auth, 3-katman erişim (RLS + modül + tier), **compliance hub** (MEPS/CRREM/EU Taxonomy/ESRS-E1 + flexibility), **billing (Stripe)**, **audit log**, **PDF export**, **glossary/tooltip**, alerts triyaj, a11y, e2e testleri, /demo · /copilot · /portfolio.
- **AI copilot** — 6 tool, SSE streaming, provider abstraction (Anthropic/Azure OpenAI/Mock).
- **IoT/AFDD** — ASHRAE Guideline 36 (12 kural, ~31 sensör, BACnet/Modbus/MQTT adaptörleri).
- **Gerçek dış veri** — Open-Meteo (hava), ENTSO-E (fiyat), ElectricityMaps (grid CO₂).
- 10 temsilî bina (DE/TR/AT/NL, ~3.5 yıl, ~693K veri noktası). **Müşteri/pilot yok** (BSBI kampüs pilotu görüşülüyor).

## 6. Dürüstlük katmanı (kredibilite kozu)

`EnergyLens_Reality_Gap_and_Data_Sourcing` — her sentetik/indikatif sayı için "şu an / gerçek standart / neye bağlanmalı". Akademisyene karşı en güçlü argüman: neyin gerçek olmadığını ve nasıl kapatılacağını tam bilmek.

- Metodoloji + dış veri **gerçek**; operasyonel bina verisi **sentetik** (pilot öncesi normal).
- Scope 1/2 izlenebilir; Scope 3 %8 screening (etiketli); market-based S2 mekanizma hazır (veri bekliyor); CRREM indikatif (Library Tem-2026); HVAC split modeled; batarya ROI üst-sınır; forecast MAPE in-sample.

## 7. Kabul şansını artıran kaldıraçlar

1. **Host + mentör çöz** (gating — bunsuz başvuru yok).
2. **İnovasyon/USP** — "sadece entegrasyon" itirazını kır: agentic AI (Lakehouse tool-use) + auditable carbon methodology (akademik IP, host ile yayınlanabilir).
3. **Pilot/LOI** — bir bina/niyet mektubu "realization" + pazar doğrulama puanını uçurur.
4. **Solo-risk nötrle** — mentör + danışmanlar + net ilk-hire planı (ekip = açık Q3 opsiyonu).
5. **Idea Sketch** — keskin, abartısız 3-5 sayfa (jüri ilk bunu okur).
6. **Gerçekçi finansal** — €45K doğru bütçe + validation-odaklı 12-ay milestone.

## 8. Bütçe (~€45.000 solo)

| Kategori | Tutar | Ne için |
|---|---|---|
| Stipend (yaşam) | €30.000 | 12 ay |
| Material — yazılım/bulut | €4.000 | Fabric, Power BI, LLM API, SaaS |
| Material — donanım | €2.500 | Laptop/monitör/mic |
| Material — müşteri kazanımı | €1.500 | Etkinlik, içerik |
| Material — hukuk/idari | €2.000 | UG kuruluş, IP, GDPR |
| Coaching | €5.000 | Mentor/sales/teknik koç |
| **Toplam** | **~€45.000** | Material ≤ €10.000 (solo tavanı) |

## 9. Sıradaki aksiyonlar

1. **Bugün:** EGS-Check (2 dk).
2. **Paralel outreach:** Chelabi maili + HWR Startup Incubator (+ Science & Startups). [metinler hazır]
3. **Host belli olunca:** mentör + "academic anchor" netleşir → başvuru paketi finalize, submit.
4. **Claude tarafı:** başvuru paketini (idea sketch + 12-ay plan + USP + €45K bütçe) güncel app + dürüstlük katmanıyla tazeler; sonra hoca brief'i + slides.

---
*v2.0 — 2026-06-13. v1.0 (2026-05-29) supersede edildi.*
