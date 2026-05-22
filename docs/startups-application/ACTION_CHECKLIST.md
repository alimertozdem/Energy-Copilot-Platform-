# Action Checklist — Sequential Tasks

**Bu liste sırayla işle. Her bir checkbox bir günlük iş bile değil (çoğu 30dk-2 saat).**

---

## FAZ 0 — ÖNCE: Raporu düzelt (capacity bekleniyor)

- [ ] Fabric capacity throttle recovery bekle (1-2 saat veya saat başı)
- [ ] SQL test: `SELECT COUNT(*) FROM gold_kpi_daily;` → hızlı dönüyorsa capacity OK
- [ ] Power BI Desktop açıp .pbix bağlantısını dene
- [ ] Page 1 görsellerini kontrol et — broken X'ler kaybolmalı
- [ ] Page 1 Scorecard EUI değerleri v5.1 (B002 ~251, B006 ~173) görünmeli
- [ ] Page 1 screenshot al → final hâl

---

## FAZ 1 — Senin yapacakların (1-2 saat toplam)

- [ ] **energylens.eu** domain al (namecheap.com veya hetzner.com, ~€15/yıl)
- [ ] LinkedIn headline güncelle → "Building EnergyLens — Energy intelligence for commercial buildings"
- [ ] LinkedIn About kısmında EnergyLens'i tanıt (1 paragraf)
- [ ] GitHub repo README'sini güzelleştir (Microsoft Fabric stack vurgusu)
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

## FAZ 3 — Claude'un hazırlayacağı 10 doküman

Claude paralelde hazırlayacak. Sıra önerisi (öncelikli olanı önce):

- [ ] 01 — **Founder Profile** (`01_founder_profile.md`)
- [ ] 02 — **Executive Summary** 1-pager (`02_executive_summary.md` + `.pdf`)
- [ ] 03 — **Pitch Deck** 10 slide (`03_pitch_deck.pptx`)
- [ ] 04 — **Architecture Document** (`04_architecture_document.md` + `.pdf`)
- [ ] 05 — **Product Roadmap** (`05_product_roadmap.md`)
- [ ] 06 — **GTM Strategy** (`06_gtm_strategy.md`)
- [ ] 07 — **Revenue Model** (`07_revenue_model.xlsx`)
- [ ] 08 — **Founder Video Script** (`08_founder_video_script.md`)
- [ ] 09 — **Product Demo Script** (`09_product_demo_script.md`)
- [ ] 10 — **Application Form Draft** (`10_application_form_draft.md`)

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

### Video B — Product Demo (3-5 dk)

- [ ] Power BI Desktop'ta dashboard'u tam ekran aç (Page 1-9)
- [ ] Loom ile screen recording başlat
- [ ] Sessiz olarak 9 sayfayı sırayla göster (script'e göre)
- [ ] Recording bitince kayıt indir
- [ ] ElevenLabs'ta script voiceover oluştur (English, professional voice)
- [ ] Descript veya CapCut'ta video + voiceover sync
- [ ] Background music ekle (pixabay.com/music)
- [ ] Final export → upload (Loom veya YouTube)
- [ ] Link kopyala

---

## FAZ 5 — Başvuru SUBMIT

- [ ] https://startups.microsoft.com adresinden başvuru formunu aç
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

**Last updated:** 2026-05-15
