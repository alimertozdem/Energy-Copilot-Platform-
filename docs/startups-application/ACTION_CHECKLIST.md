# Action Checklist — Sequential Tasks

**Bu liste sırayla işle. Her bir checkbox bir günlük iş bile değil (çoğu 30dk-2 saat).**
**Güncel durum (2026-05-28):** Faz 0 + büyük çoğunluğu Faz 1 tamamlandı. Sıradaki kritik: Faz 2 video kayıtları + Faz 3 submit.

---

## FAZ 0 — Raporu düzelt (capacity bekleniyor) ✅ TAMAMLANDI

- [x] Fabric capacity throttle recovery bekle
- [x] SQL test: `SELECT COUNT(*) FROM gold_kpi_daily;` → çalıştı
- [x] Power BI Desktop açıp .pbix bağlantısını dene
- [x] Page 1-9 görsellerini kontrol et (Page 8 IoT post-Tier 2 polish için bekliyor)
- [x] Page 1 Scorecard EUI değerleri kontrol edildi
- [x] Page 1 screenshot al → final hâl

---

## FAZ 1 — Senin yapacakların ✅ ÇOĞU TAMAMLANDI

- [x] **energylens.eu** domain alındı
- [ ] LinkedIn headline güncelle → "Building EnergyLens — Energy intelligence for commercial buildings"
- [ ] LinkedIn About kısmında EnergyLens'i tanıt (1 paragraf)
- [ ] GitHub repo README'sini güzelleştir (Microsoft Fabric stack vurgusu — şu an web app + Copilot da var)
- [ ] **YENİ — Namecheap'te alimert@energylens.eu → alimertozdem@gmail.com forwarding kur (~15 dk)**
- [ ] ElevenLabs hesap aç (elevenlabs.io — free tier)
- [ ] Loom hesap aç (loom.com — free)
- [ ] Descript hesap aç (descript.com — free tier video edit için)

---

## FAZ 2 — Pilot outreach (paralel yürür, 30 dk yazma + bekleme)

- [ ] BSBI **facility/sustainability manager** araştır (LinkedIn / BSBI website)
- [ ] BSBI'a email yaz: "M.Sc. capstone için kampüsün enerji datasıyla çalışmak istiyorum"
  - Şablon Claude tarafından sağlanacak (ileride)
- [ ] M.Sc. **supervisor**'a email: "Energy platform geliştiriyorum, advisor letter ister miydiniz?"
- [ ] İzmir Yaşar mezun network'ünden 1-2 FM/property mgmt kişisi yaz LinkedIn

---

## FAZ 3 — Claude'un hazırladığı 10 doküman ✅ TAMAMLANDI

10 doküman v1.0 (2026-05-15) yazıldı, v1.1 (2026-05-28) ile Day 16 sonrası reality'e güncellendi.

- [x] 01 — **Founder Profile** (`01_founder_profile.md`) — v1.1
- [x] 02 — **Executive Summary** (`02_executive_summary.md`) — v1.1
- [x] 03 — **Pitch Deck** 10 slide (`03_pitch_deck.pptx`) — 4 slide güncellendi (5/8/9/10)
- [x] 04 — **Architecture Document** (`04_architecture_document.md`) — v1.1 + Section 2.6 AI Copilot Layer
- [x] 05 — **Product Roadmap** (`05_product_roadmap.md`) — v1.1
- [x] 06 — **GTM Strategy** (`06_gtm_strategy.md`) — v1.1
- [x] 07 — **Revenue Model** (`07_revenue_model.xlsx`) — sayılar hâlâ geçerli, dokunulmadı
- [x] 08 — **Founder Video Script** (`08_founder_video_script.md`) — v1.1 (execution proof line)
- [x] 09 — **Product Demo Script** (`09_product_demo_script.md`) — v2.0 (Web App + Copilot Forward)
- [x] 10 — **Application Form Draft** (`10_application_form_draft.md`) — v1.1

---

## FAZ 4 — Video kayıtları

### Video A — Founder Intro (sen, 90-120 sn)

