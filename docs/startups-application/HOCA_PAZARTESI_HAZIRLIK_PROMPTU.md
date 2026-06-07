# Pazartesi Hoca Toplantısı Hazırlık — Yeni Konuşma Promptu

**Yeni konuşma açtığında BU METNİ kopyala-yapıştır:**

---

Selam, EnergyLens platformu — Pazartesi (2026-06-01) BSBI'da Dr. Kaddour Chelabi ile yüz yüze görüşmem var, ona hazırlanmam lazım. Bu acil ve odaklı bir iş.

## Durum özeti

**Hocadan dönüş:** Dr. Chelabi LinkedIn'de "I will be honored" dedi (mentor olur), pazartesi BSBI'da yüz yüze görüşmemizi önerdi. Ben kabul ettim. Bu sefer **güvenini kazanmam** gerek çünkü:
- EXIST Gründerstipendium başvurusu için akademik mentor letter şart (~€65K paket, 12 ay tam zamanlı stipend)
- BSBI'nın kampüs enerji verisini pilot için almak ihtimal var
- Hoca güvenirse EXIST yolunu açıyor

**Benim sorunum:** Bu app'i 5 hafta gibi kısa sürede solo yaptım, ama domain detaylarını + her terimin anlamını + her hesaplamanın nedenini iyi bilmiyorum. CRREM, Scope 1/2/3, EUI, BACnet, EnEfG, DirectLake, Eventstream vs. — bunları hocaya net açıklayabilir düzeyde değilim. Pazartesi'ye kadar bu eksiği kapatmalıyım. Hoca bana "şu sayıyı niye böyle hesapladın?" sorarsa duraklamam.

**Bağlamı al — okunacak memory'ler (sırayla):**
- spaces/.../memory/MEMORY.md (tam liste, üstten oku)
- application_pivot_2026_05_29.md (DÜN: Microsoft submit edilemedi, EXIST'e pivot)
- frontend_architecture.md (web app + AI Copilot mimari)
- day_16_completion.md (Copilot detay)
- day_15_completion.md (/portfolio detay)
- founder_profile.md (Mert kim)
- brand_identity.md (EnergyLens marka)
- page3_completion.md, page4_completion.md, page5_completion.md, page6_completion.md, page7_extreme_showcase_plan.md, page8_revised_design.md, page9_v56_master.md (her dashboard sayfasının özet durumu)
- feedback_dax_patterns.md, feedback_pbi_embed.md, feedback_fabric_notebooks.md (teknik kararlar)
- phase2_production_architecture.md (IoT/EU compliance mimari)
- app_access_architecture.md (3-katman RLS + module + subscription)

**Bağlamı al — okunacak klasör yapısı:**

Proje klasörü: `C:\Energy Management App\Energy-copilot-platform`

İçinde aramaya başla:
- `docs/` — mimari, business logic, data model, sayfa-bazlı dokümanlar
- `docs/startups-application/` — pitch package (02-10 doc + pitch deck + BSBI/EXIST/EU dokümanlar)
- `web-app/backend/` — FastAPI + Postgres + 6 Copilot tool
- `web-app/frontend/` — Next.js 16 + 3 auth provider + /portfolio + /buildings + /copilot
- `pipelines/` veya `notebooks/` — Fabric notebooks (Bronze/Silver/Gold)
- DAX measure dokümanları (varsa)
- README.md

**Her şeyi oku — yüzeysel değil, derinlemesine.** App'in her özelliği, her tablo, her hesaplama, her teknik karar hakkında "nedir, niye, nasıl" üçlüsünü bilmen lazım. Bunu Mert için sonradan dilden anlatacaksın.

## Görev — 2 ana çıktı

### ÇIKTI 1: Master Reference Document (Mert'in öğrenme kitabı)

**Format:** Tek bir uzun markdown dosyası. Kitap gibi. Geniş, kapsamlı, açıklayıcı. Mert pazartesiye kadar 2 kez okuyup içselleştirecek.

**İçerik tablosu önerisi (sen genişletebilirsin):**

1. **EnergyLens nedir, ne yapar** (1 paragraf high-level + 1 paragraf detay)
2. **Domain temelleri** — Her bir terimin tanımı + neden önemli:
   - EUI (Energy Use Intensity) — formül, birim, mantık, EU 2030 hedefi
   - CRREM (Carbon Risk Real Estate Monitor) — nedir, pathway nasıl çalışır, stranding ne demek
   - Scope 1/2/3 emisyonlar — fark, örnek, EnergyLens'te nasıl hesaplanır
   - EPC (Energy Performance Certificate) — A-G skalası, ülkelere göre fark
   - EnEfG (Almanya), GEG, EU CSRD, EU 2023/1542 — her birinin kısa özeti, EnergyLens'in nasıl destek verdiği
   - HVAC + COP + boiler efficiency + envelope U-value — her bir kavram, hesap
   - Battery dispatch terimleri: Backup, Peak-Shaving, Self-Consumption, Time-of-Use, NPV, IRR, Payback
   - BACnet, Modbus, MQTT, OPC-UA — IoT protokolleri, niye birden fazla
   - DirectLake, SQL Analytics Endpoint, LLM tool use — 3 paralel Fabric veri yolu mantığı
3. **Mimari** — Bronze/Silver/Gold medallion, 57 Lakehouse tablosu, hangi katmanda hangi tablo, niye böyle
4. **9 Power BI sayfası — her birinin tam özeti:**
   - Sayfa adı
   - Hangi soruyu cevaplıyor (business question)
   - KPI'lar ve formülleri (DAX dahil)
   - Visual'lar ve ne gösteriyor
   - Hangi hedef kullanıcı için
   - Bilinen sorunlar (Page 1 monthly trend bug, Page 8 sensor uptime renk hatası gibi)
5. **Web app sayfaları:**
   - /portfolio, /buildings/[id], /copilot — her birinin amacı, mimarisi, niye böyle
6. **AI Copilot derin dive:**
   - 6 tool — query_kpi, compare_buildings, list_recommendations, get_anomalies, simulate_battery_scenario, update_action_status
   - LLM provider abstraction (Anthropic / Azure OpenAI / Mock)
   - SSE streaming, tool use loop, schema doğrulama
7. **Veri modeli:**
   - 10 representative bina (B001-B010) — her birinin özelliği, ülke, type, sample data mantığı
   - 3.5 yıl × 693K data point niye seçildi
8. **EU compliance — derinlik:**
   - CRREM pathway nasıl hesaplanır
   - Scope 1/2/3 ayrımı nasıl yapılır
   - Battery EU 2023/1542 compliance check mantığı
9. **EnergyLens'in pazardaki yeri:**
   - Rakipler (Measurabl, Aquicore, Cortexa, BuildingIQ, Honeywell Forge)
   - Niye Microsoft Fabric, niye mid-market, niye DACH
   - TAM/SAM/SOM
10. **EXIST için hocaya anlatılacak hikaye:**
   - Mert'in profili (DP-600 + M.Sc. + 5 hafta execution)
   - Niye solo bu kadarı yapabildi
   - Sonraki 12 ay'da ne yapacak (eğer EXIST'e onay gelirse)

