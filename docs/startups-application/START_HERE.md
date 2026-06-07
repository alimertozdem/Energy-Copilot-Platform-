# BURADAN BAŞLA — Microsoft Startups Submit'e Kadar Yol Haritası

**Hedef:** 1-2 gün içinde portal.startups.microsoft.com'a SUBMIT.
**Tahmini toplam süre:** ~5-6 saat (parça parça yayılabilir)

Bu dosya tek sayfa, kafanın karışmaması için. Detay lazım olduğunda ilgili rehbere atlarsın.

---

## 11 dosya neyse — sen bu sırayla kullanacaksın

```
HAZIRLIK    →   1. START_HERE.md (BU DOSYA — şimdi okuyorsun)
                2. VIDEO_CEKIM_REHBERI.md (video yapımı için adım-adım)

OKUMAK İÇİN →   3. 00_MASTER_PLAN.md (genel durum, isteğe bağlı)

VIDEO İÇİN  →   4. 08_founder_video_script.md (founder intro — okuyacağın script)
                5. 09_product_demo_script.md (product demo — okuyacağın script)

SUBMIT İÇİN →   6. 10_application_form_draft.md (form alanlarına kopyala-yapıştır)
                7. 03_pitch_deck.pptx (forma upload)
                8. 02_executive_summary.md (forma upload veya yapıştır)
                9. 04_architecture_document.md (forma upload — opsiyonel)
                10. 05_product_roadmap.md (forma upload — opsiyonel)
                11. 06_gtm_strategy.md (forma upload — opsiyonel)
                12. 07_revenue_model.xlsx (forma upload — opsiyonel)
                13. 01_founder_profile.md (referans)

TAKİP İÇİN  →   14. ACTION_CHECKLIST.md (tik atarken kullan)
```

---

## ADIM-ADIM AKIŞ (Sırayla)

### GÜN 1 — Hazırlık (toplam ~1 saat)

#### Adım 1 — Email forwarding (15 dk)
- Namecheap'e gir → Domain List → **energylens.eu** → Manage
- Sol menü → **Redirect Email**
- Add Forwarder: **alimert@** → **alimertozdem@gmail.com**
- Test et: Gmail'inden alimert@energylens.eu'ya mail at, 1-2 dk içinde inbox'a düşmeli

#### Adım 2 — Ücretsiz hesaplar (10 dk)
- **Loom** (loom.com) — ekran kaydı için. Google ile hızlı kayıt.
- **Descript** (descript.com) — ses + video edit için. Google ile hızlı kayıt.
- **ElevenLabs** (elevenlabs.io) — ATLA, kendi sesini kullanacaksın. Hesap açmana gerek yok.