- [ ] Sessiz oda hazırla, gün ışığı yüze, dağınık olmayan arka plan
- [ ] Telefon tripod üstünde, yatay tut
- [ ] Script ezberle (Claude'un hazırladığı 08_founder_video_script.md)
- [ ] 3-5 take çek, en iyisini seç
- [ ] Loom'a yükle veya YouTube unlisted
- [ ] Descript'te basit edit (umm/uhh temizle, subtitle ekle)
- [ ] Link kopyala — başvuru formunda kullanılacak

### Video B — Product Demo (3:30-4:15 — Web App + Copilot Forward, script v2.0)

- [ ] Web app: `npm run dev` (frontend) + `uvicorn main:app --reload` (backend) — ikisi de açık
- [ ] Power BI Desktop'ta .pbix tam ekran aç (Page 1, 6, 9 odak — Page 8 atla)
- [ ] Loom ile screen recording başlat
- [ ] Scene 1: Landing → sign-in (Microsoft butonu) → `/portfolio` (~30 sn)
- [ ] Scene 2: `/portfolio` KPI tile + buildings table (~45 sn)
- [ ] Scene 3: Bir bina seç → `/buildings/[id]` → embed içinde Page 1-2 (~30 sn)
- [ ] Scene 4 ★: `/copilot` — 3 hazır soru sırayla yaz (B001 enerji / B001 vs B005 / B005 battery scenarios) (~90 sn)
- [ ] Scene 5-6: Embed içinde Page 6 (CRREM) + Page 9 (Battery) (~50 sn)
- [ ] Scene 7: Outro card (~10 sn)
- [ ] Recording bitince kayıt indir
- [ ] ElevenLabs'ta script voiceover oluştur (English, "Adam" veya "Bella")
- [ ] Descript'te video + voiceover sync
- [ ] Background music ekle (Pixabay royalty-free, -20 dB)
- [ ] Final export 1080p MP4 → upload (Loom unlisted)
- [ ] Link kopyala

---

## FAZ 5 — Başvuru SUBMIT

- [ ] **https://portal.startups.microsoft.com/** adresinden başvuru formunu aç (doğru URL — eski foundershub.* değil)
- [ ] Claude'un hazırladığı `10_application_form_draft.md` dosyasından her alana kopyala-yapıştır
- [ ] Pitch deck upload
- [ ] Founder video link
- [ ] Product demo video link
- [ ] Executive summary upload
- [ ] Architecture document upload
- [ ] Review — boş alan kalmadı mı?
- [ ] SUBMIT
- [ ] Confirmation email gelmesini bekle

---

## FAZ 6 — Bekleme + paralel iş

- [ ] Microsoft cevabını bekle (3-14 gün)
- [ ] Bu sırada Page 2-9 dashboard review'u yap (rapor finalizasyonu)
- [ ] Pilot outreach takibi (gelen cevaplara hızlı yanıt ver)
- [ ] UG mini-GmbH kuruluşu için danışman bul (Berlin'de bol)

---

## FAZ 7 — Onay sonrası

- [ ] Azure credit aktifleştir
- [ ] Power BI Premium aktifleştir
- [ ] Mevcut Fabric workload'u yeni capacity'ye migrate et
- [ ] "Microsoft for Startups Member" rozetini LinkedIn'e ekle
- [ ] BSBI pilot başlat (gerçek data ile)
- [ ] Case study yaz (1-3 ay sonra)
- [ ] Tier 3 upgrade hazırla (6 ay sonra)

---

## ÖNEMLİ NOTLAR

- **Sıra esnek:** Domain almak için Claude'un docs'unu beklemen gerekmez. Paralel git.
- **Capacity recovery önce:** Rapor düzelmeden Startups dokümanlarına başlamayalım çünkü pitch deck/demo video için screenshot lazım.
- **Pilot acil değil:** BSBI pilot resmi 2-3 ay sonra başlasa bile başvuruda "in active discussion" diye yazılabilir.
- **Tier 2 hedef:** Tier 3 için 3-6 ay sonra upgrade. Şirket kurmak henüz şart değil.

---

**Last updated:** 2026-05-28 (v1.1 — Faz 0 + büyük çoğunluğu Faz 1 tamamlandı, Faz 3 dokümanlar v1.1'e güncellendi)