**Yazım kuralları:**
- Türkçe yaz (Mert'in dili — sohbet dili)
- Teknik terimleri İngilizce bırak (EUI, CRREM vb. — App UI zaten İngilizce)
- Her teknik terim için bir cümle "ne demek bu" açıklaması
- Formüller varsa kod blok'ta yaz
- Mert hocaya bunu anlatacak gibi yaz — sade ama derin

### ÇIKTI 2: Pazartesi Sunum Paketi

**Format:** 2 alt dosya:

**A) HOCA_SUNUM_SCRIPTI.md**
- 20-30 dakikalık BSBI yüz yüze toplantı senaryosu
- Açılış (5 dk): kendini tanıt, neden geldin
- App tanıtımı (10 dk): canlı demo gibi anlat, hangi sayfayı niye göstereceksin
- EXIST açıklaması (5 dk): ne istiyorsun hocadan, takvim, mentor letter ne içerir
- Pilot teklif (5 dk): BSBI kampüs verisi için pilot teklif — risk yok, value var
- Soru-cevap hazırlığı (5 dk): hocanın muhtemel soruları + cevapları

**B) HOCA_DEMO_REHBERI.md**
- Pazartesi'ye laptop ile gidiyorsun
- Live demo yapacaksın (web app + AI Copilot)
- Hangi sayfayı hangi sırada açacaksın
- Hangi Copilot sorusunu soracaksın
- Hangi PBI sayfasını gösterceksin
- Backup: internet yoksa veya canlı çökerse ne yapacaksın (demo video YouTube'da hazır: https://youtu.be/0IiqssHYtkY)
- Ek olarak: hangi dosyaları printout taşımalı (executive summary 1 pager + pitch deck PDF?)

## Çalışma yöntemi — sıkı

1. **OKUMA FAZI** (en başta) — yukarıdaki memory + klasör dosyalarını oku. Bu en az 30-60 dk Read tool ile. Yüzeysel değil.
2. **PLAN SUN** — okuma bittikten sonra bana:
   - Master Reference Document için detaylı içerik tablosu (10 ana başlık altında alt başlıklar)
   - Pazartesi Sunum Paketi outline
   - Tahmini sayfa sayısı / kelime sayısı / saat
3. **ONAY AL** — ben onaylayana kadar yazma. Plan'da değişiklik istersem söyleyeceğim.
4. **PARÇA PARÇA YAZ** — onay sonrası, parça parça (bölüm bölüm), her birinde kısa update. Toptan dump yapma.
5. **PRESENT_FILES ile paylaş** — her dosya bitince present_files ile göster.

## KARARLAR (memory'de detay)

- UI dili İngilizce
- **Türkçe konuş** (sohbet)
- DOSYA DEĞİŞİKLİĞİ ONAY OLMADAN YAPMA
- Plan + onay + parça parça pattern (büyük dump'lar değil)
- BMAD methodology

## ZAMAN BASKISI

- Bugün: Cuma 2026-05-29 (akşam)
- Yarın: Cumartesi 2026-05-30
- Sonra: Pazar 2026-05-31
- **Toplantı: Pazartesi 2026-06-01 BSBI**

Yani yaklaşık **2.5 gün** var. Hocaya gitmeden Mert master document'i 2 kez okumalı, sunum scriptini ezberlemeli. Yani **Pazar akşamına kadar her şey biten** olmalı.

İLK İŞ — yeni konuşmaya başladığında:
1. Önce yukarıdaki memory'leri ve docs klasörlerini sırayla oku
2. Sonra bana "okudum, plan şu" diye gel
3. Onay alınca yazmaya başla

Hazır mısın?

---

**Not — Yukarıdaki promptu kopyala, yeni konuşmada başla. Bu konuşmada hazırlığa girmiyoruz, context çok yüklü, taze sayfa daha sağlıklı.**