#### Adım 3 — LinkedIn (5 dk)
- LinkedIn → Profil → Headline'ı şu yap: **"Building EnergyLens — Energy intelligence for commercial buildings | Microsoft DP-600"**
- About kısmına 1 paragraf EnergyLens tanıtımı ekle (örnek 02_executive_summary.md'nin ilk 2 paragrafı, kısalt)

#### Adım 4 — GitHub README (15 dk, isteğe bağlı)
- Repo README'ye 3 cümle Microsoft Fabric + AI Copilot vurgusu ekle
- Reviewer LinkedIn → GitHub'a bakabilir

---

### GÜN 1 SONU veya GÜN 2 — Video kayıtları (toplam ~3 saat)

#### Adım 5 — Founder intro video (90-105 saniye)
**Rehber:** `VIDEO_CEKIM_REHBERI.md` → "BÖLÜM A — Founder Intro Video"
**Script:** `08_founder_video_script.md`
**Çıktı:** Loom unlisted link

#### Adım 6 — Product demo video (4:15 dakika)
**Rehber:** `VIDEO_CEKIM_REHBERI.md` → "BÖLÜM B — Product Demo Video"
**Script:** `09_product_demo_script.md`
**Çıktı:** Loom unlisted link

> **NOT:** Video çekimden önce web app çalışır halde olmalı: `npm run dev` (frontend) + `uvicorn main:app --reload` (backend). Power BI Desktop'ta .pbix açık olmalı (Page 1, 6, 9 hazır — Page 8 atla).

---

### GÜN 2 SONU — SUBMIT (toplam ~45 dk)

#### Adım 7 — Form doldur
- **https://portal.startups.microsoft.com/** aç
- LinkedIn ile giriş yap (zorunlu)
- Her alanı `10_application_form_draft.md`'den kopyala-yapıştır
- Pitch deck (`03_pitch_deck.pptx`) upload
- Founder video Loom linkini yapıştır
- Product demo video Loom linkini yapıştır
- Executive summary (`02_executive_summary.md`) — form izin verirse upload, vermezse paste
- Diğer ek dosyalar (architecture, roadmap, GTM, revenue model) — form izin verirse upload

#### Adım 8 — SUBMIT
- Bütün alanları bir kez daha gözden geçir
- Boş alan yok mu?
- SUBMIT
- Confirmation email gelmesini bekle (24 saat içinde)

#### Adım 9 — Bekleme dönemi (3-14 gün)
- Microsoft incelemesi
- Bu sürede: Page 8 IoT polish, LinkedIn post (opsiyonel), BSBI pilot email

---

## SIKÇA SORULAN SORULAR

**S: Hangi dosyayı submit'te upload edicem?**
**C:** Zorunlu: pitch deck (`03_pitch_deck.pptx`). Form izin verirse: executive summary + architecture + roadmap + GTM + revenue model. Form izin vermezse sadece pitch deck yeter, diğerlerinin içeriği zaten 10'un içinde özetlenmiş.

**S: Video kayıtlarken ne kadar sürer?**
**C:** Founder intro (~1 saat): 15 dk slide hazırlık + 15 dk ses kayıt (3 take) + 30 dk Descript edit. Demo (~2 saat): 30 dk web app hazırlık + 30 dk screen recording + 60 dk edit + voiceover sync.

**S: Sesimi kaydettim ama beğenmedim, ne yapayım?**
**C:** Tekrar dene. Mikrofona 30 cm mesafe, sessiz oda, su iç. 2-3 takede iyi olur. Çok zor giderse AI voiceover'a (ElevenLabs) geçeriz — VIDEO_CEKIM_REHBERI'nde alternatif bölümü var.

**S: Page 8 IoT capacity sorunu submit'i etkiler mi?**
**C:** Hayır. Demo videoda atlanıyor, pitch deck'te slide 10'da "F4 throttle" zaten ASK gerekçen. Reviewer "F4 throttle, F8 gerek" mesajını alıyor — pitch'in artısı.

**S: AI Copilot Mock'ta çalışıyor, reviewer fark eder mi?**
**C:** Hayır. UI'da "Mock" yazısı yok, dönüşler template-driven ama Fabric SQL sorguları gerçek (gerçek rakamlar dönüyor). Demo'da hangi 3 soru kullanılacağı pre-test edilmiş, hiçbiri başarısız olmaz.

**S: Submit'ten sonra ne yapacağım?**
**C:** 3-14 gün bekle. Microsoft confirmation email + onay/red mailini gönderir. Onay gelirse Azure credits + Power BI Premium aktif olur. Bu sürede Page 8 IoT polish'e dön.

---

## NEREDEN YARDIM ALACAĞIM

- **Video çekim:** `VIDEO_CEKIM_REHBERI.md` — adım-adım, AI tools dahil
- **Script'ler:** `08_founder_video_script.md` (intro) + `09_product_demo_script.md` (demo)
- **Form içeriği:** `10_application_form_draft.md` — direkt kopyala
- **Tıkanırsan:** Bana mesaj at, hangi adımda olduğunu söyle, tek konuda detay veririm

---

**Şu an yapman gereken ilk şey:**

1. Bu dosyayı bir kez okudun ✅
2. `VIDEO_CEKIM_REHBERI.md`'yi aç → BÖLÜM A başlığını oku → Adım 1'e başla

Hadi.

---

*v1.0 — 2026-05-28*
