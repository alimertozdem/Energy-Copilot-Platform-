# EnergyLens — Master Referans & Hoca Hazırlık Dokümanı

> **Kim için:** Ali Mert Özdemir — EnergyLens kurucusu
> **Ne için:** Dr. Kaddour Chelabi (BSBI) ile yüz yüze mentor görüşmesine hazırlık
> **Dil:** Açıklamalar Türkçe; teknik terimler İngilizce bırakıldı (uygulama UI'ı zaten İngilizce, hocayla muhtemelen İngilizce konuşacaksın). Her teknik terimin yanında bir cümlelik "bu ne demek" açıklaması var.
> **Tarih:** 2026-06-02 hazırlandı · Görüşme ~2026-06-08 (6 gün sonra)

---

## 0. Bu dokümanı nasıl kullanırsın

Bu doküman senin **öğrenme kitabın**. Amaç şu: hoca sana "bu sayıyı niye böyle hesapladın?", "Scope 2 location-based mı market-based mı?", "CRREM stranding'i nasıl buluyorsun?" diye sorduğunda **bir saniye bile duraklamadan** cevap verebilmen. Sen bu uygulamayı 5 haftada yaptın ama her terimin *neden* öyle olduğunu dilinden dökülecek kadar oturtmadın. Bu doküman tam o boşluğu kapatıyor.

Doküman 12 bölüm. Her teknik kavramı **üç soruyla** anlatıyorum:

1. **Nedir?** — terimin bir cümlelik tanımı
2. **Neden önemli?** — hocayı/müşteriyi neden ilgilendiriyor
3. **Nasıl hesaplanıyor?** — EnergyLens'te formül veya mantık

Bir de her dashboard sayfasının ve uygulamadaki her özelliğin "ne sorusunu cevaplıyor" mantığını veriyorum. **Bölüm 9 (Dürüstlük Katmanı)** en kritik bölüm: orada hangi sayıları güvenle savunabileceğini, hangilerini "şu an indikatif, roadmap'te şöyle güçlendireceğim" diye dürüstçe çerçeveleyeceğini öğreneceksin. Bir enerji akademisyeni zayıf noktayı dakikalar içinde bulur; o yüzden zayıf noktaları **önce sen** bil ve dürüst çerçeveni hazır tut. Dürüstlük, bir akademisyenin gözünde güvenilirliğin ta kendisidir.

### 6 günlük okuma planı

Elinde 6 gün var. Bunu israf etme — ama panik de yapma. Önerilen tempo:

| Gün | Ne yap | Hedef |
|---|---|---|
| **Gün 1** | Bölüm 1–2 (EnergyLens 360° + Domain temelleri) oku. Formülleri yüksek sesle tekrar et. | EUI, Scope 1/2/3, COP, CRREM, EPC'yi kendi cümlelerinle anlatabil |
| **Gün 2** | Bölüm 3–4 (Mimari + 9 PBI sayfası) oku. | Medallion'ı çiz, her sayfanın hangi soruyu cevapladığını söyle |
| **Gün 3** | Bölüm 5–6 (Web app + AI Copilot) + Bölüm 8 (EU compliance derinlik) oku. | 6 Copilot tool'unu ve "tool use vs text summary" farkını anlat |
| **Gün 4** | **Bölüm 9 (Dürüstlük katmanı) — iki kez oku.** Bölüm 7 (veri modeli). | Her bilinen sınır için 1 cümlelik dürüst çerçeveni ezberle |
| **Gün 5** | Bölüm 10–11 (Pazar + EXIST) + Bölüm 12 (Hocanın 20 sorusu). Sesli prova: showcase Word dosyasını baştan sona anlat. | Demoyu akıcı sun, EXIST talebini net söyle |
| **Gün 6** | Hafif tekrar. Showcase Word dosyasını + demo rehberini gözden geçir. Laptop + backup video hazır. | Sakin, hazır, kendine güvenen |

**Altın kural:** Bir şeyi ezberlemek yetmez — *neden* öyle olduğunu bil. Hoca "neden 5% discount rate?" diye sorarsa "çünkü ticari gayrimenkul için tipik reel iskonto oranı ve muhafazakâr tarafta kalıyor" diyebilmelisin, "çünkü öyle yazmışım" değil.

---

## 1. EnergyLens nedir, ne yapar

### Yüksek seviye (hocaya ilk söyleyeceğin paragraf)

EnergyLens, ticari binalar için **Microsoft Fabric üzerine kurulu bir enerji zekâsı ve karar-destek platformu**. Bir bina portföyünün enerji verisini (sayaç, fatura, IoT sensörü, hava durumu, solar, batarya) tek bir canlı sisteme topluyor; bu veriyi medallion mimarisiyle (Bronze→Silver→Gold) işliyor; ve üç katman halinde sunuyor: (1) 9 sayfalık bir Power BI analitik raporu, (2) Next.js + FastAPI tabanlı bir web uygulaması, (3) Lakehouse üzerinde *tool use* ile doğal dilde soru cevaplayan bir AI Copilot. Üstüne, AB regülasyonlarına (CRREM, EnEfG, GEG, CSRD/ESRS E1, EU Battery Regulation 2023/1542) karşı uyumluluk skorlaması ekliyor.

### Tek cümlelik konumlandırma

> "Ticari bina portföylerinin ham enerji verisini, Microsoft Fabric üzerinde **denetlenebilir** KPI'lara, AB-uyumlu sürdürülebilirlik raporlamasına ve AI destekli önerilere dönüştüren mid-market bir SaaS platformu."

### Teknik seviye (biraz derine inince)

Mimari, **tier-aware** (kademeye duyarlı): Tier 1 binalar saatlik fatura/sayaç verisiyle batch işlenir; Tier 2/3 binalar IoT sensörleriyle gerçek-zamanlıya yakın işlenir. Veri katmanı **OneLake** üzerinde Delta Lake formatında duruyor; Power BI buna **DirectLake mode** ile bağlanıyor (import yok, DirectQuery gecikmesi yok). Web uygulaması Fabric'e **üç paralel yoldan** erişiyor: (1) Power BI embed (DirectLake), (2) custom React sayfaları SQL Analytics Endpoint üzerinden (pyodbc/ODBC), (3) AI Copilot backend dispatcher üzerinden LLM tool use. Erişim kontrolü **üç katmanlı**: Power BI Row-Level Security (hangi binayı görür), web app navigation (hangi modül açık), subscription tier (hangi özellik aktif).

### İlk 2 dakika — hocaya asansör konuşması (İngilizce söyleyeceğin versiyon)

> "EnergyLens is a Microsoft Fabric-native energy intelligence platform for commercial buildings. It unifies energy data from multiple buildings — meters, bills, IoT sensors, weather, solar, battery — into a medallion data architecture, and surfaces it through a 9-page Power BI report, a web application, and an AI Copilot that answers natural-language questions over the Lakehouse using tool use. On top of that, it scores each building against EU regulations — CRREM decarbonization pathways, EnEfG, the building energy act GEG, and CSRD/ESRS E1 sustainability reporting. I built the whole stack solo in about five weeks, end to end, while finishing my M.Sc. here at BSBI. I'm Microsoft DP-600 certified, which is the Fabric analytics engineering certification."

### Hocanın sende görmek istediği şey (kendine hatırlat)

Hoca seni LinkedIn'de "I will be honored" diyerek mentor olmaya çağırdı — yani kapı zaten açık. Bu görüşmede yapman gereken **satış değil, güven inşası**. Hoca bir akademisyen; onu etkileyen şey parlak slaytlar değil, **kavramsal derinlik ve dürüstlük**. Üç şeyi göstermen yeter:

1. **Domain hâkimiyeti** — enerji mühendisliği kavramlarını (EUI, COP, U-value, HDD/CDD) ve AB regülasyonlarını gerçekten anladığını
2. **Dürüst öz-değerlendirme** — neyin sağlam, neyin daha geliştirilecek (indikatif/roadmap) olduğunu açıkça söyleyebildiğini; bu akademik dürüstlüktür ve hoca bunu ödüllendirir
3. **Yürütme kapasitesi** — 5 haftada tek başına production-grade bir stack çıkardığını

Bunları gösterirsen mentor letter (EXIST için zorunlu) ve muhtemelen BSBI kampüs pilotu gelir.
---

## 2. Domain temelleri — her terim: nedir / neden / nasıl

Bu bölüm dokümanın kalbi. Hoca burada anlattığın her terimi gerçekten anladığını görmek isteyecek. Formülleri ezberle ama daha önemlisi **mantığını** kavra.

### 2.1 EUI — Energy Use Intensity (enerji yoğunluğu)

**Nedir?** Bir binanın birim alan başına ne kadar enerji tükettiği. Binaların enerji verimliliğini karşılaştırmanın temel metriği. (EnPI = Energy Performance Indicator, ISO 50001'in aynı kavrama verdiği isim.)

**Neden önemli?** İki binayı "kaç kWh tüketti" diye karşılaştıramazsın — büyük bina doğal olarak çok tüketir. m²'ye bölünce *verimlilik* karşılaştırılabilir hale gelir. EPC sertifikaları, AB hedefleri, benchmark'lar hep bu metrik üzerinden konuşur.

**Nasıl hesaplanıyor?**
```
EUI = Yıllık toplam tüketim (kWh) / Şartlandırılmış alan (m²)
Birim: kWh/m²/yıl

İklim-düzeltilmiş EUI (climate-adjusted):
EUI_adj = EUI × (Referans HDD+CDD / Gerçek HDD+CDD)
```

**İklim düzeltmesi neden?** Berlin'deki bir bina, İstanbul'daki *aynı verimlilikteki* binadan daha çok ısıtma enerjisi harcar — çünkü hava daha soğuk. Adil karşılaştırma için tüketimi **derece-güne** (degree days) göre normalize edersin.

- **HDD (Heating Degree Days):** Günlük ortalama sıcaklık 15°C'nin altına düştüğü her derece için biriken ısıtma ihtiyacı. `HDD = Σ max(0, 15 − T_gün)`
- **CDD (Cooling Degree Days):** 22°C'nin üstü için soğutma ihtiyacı. `CDD = Σ max(0, T_gün − 22)`
- Baz sıcaklıklar **EN ISO 15927-6** standardından (HDD 15°C, CDD 22°C).

> **Hoca sorabilir:** "İklim düzeltmesinde CDD'yi de katıyor musun yoksa sadece HDD mi?" — **Cevap:** Başta sadece HDD'ye bölüyordum (bu bir hataydı, soğutma-ağırlıklı binaları yanlış normalize ediyordu); refactor'da **ratio metoda** geçtim, referans HDD+CDD baseline'ı ile, hem ısıtma hem soğutmayı katarak. Doğru EnPI normalizasyonu budur. *(Bu dürüstlük — düzelttiğin bir şeyi anlatmak güven verir.)*

**Office benchmark'ları:**
| Sınıf | EUI (kWh/m²/yıl) |
|---|---|
| Excellent | < 80 |
| Good | 80–130 |
| Average | 130–200 |
| Poor | > 200 |

Hotel, Retail, Logistics, Hospital için ayrı benchmark setleri var (ör. veri merkezi/hastane çok daha yüksek normaldir).

### 2.2 Peak Demand, Load Factor, Base Load (güç profili)

**Peak Demand (tepe talep) — Nedir?** Dönem içindeki en yüksek anlık güç çekişi (kW). **Neden önemli?** Ticari elektrik faturalarında en büyük kalemlerden biri "demand charge" — yani aylık en yüksek 15-dakikalık ortalama kW üzerinden alınan kapasite ücreti. Sabah 10:00'daki tek bir tepe, tüm ayın faturasını belirler.
```
Peak_Demand_kW = MAX(demand_kw)
Batarya varsa: Peak_Shaved_kW = Peak_bataryasız − Peak_bataryalı
Demand Charge Tasarrufu = Peak_Shaved_kW × demand_charge (€/kW/ay)
```

**Load Factor (yük faktörü) — Nedir?** Ortalama talebin tepe talebe oranı (0–1). **Neden önemli?** Tüketimin ne kadar "düz" olduğunu ölçer. 1.0 = mükemmel düz (ideal); 0.3 = çok dikenli (tarife mahkumu, ekipman kısa-döngü yapıyor). Office hedefi > 0.70.
```
Load_Factor = Ortalama_Talep_kW / Peak_Talep_kW
```

**Base Load (taban yük / uyku tüketimi) — Nedir?** Bina boşken (gece 02:00–04:00) çektiği minimum güç. **Neden önemli?** Gece bina "uyumalı". Hâlâ tepenin %35'inden fazla çekiyorsa bir şey kapanmıyor — server, aydınlatma, HVAC zamanlaması, ısrarlı standby cihazlar. Net €kayıp.
```
Base_Load_kW = MIN(demand_kw), 02:00–04:00 yerel saat
Alarm: Base_Load / Peak_Demand > 0.35
```

### 2.3 Solar KPI'ları (has_pv = True olan binalar)

**Self-Consumption Rate vs Self-Sufficiency Rate — müşterilerin sürekli karıştırdığı ayrım:**
- **Self-Consumption Rate:** "Ürettiğim solar'ın yüzde kaçını kendim kullandım?" (şebekeye satmak yerine) → `self_consumed / generated`. Hedef > %70.
- **Self-Sufficiency Rate:** "Toplam ihtiyacımın yüzde kaçını kendi solar'ımdan karşıladım?" (şebekeden almak yerine) → `self_consumed / total_consumption`. Tipik %20–60.

**Solar Yield (verim):** `generated_kwh / pv_capacity_kwp`. Almanya 900–1050 kWh/kWp/yıl; Türkiye 1300–1600 (daha güneşli).

**Performance Ratio (PR) — Nedir?** Gerçek verimin teorik verime oranı. Sistemin "sağlıklı mı" olduğunu söyler.
```
PR = gerçek_verim / teorik_verim
teorik_verim = irradiance_kwh_m² × pv_capacity_kwp × 0.80
Hedef PR > 0.75 — düşükse: panel kirlenmesi, gölgeleme, inverter arızası
```

### 2.4 Battery KPI'ları + Dispatch stratejileri

**Round-Trip Efficiency (gidiş-dönüş verimi):** `deşarj_kwh / şarj_kwh`. LFP lityum için hedef > 0.90. Bataryaya koyduğun enerjinin ne kadarını geri alabildiğin.

**SoC (State of Charge):** Şarj seviyesi %0–100. **Önerilen bant 20%–80%.** *Neden?* Bandın altına inince hücre kimyası bozulur, üstüne çıkınca elektrot stres yer — ikisi de batarya ömrünü kısaltır. (Çalışma bandı 15%–90% zorunlu, 20%–80% optimal.)

**Cycle count:** `şarj_kwh / kapasite_kwh` — günlük tam-eşdeğer döngü sayısı. Ömür tahmini = toplam_döngü / garantili_döngü (LFP ~4.000 döngü).

**Dispatch stratejileri (bataryayı ne zaman şarj/deşarj edeceğine karar veren mantık):**
- **Self-Consumption Mode:** Solar fazlası varsa şarj et, tüketim solar'ı aşınca deşarj et. Hedef: self-consumption'ı maksimize et.
- **Peak Shaving Mode:** Talep bir eşiği (ör. son 12 ayın 90. persentili) aşınca deşarj ederek tepeyi tıraşla. Hedef: demand charge'ı düşür.
- **Diğerleri (Page 9'da karşılaştırılıyor):** arbitrage (ucuz saatte şarj/pahalı saatte deşarj), time-of-use, self-consumption, frequency regulation, demand response, hybrid.

### 2.5 Heat Pump COP/SCOP + Boiler Efficiency

**COP (Coefficient of Performance) — Nedir?** Isı pompasının ürettiği ısı enerjisinin, harcadığı elektriğe oranı. COP=4 demek: 1 kWh elektrikle 4 kWh ısı. **Neden önemli?** Isı pompasının kalbi; düşerse hem para hem konfor kaybı.
```
COP = Üretilen_ısı_kWh / Tüketilen_elektrik_kWh
SCOP (Seasonal COP) = Sezon_toplam_ısı / Sezon_toplam_elektrik
COP_Performance_Ratio = COP_gerçek / COP_rated
  < 0.80 → MEDIUM bakım alarmı
  < 0.60 → HIGH kritik arıza alarmı
```
> **Kritik nüans (hoca enerji mühendisi — bunu mutlaka bil):** COP soğuk havada *doğal olarak* düşer. Alarmı yorumlamadan önce "mevsim mi değişti?" diye bak. EnergyLens kodu COP'u **eşdeğer dış-sıcaklık bandında** karşılaştırır, böylece kış düşüşünü arıza sanmaz.

**Boiler efficiency (kazan verimi):** Gaz kazanı baseline'ı 0.90 alınır (yani gazın %90'ı ısıya döner). Isı pompası simülasyonunda mevcut gaz maliyetini bununla hesaplarsın: `gaz_maliyeti = ısı_kWh / 0.90 × gaz_fiyatı`.

### 2.6 Bina kabuğu: U-value, WWR, air-tightness

**U-value (ısı geçirgenlik katsayısı) — Nedir?** Bir bina elemanından (duvar, çatı, pencere) ne kadar ısı kaçtığı. Birim W/m²K. **Düşük = iyi** (daha iyi yalıtım). GEG (Almanya) minimumları: duvar ≤ 0.24, çatı ≤ 0.20, pencere ≤ 1.30 W/m²K.

**WWR (Window-to-Wall Ratio):** Pencere alanı / dış duvar alanı. Hem ısı kaybını hem gün ışığını etkiler.

**Air-tightness (ACH — Air Changes per Hour):** Binanın saatte kaç kez havasının sızıntıyla değiştiği. Yüksek = kontrolsüz ısı kaybı.

**Isı kaybı / yalıtım iyileştirme tasarrufu:**
```
Q_tasarruf = ΔU × yüzey_alanı × HDD × 24 / 1000
ΔU = mevcut_u_value − hedef_u_value
```
> A7 anomalisi (insulation degradation): iklim-düzeltilmiş EUI bir önceki yıla göre >%15 arttıysa ve hava + HVAC değişmediyse → yalıtım bozulmuş olabilir. Önerilen aksiyon: **Blower Door Test** (EN 13829 / ISO 9972).

### 2.7 Karbon & Maliyet

**Emission factor (emisyon faktörü) — Nedir?** Bir kWh elektriğin şebekeden gelirken ne kadar CO₂ saldığı (kg CO₂/kWh). Ülkenin elektrik üretim karışımına bağlı.
```
CO2_tüketim_kg = tüketim_kwh × emission_factor
CO2_kaçınılan_kg = solar_üretim_kwh × emission_factor  (solar ürettiği için şebekeden ÇEKİLMEYEN elektrik)
CO2_net_kg = CO2_tüketim − CO2_kaçınılan
Carbon_Intensity = CO2_net / alan_m²  (kg CO₂/m²/yıl)
```

**EnergyLens'in kanonik grid faktörleri (refactor sonrası, kaynaklı + yıl-indeksli):**
- **Almanya:** UBA (Umweltbundesamt) serisi — 2022 = 0.433, 2023 = 0.386, 2024 = 0.363 kg CO₂/kWh (şebeke yıldan yıla temizleniyor)
- **Türkiye:** **0.442 kg CO₂/kWh** (TEİAŞ) — tek kanonik değer
- Diğer ülkeler IEA placeholder olarak işaretli

> **Bunu mutlaka bil:** Daha önce bu faktör 4 farklı dosyada 0.430/0.442/0.450 olarak çelişiyordu (denetimde yakalandı). Refactor'da **tek referans tablosu** (`ref_grid_emission_factors`, kaynak + URL + yıl ile) kurdum; artık her motor oradan okuyor. Bu, "her disclosed kg CO₂ tek bir kaynağa kadar izlenebilir" (regulator-grade lineage) iddiasının temeli.

**EU ETS (Emissions Trading System) & carbon credit:** AB karbon piyasası; 2024'te ~€60–80/ton CO₂. `carbon_credit_değeri = co2_kaçınılan_kg / 1000 × ETS_fiyatı`.

**Maliyet:**
```
Enerji_Maliyeti = (şebeke_alım × elektrik_fiyatı)
                + (peak_demand × demand_charge)
                − (şebeke_satış × feed-in tarife)
```
Kanonik tarifeler: DE ≈ 0.226 €/kWh (Eurostat non-household), gaz CO₂ 0.201 kg/kWh (DEFRA, tek baz).

### 2.8 Scope 1 / 2 / 3 emisyonları

**Nedir?** GHG Protocol'ün (sera gazı muhasebe metodolojisi) emisyonları üç kovaya ayırması:
- **Scope 1 — Doğrudan:** Senin sahip olduğun/kontrol ettiğin kaynaklardan. Örnek: gaz kazanı, şirket araçları, **soğutucu gaz kaçakları** (HVAC).
- **Scope 2 — Satın alınan enerjiden dolaylı:** Şebekeden aldığın elektrik/ısı/buhar. **İki yöntemle raporlanır:**
  - *Location-based:* ülke şebeke ortalaması emisyon faktörü
  - *Market-based:* tedarikçine özgü faktör (yeşil sertifika vb.)
- **Scope 3 — Diğer tüm dolaylı:** Değer zincirindeki her şey. 15 kategori. Binalar için en önemlileri: Kategori 13 (downstream leased assets — kiraya verilen alanlar), Kategori 1 (satın alınan mal/hizmet, gömülü karbon).

**Neden önemli?** ESRS E1-6 (AB iklim açıklaması) Scope 1, 2, 3'ü **ayrı ayrı**, Scope 2'yi de **hem location- hem market-based** ister. Çoğu şirket market-based'i unutur ve denetimde takılır.

> **Hoca sorabilir:** "Scope 3'ü nasıl hesaplıyorsun?" — **Dürüst cevap:** Şu an Scope 3'ü `(Scope1+Scope2)×%8` ile bir *screening tahmini* olarak veriyorum ve çıktıda `scope3_disclosure_grade = False` diye açıkça etiketliyorum — yani "disclosure-ready değil, gösterge". Gerçek binalarda Scope 3 (özellikle Kat. 13) çoğu zaman en büyük kovadır; o yüzden roadmap'te kategori-bazlı aktivite verisiyle modellemek var. (Bunu Bölüm 9'da detaylı çerçeveliyorum — sakın "ESRS-ready Scope 3" deme.)

### 2.9 EPC + ESG Composite Score

**EPC (Energy Performance Certificate) — Nedir?** Binanın A+→G arası ulusal enerji performans notu (kWh/m²/yıl bazlı). AB'de satış/kiralama anında zorunlu. Her ülkenin metodolojisi farklı (Almanya'da DENA).

> **Önemli — area-weighting (alan-ağırlıklı):** Portföy EPC skorunu "binaların ortalaması" diye hesaplamak bir **denetim hatasıdır** — çünkü 50 m²'lik bina ile 50.000 m²'lik bina eşit ağırlık almamalı. Doğrusu **zemin-alanına göre ağırlıklamak.** EnergyLens başta düz AVERAGE yapıyordu (denetimde yakalandı); v57 DAX'ta `DIVIDE(SUMX(alan×skor), SUMX(alan))` ile gerçekten area-weighted yaptım.

**ESG Composite Score (0–100):** Platformun kendi bileşik skoru:
```
%40 — EUI vs sektör benchmark
%30 — CO₂ yoğunluğu vs ülke ortalaması
%20 — Yenilenebilir pay (solar self-sufficiency)
%10 — Uyumluluk durumu
```

### 2.10 CRREM — Carbon Risk Real Estate Monitor

**Nedir?** Gayrimenkulün karbon yoğunluğunu, bilimsel bir **dekarbonizasyon patikasıyla** (1.5°C / 2°C uyumlu, yıldan yıla düşen kg CO₂/m²/yıl eğrisi) karşılaştıran bir araç. Bina bu eğriyi hangi yıl aşacaksa, o yıl **"stranded" (sıkışmış/atıl varlık)** olur — yani regülasyonel/piyasa açısından değerini kaybetme riski.

**Neden önemli?** REIT'ler, varlık yöneticileri için kritik: hangi binalar portföyü "stranding" riskine sokuyor? CRREM'in ücretsiz Excel aracı **1 Temmuz 2026'da emekliye ayrılıyor** — yani zamanlaman iyi.

**Nasıl?** `carbonIntensity = (CO₂_30g × 365.25/30) / alan` hesaplanır, tip+bölge bazlı pathway eğrisiyle karşılaştırılır; kesişim yılı = stranding yılı.

> **Dürüst sınır:** EnergyLens'teki CRREM pathway'leri şu an **indikatif** (temsili 1.5°C anchor'ları), resmî CRREM v2 tool verisi değil. Sebep: resmî eğrileri ticari yazılıma *gömmek* CRREM License Partner anlaşması ister. Tek modülde (`PATHWAY_ANCHORS`) swappable yaptım — License Partner olunca resmî değerler tek dosyada değişir. Müşteriye/hocaya "indicative pathway" de.

### 2.11 Regülasyonlar (her birinin kısa özeti + EnergyLens nasıl destek veriyor)

- **CSRD (Corporate Sustainability Reporting Directive):** AB sürdürülebilirlik raporlama yasası; ESRS standartlarını kullanır. **2026 Omnibus ile kapsam daraldı** (>1000 çalışan & €450M ⇒ çok daha az şirket; ESRS E1 veri noktaları −%61). → Bu yüzden EnergyLens'i **"report-ready / ESRS-E1-aligned reporting support"** diye konumlandır, **"herkese zorunlu" veya "CSRD-compliant garantisi" DEME** (anti-greenwashing).
- **ESRS E1 (Climate Change):** 12 ESRS standardından en önemlisi; 9 açıklama gereksinimi (E1-1 → E1-9). EnergyLens eşlemesi: E1-5 enerji karışımı (Sayfa 1–3), E1-6 Scope 1/2/3 GHG (Sayfa 6), E1-1 geçiş planı (Sayfa 4–5), E1-9 finansal etkiler (Sayfa 9).
- **EnEfG (Almanya Enerji Verimliliği Yasası):** ≥250 çalışanlı organizasyonlar için ISO 50001 veya denetim zorunlu. EnergyLens `employee_count` + `iso50001_certified` ile kontrol eder.
- **GEG (Gebäudeenergiegesetz — Almanya Bina Enerji Yasası):** 2024+ HVAC değişimlerinde ≥%65 yenilenebilir zorunlu (§71); minimum U-value'lar. EnergyLens ısı pompası önerisini buna bağlar (ısı pompası %65'i otomatik karşılar).
- **EEG (Erneuerbare-Energien-Gesetz):** PV şebeke ihracı için feed-in tarife oranları (~€0.08/kWh, 2024).
- **EPBD (Energy Performance of Buildings Directive):** AB bina direktifi; **recast 2024/1275** — ulusal ticari MEPS 2027; en kötü %16 → 2030, %26 → 2033; yeni binalar zero-emission 2030. EnergyLens'in /compliance MEPS radarı tam buna bağlı.
- **EU 2023/1542 (Battery Regulation):** Ocak 2024+ AB'de satılan bataryalar için karbon ayak izi etiketi, geri-dönüştürülmüş içerik, garanti döngüleri, State of Health zorunlu. EnergyLens Page 9 sadece EU-compliant bataryaları senaryoya alır.
- **BEP-TR (Türkiye Binalarda Enerji Performansı):** EPC zorunlu, 10 yılda bir yenileme.

### 2.12 IoT protokolleri — neden birden fazla?

**Sorun:** Ticari binalardaki Building Management System (BMS) tek bir dil konuşmuyor. Bina otomasyonu pazarı parçalı. Tek protokol desteklersen yarı pazarı kaybedersin. O yüzden **protocol adapter pattern** (her protokol için bir adaptör sınıfı, hepsi standart birime normalize eder: °C, %, ppm, kW, kWh).

- **BACnet/IP (ASHRAE 135):** Almanya BMS standardı. P0 öncelik.
- **Modbus TCP (IEC 61158):** AB'de çok yaygın, endüstriyel. P0 öncelik.
- **MQTT 5.0 (ISO/IEC 20922):** Hafif pub/sub IoT mesajlaşma; ölçeklenebilir, yükselen. P1.
- **REST API (HTTP/JSON):** Her şeyi yakalayan genel yol. P1.
- **OPC-UA (IEC 62541):** Premium endüstriyel otomasyon. P2 (Faz 2.5).

> Page 8 araştırmasında 2026 sektör standardına bakıldı: Brick Schema + Project Haystack + **ASHRAE 223P** semantik katmanlar, 9+ protokol, ~31 sensör tipi, **ASHRAE Guideline 36** AFDD (Automated Fault Detection & Diagnostics). Bu, app'in en güçlü, en sektör-grade tarafı.

### 2.13 Microsoft Fabric kavramları (hocaya "DP-600 mindset" göster)

- **OneLake:** Tüm organizasyon için tek mantıksal veri gölü. Her workload aynı veri katmanını okur/yazar — veriyi sistemler arası kopyalamayı bitirir. (Fabric'in "büyük olayı".)
- **Lakehouse:** Veri gölü esnekliği + warehouse yapısını birleştiren depolama. Fabric'te Delta Lake formatında OneLake üstünde.
- **Medallion mimarisi:** Bronze (ham) → Silver (temizlenmiş, normalize) → Gold (iş-hazır, KPI). Her katman bir öncekinin üstüne kurulur; lineage (köken izlenebilirliği) buradan gelir.
- **DirectLake mode:** Power BI'ın OneLake'teki Parquet dosyalarını *doğrudan* okuması — import yok, DirectQuery yok. Import hızında + gerçek-zaman tazeliğinde. Fabric'in başlık özelliği.
- **DirectQuery vs Import (karşılaştırma):** Import = hızlı ama bayat (refresh gerekir); DirectQuery = canlı ama yavaş. DirectLake ikisinin de iyi tarafını verir.
- **SQL Analytics Endpoint:** Lakehouse'a SQL ile (ODBC/pyodbc) bağlanma noktası. Web app'in custom React sayfaları Fabric'i buradan okuyor (DAX değil, SQL).
- **EventStream + Eventhouse (KQL):** Fabric'in gerçek-zamanlı veri akışı + zaman-serisi analiz veritabanı (Kusto Query Language ile sorgulanır). Page 8 IoT'nin canlı yolu.
- **RLS (Row-Level Security):** Power BI'da kullanıcının hangi satırları (hangi binayı) göreceğini kısıtlayan özellik. EnergyLens `building_id` üzerinde RLS uygular.
- **Capacity (F-SKU):** Fabric'in fiyat/hesaplama birimi (F2, F4, F8...). F2 production POC için en küçük makul birim.
---

## 3. Mimari — Medallion, Reference Layer, 3 Katman Erişim

### 3.1 Uçtan uca akış (bunu bir kağıda çizebilmelisin)

```
KAYNAKLAR
  Akıllı sayaçlar, faturalar (CSV / API)
  BMS sensörleri (BACnet, Modbus, MQTT, OPC-UA)
  Hava API'leri (Open-Meteo / DWD / MGM)
  Batarya telemetrisi, solar inverter
  Elektrik fiyatı (ENTSO-E), şebeke CO₂ (ElectricityMaps)
            │
            ▼
INGESTION (Microsoft Fabric)
  Data Factory pipeline → batch    (Tier 1)
  EventStream           → real-time (Tier 2/3)
            │
            ▼
DEPOLAMA — Fabric Lakehouse (OneLake, Delta format)
  BRONZE  ham, geldiği gibi
     └─► SILVER  temiz, normalize, doğrulanmış
              └─► GOLD  iş-hazır (KPI, anomali, simülasyon)
                        │
                        ▼ DirectLake mode
                 SEMANTIC MODEL (Power BI)
                 9 sayfalık rapor + DAX kütüphanesi (v57–v60)
                        │
            ┌───────────┼───────────────┐
            ▼           ▼               ▼
     Embedded PBI   Custom React     AI Copilot
     (DirectLake)   (SQL Endpoint)   (tool use)
```

### 3.2 Medallion mimarisi — neden bu yapı?

**Bronze (ham):** Veri geldiği gibi yazılır, hiç dokunulmaz. Tablolar: `raw_energy_readings`, `raw_solar_generation`, `raw_battery_status`, `raw_weather_data`, `raw_hvac_data`, `bronze_iot_raw`. `building_id / yıl / ay / gün` ile partition'lı.

**Silver (temiz):** Normalize edilmiş, kalite-kontrollü, birimleri standartlaştırılmış. Kalbi: `silver_building_master` — tüm mantığı yöneten boyut tablosu (bina kimliği, coğrafya, alan, tip, abonelik, teknoloji bayrakları `has_pv`/`has_battery`/`has_heat_pump`, kabuk U-value'ları, EPC, regülasyon profili). Ayrıca `energy_readings_clean`, `solar_generation_clean`, `battery_status_clean`, `weather_clean`.

**Gold (iş-hazır):** Power BI'ın doğrudan okuduğu KPI/anomali/simülasyon tabloları: `gold_kpi_hourly/daily/monthly`, `gold_anomaly_log`, `gold_ghg_scope`, `gold_compliance_results`, `gold_recommendations`, `gold_hvac_analytics`, `gold_iot_realtime/fdd/daily_summary`, batarya tabloları, vb. Toplam ~57 Lakehouse tablosu (3 katman boyunca).

> **Neden medallion?** Çünkü her açıklanan kg CO₂'yi **ham fatura satırına kadar geri izleyebilmek** istiyorsun — bu "audit-ready / regulator-grade lineage" demek ve CSRD/ESRS denetiminin tam ihtiyacı. Fabric'in süper gücü budur. Ayrıca ingestion / transformation / business-logic'i ayırmak kodu temiz ve açıklanabilir tutar.

### 3.3 Reference Layer (tek doğruluk kaynağı) — denetim sonrası eklendi

Denetimde en büyük açık şuydu: emisyon faktörleri ve tarifeler kodun içinde dağınık sabitlerdi (aynı TR faktörü 4 dosyada farklı). **Çözüm:** kaynaklı, yıl-indeksli referans tabloları:
- `ref_grid_emission_factors` (12 ülke; kaynak + URL + yıl)
- `ref_electricity_tariffs` (5 ülke)
- `ref_fuel_factors` (4 yakıt; gaz 0.201 DEFRA)

Artık her motor (03, 05, 06, 09, 11, 12) bu tablolardan JOIN ile okuyor. Bu, "satır-düzeyi lineage: ham faktörden açıklanan kg CO₂'ye" satış argümanının gerçekleştiği yer.

### 3.4 Gerçek veri kaynakları (artık tamamen sentetik değil)

Önemli bir olgunlaşma: bina-içi tüketim/solar/batarya verisi hâlâ 10 temsili bina için sentetik üretiliyor (gizlilik + henüz müşteri yok), **ama** dış sinyaller artık gerçek açık-kaynak API'lerden:
- **Open-Meteo** → gerçek saatlik hava + shortwave radiation → `silver_weather_clean` (211k satır, gerçek HDD/CDD, climate_adjusted_eui'yi besler)
- **ENTSO-E** → gerçek elektrik fiyatı → ref_electricity_tariffs
- **ElectricityMaps** → canlı şebeke CO₂

> **Önemli ayrım (hocaya):** Disclosure (Scope 2) için grid faktörü **yıllık-resmî** (UBA/TEİAŞ) kalır — auditable olması için. Canlı ElectricityMaps operasyonel içgörü için. Open-Meteo ücretsiz ama ticari-değil → satışta DWD (resmî Alman hava servisi) kullanılacak.

### 3.5 Tier-aware ingestion (kademeye duyarlı veri alımı)

Her binaya streaming pipeline koymak israf — akıllı sayaç zaten saatlik veri veriyorsa neden gerçek-zamanlı ödeyesin? O yüzden:
- **Tier 1 (Insight):** batch (Data Factory), ~1 saat gecikme, sayaç + fatura
- **Tier 2 (Monitor):** + IoT sensörleri (BACnet/Modbus/MQTT), 5–15 dk
- **Tier 3 (Copilot):** + batarya/ısı pompası telemetrisi, <5 dk

### 3.6 Üç katmanlı erişim modeli (CONFIRMED tasarım kararı)

Bu, kurumsal BMS ürünlerinin (Siemens Desigo, Schneider EcoStruxure) çalışma şekli. Üç farklı katman, üç farklı görev:

```
KATMAN 1 — Power BI RLS (VERİ katmanı)
  → Hangi binayı/veriyi görür? "Müşteri A sadece kendi 3 binasını görür"
  → building_id üzerinde RLS. Page visibility'yi KONTROL EDEMEZ (PBI teknik sınırı)

KATMAN 2 — Web App Navigation (MODÜL katmanı, Next.js)
  → Hangi sayfa/modül açık? "IoT sensörü yok → Page 8 kilitli"
  → DB'den abonelik + bağlı sensör envanteri okur

KATMAN 3 — Subscription / Tier (TİCARİ katman, PostgreSQL + FastAPI)
  → Hangi özellik aktif? Plan-bazlı feature gate
```
RLS her zaman aktif — veri asla müşteri sınırını geçmez.

**Pratik örnek:**
```
Müşteri A: 3 bina, sadece enerji sayacı → Sayfa 1-7 aktif, 8 ve 9 KİLİTLİ
Müşteri B: 1 bina, enerji + IoT → Sayfa 1-8 aktif, 9 KİLİTLİ
Müşteri C: 6 bina, full paket → 9 sayfa aktif
```

### 3.7 Notebook envanteri (pipeline'ın gerçek dosyaları)

Hoca "kodun nasıl organize?" derse, kategorilere göre:
- **reference/** — `00_reference_data_loader`, `01_epc_ratings_loader`, `03_ref_factors_tariffs_loader` (tek doğruluk kaynağı)
- **ingestion/** — `01_bronze_ingestion`, `02_openmeteo_weather_loader`, `03_entsoe_price_loader`, `05_electricitymaps_co2_loader`
- **transformation/** — `02_silver_transformation`
- **gold/** — `03_gold_kpi_engine` (Sayfa 1-2 çekirdek), `09_ghg_scope_engine` (Sayfa 6), `10_crrem_pathway_loader`, `11_hvac_analytics_engine` (Sayfa 7)
- **anomaly-detection/** — `anomaly_detection.py` (Sayfa 3, tek otorite)
- **forecasting/** — `07_consumption_forecast` (Prophet, Sayfa 4), `08_occupancy_prediction`
- **compliance/** — `05_compliance_checker` (Sayfa 5)
- **recommendation/** — `06_recommendation_engine` (Sayfa 5)
- **simulation/** — `04_simulation_engine`, `12_battery_dispatch_and_simulation` (+13/14/15, Sayfa 9)
- **iot/** — `00_iot_sensor_master_generator`, `01_bronze_iot_raw_generator`, `11b_iot_processing`, `11c_iot_fdd` (Sayfa 8 AFDD)
- **loaders/** — `16_load_page9_tables`

> **DP-600 best-practice kararları (hoca teknik sorarsa):** DeltaTable MERGE > spark.sql UPDATE (idempotent); native `when/otherwise` > Python UDF (Catalyst optimizer'ı bloklamaz); schema-enabled lakehouse için dinamik `_resolve_tables_prefix()` (Tables/dbo/ vs Tables/); silent except yasak (hatalar görünür olmalı).
---

## 4. 9 Power BI Sayfası — her birini tam anlat

Her sayfa için: **hangi soruyu cevaplıyor · hedef kullanıcı · KPI'lar + formül · visual'lar · bilinen sınır.** Bilinen sınırları Bölüm 9'da topluca da çerçeveliyorum; burada sayfa-bazında veriyorum ki demoda hangi sayfada neyi dikkatli anlatacağını bil.

### Sayfa 1 — Portfolio Overview

- **Soru:** "Portföyüm bu ay nasıl gidiyor?"
- **Kullanıcı:** Energy Manager, C-suite
- **KPI'lar:** Toplam portföy kWh; kWh/m² (EUI) bina-bazlı ısı haritası; toplam enerji maliyeti €; toplam CO₂ kg; en kötü 3 bina (tip-benchmark'a göre en yüksek EUI)
- **Visual'lar:** Bina-bazlı tüketim bar; EUI heat map; maliyet/CO₂ kartları; underperformer listesi
- **Kaynak:** `gold_kpi_daily` portföy seviyesine toplanmış
- **Bilinen sınır:** Aylık trend görselinde bir aggregation pürüzü vardı (saatlik toggle / time-grain field parametresi PBI tarafında kurulurken); `gold_kpi_hourly[date] → Date[Date]` ilişkisi kurulduğunda çözülüyor.

### Sayfa 2 — Building Deep-Dive

- **Soru:** "Bu bina şu anda ne yapıyor?"
- **Kullanıcı:** Facility Manager
- **KPI'lar:** 24-saat tüketim profili (saatlik kW); bugünkü peak vs baseline; aya kadar maliyet; iklim-düzeltilmiş EUI
- **Visual'lar:** Saatlik demand çizgisi; peak göstergesi; maliyet kartı
- **Kaynak:** `gold_kpi_hourly` + `gold_kpi_daily`, `building_id` filtreli
- **Bilinen sınır:** Solar PR'da sentetik-üretim ↔ gerçek-irradiance uyumsuzluğundan kaynaklı gürültü olabilir (Open-Meteo gerçek ışınım geldi ama solar üretimi hâlâ sentetik). Demoda solar'ı olan binada PR'a fazla odaklanma.

### Sayfa 3 — Anomaly Detection

- **Soru:** "Nerede enerji israfı / arıza var?"
- **Kullanıcı:** Facility Manager, Energy Manager
- **KPI'lar / Visual'lar:** Severity'ye göre anomali sayısı (LOW/MEDIUM/HIGH/CRITICAL); tip kırılımı; anomali tablosu (zaman, tip, severity, etkilenen sistem, önerilen aksiyon, tahmini € kayıp); çözüm durumu (`is_resolved`)
- **Anomali tipleri (canlı motor — anomaly_detection.py, 7 tip):** CONSUMPTION_SPIKE, COP_DEGRADATION, SOLAR_UNDERPERFORM, BATTERY_IDLE, HIGH_CARBON_INTENSITY, DATA_GAP, AFTER_HOURS_WASTE. Üçdilli (en/de/tr) açıklama + önerilen aksiyon.
- **Kaynak:** `gold_anomaly_log` (TEK otorite = anomaly_detection.py; eski 03 §8 motoru legacy'ye taşındı)
- **Bilinen sınır:** Eskiden iki motor aynı tabloyu farklı taksonomiyle yazıyordu (run-order'a göre değişiyordu) — düzeltildi, tek motor. COP/karbon anomalileri proxy (gerçek COP telemetrisi sadece ısı pompalı binada var). SOLAR_PR_DROP gürültüsü (yukarıda).

### Sayfa 4 — Forecasting

- **Soru:** "Gelecek ay/çeyrek ne kadara mal olacak?"
- **Kullanıcı:** Energy Manager, Sustainability Manager
- **KPI'lar / Visual'lar:** 7/30/90-gün ileri tüketim tahmini (Prophet); tahmini maliyet €; tahmini CO₂; güven bandı (confidence interval)
- **Kaynak:** `gold_kpi_daily` + Prophet model çıktısı. HDD/CDD + occupancy regressor'ları. Bina-tipine duyarlı eşikler.
- **Bilinen sınır (dürüst, hocaya söyle):** MAPE (hata metriği) **in-sample** hesaplanıyor — yani modeli kendi eğitim verisinde test ediyor, bu doğruluğu olduğundan iyi gösterir. Müşteri sayısı için Prophet `cross_validation` (rolling-origin) kullanmak roadmap'te. Şimdilik "in-sample fit" diye etiketlemek dürüst olan. Güven bandı hesaplanıyordu ama görselde gösterilmiyordu (v54 backlog) — production-ready maratonunda band görsele bağlandı.

### Sayfa 5 — Decision Support (Karar Desteği)

- **Soru:** "Ne yapmalıyım, hangi sırayla, ne kazandırır?"
- **Kullanıcı:** Energy Manager, Sustainability Manager
- **KPI'lar / Visual'lar:** priority_score'a göre sıralı öneriler; tahmini tasarruf (€/yıl, kWh/yıl, CO₂ kg/yıl); uygulama eforu (LOW/MEDIUM/HIGH); payback yılı; eşleşen teşvik programları (KfW, BAFA, YEKA, EEG)
- **Kaynak:** `gold_recommendations` + `gold_compliance_results` + simülasyon sonuçları
- **Güçlü yan:** Çok-ülkeli regülasyon skorlaması (DE GEG/EnEfG/EEG, AT OIB-RL6/EAG, NL Energielabel, TR BEP-TR, EU EPBD) + teşvik eşleştirme — gerçek bir farklılaştırıcı.
- **Bilinen sınır:** "CSRD score" diye adlandırılan bir skor karbon-yoğunluğu eşiğinden hesaplanıyordu — **ama CSRD bir açıklama direktifidir, kg/m² eşiği değil.** v57'de `eu_taxonomy_score` / `csrd_disclosure_readiness %` olarak yeniden adlandırıldı. Hocaya: "CSRD bir performans limiti koymaz, disclosure tamlığıdır" — bunu bil.

### Sayfa 6 — Sustainability (ESG / GHG) — ANA NİŞ SAYFASI

- **Soru:** "Karbon ayak izim ne, AB-uyumlu raporlamaya hazır mıyım?"
- **Kullanıcı:** Sustainability Manager, ESG danışmanı, denetçi
- **KPI'lar / Visual'lar:** Scope 1/2/3 donut (mevcut ay); yıldan yıla Scope toplam bar; EPC uyumluluk heatmap (A+→G, **area-weighted**); ESG Score 0–100; carbon credit potansiyeli €
- **Kaynak:** `gold_ghg_scope` + EPC + CRREM pathway
- **ESRS E1 eşlemesi:** E1-5 (enerji karışımı), E1-6 (Scope 1/2/3, hem location- hem market-based)
- **Bilinen sınırlar (BURASI EN HASSAS — Bölüm 9'da detay):**
  1. Scope 3 = (S1+S2)×%8 *screening tahmini*, `scope3_disclosure_grade=False` etiketli. ESRS-ready değil.
  2. Market-based Scope 2 mekanizması var (supplier_ef) ama gerçek tedarikçi verisi olmadan location-based'e eşit çıkar.
  3. CRREM pathway'leri indikatif (License Partner değil).
  4. Refrigerant (soğutucu gaz) Scope 1 henüz hariç (opsiyonel roadmap).
  > **Bunu mutlaka çerçevele:** "Sayfa 6 şu an Scope 1/2 için solid, denetlenebilir lineage var; Scope 3 ve market-based S2 gerçek aktivite/tedarikçi verisiyle güçlendirilecek. Ben buna 'ESRS-E1-aligned reporting support' diyorum, 'audited CSRD disclosure' değil."

### Sayfa 7 — HVAC & Hourly Profile

- **Soru:** "Isıtma/soğutma sistemim verimli mi?"
- **Kullanıcı:** Facility Manager, bina sahibi
- **KPI'lar / Visual'lar:** Saatlik ısı pompası COP (gerçek vs rated); supply/return hava sıcaklık delta'sı (HVAC verim proxy'si); HVAC çalışma saatleri; HVAC'in toplam tüketimdeki payı; 10-bina portföyü (B007 Copenhagen Net-Plus, B008 Leipzig Plattenbau, B009 Frankfurt DC, B010 Stockholm Lab dahil)
- **Kaynak:** `gold_hvac_analytics` + silver HVAC
- **Bilinen sınır (dürüst):** HVAC ısıtma/soğutma/havalandırma **split'i sub-metered değil, bina-tipi katsayısı + hava şekli ile modellenmiş** (ör. Office HVAC payı ~0.35'e sabitlenmiş gibi). Bir HVAC mühendisi bunu hemen tanır. Görselde "modeled split (HDD/CDD method) — sub-metering refines this" diye çerçevele. Sub-metering Tier-3 upsell. Envelope/heat-loss geometrik tahmin; COP sadece ısı pompalı binada gerçek.

### Sayfa 8 — Real-Time IoT Monitoring — FLAGSHIP (app'in en güçlü tarafı)

- **Soru:** "Binalarımda şu an ne oluyor, hangi arıza para yakıyor?"
- **Kullanıcı:** Facility Manager (operasyon) + Energy Manager (stratejik)
- **KPI kartları:** C1 gerçek-zamanlı bina gücü (kW, yeşil/amber/kırmızı vs baseline); C2 zone comfort compliance % (setpoint içindeki zone'lar); C3 CO₂ seviyesi (Good/Fair/Poor); C4 aktif alarm + tahmini günlük € maliyet ("3 Alerts — Est. €47 today")
- **Visual'lar:** V1 24h güç trendi (`building_kwh` + `hvac_kwh` ayrı seriler + baseline); V2 sensor uptime matrisi (satır=zone, sütun=sensor_type — **DİNAMİK, hardcoded değil**); V3 zone setpoint compliance; V4 alarm tablosu; V5 FDD teşhisleri
- **Mimari:** Event Hub → EventStream → KQL Eventhouse + Lakehouse → DAX. `sensor_type` bir **DİMENSİON** — her bina sadece bağlı sensör tiplerini gösterir.
- **AFDD (Automated Fault Detection & Diagnostics):** `11c_iot_fdd.py` — **ASHRAE Guideline 36** bazlı, 12 kural (zone/AHU/chiller/boiler/pump/bina), frozen FAULT_CODES, teşhis-düzeyi çıktı (occurrence/persistence + confidence + priority_score + probable_cause + energy_impact). ~31 sensör tipi (IAQ: CO2/VOC/PM2.5/PM10; occupancy; energy sub-metering; HVAC telemetri; water; PV/battery/EV).
- **Anomali maliyet tahmini (her zaman "Est." etiketli):**
```
cost_eur = süre_saat × güç_israfı_kw × grid_fiyat_eur_kwh
HVAC_temp ihlali: °C sapma başına 2-5 kW; CO2>1500ppm: 1-3 kW; güç spike >120%: gerçek fazla kW
Grid fiyatı: ref_electricity_tariffs'ten (DE/TR)
```
- **Bilinen sınır:** Page 8 EventStream'e bağlı; trial sonrası stream kapanınca **statik IoT snapshot** (sensor_master + bronze + 11b + 11c) demoyu besler. Yani demoda Page 8 statik snapshot'tan canlı görünür. Maliyet eskiden upstream'den enjekte ediliyordu; refactor'da silver IoT adımına + ref_electricity_tariffs'e taşındı.

### Sayfa 9 — Battery Dispatch & ROI

- **Soru:** "Bataryaya yatırım yapmalı mıyım, hangi kimya/strateji, ne zaman geri öder?"
- **Kullanıcı:** Energy Manager, CFO, yatırımcı
- **KPI'lar / Visual'lar:** Batarya teknoloji matrisi (LFP/NCA/NMC/Solid-State × 12 ülke → 49 fitness skoru); 7 dispatch stratejisi karşılaştırması; ülke-bazlı elektrik fiyatı (EPEX/ENTSO-E DE-EU, EXIST TR, fallback); €/kWh yatırım maliyeti; payback yılı, NPV (5% iskonto, 10-yıl), IRR; EU Battery Regulation 2023/1542 uyumluluk bayrağı (karbon ayak izi, geri-dönüşüm içeriği, garanti döngüleri)
- **Kaynak:** `gold_battery_dispatch` + `battery_simulation` + `battery_technologies` + `country_regs` + `strategy_fitness`. 12 ülke × 8 kimya × 7 strateji.
- **Güçlü yan:** Gerçek finansal model (enflasyon + salvage'lı NPV, Newton-Raphson IRR, payback). Tam EU 2023/1542 alanları.
- **Bilinen sınır (dürüst, CFO sayfası olduğu için kritik):** Batarya tasarrufu muhtemelen **abartılı** — tüm deşarj **peak tarifeyle** değerleniyor (gerçekte peak/mid/off-peak karışımını öteler) ve demand-charge tasarrufu peak-kW azalması yerine deşarj enerjisiyle orantılı hesaplanıyor → payback fazla kısa, NPV/IRR fazla iyi görünüyor (ör. B003 1.6 yıl / %64 IRR iyimser). Roadmap: deşarjı öttüğü saatin tarifesiyle değerle, demand tasarrufunu modellenmiş peak-kW tıraşına bağla. **Hocaya/yatırımcıya: "ROI modeli yapısal olarak doğru (NPV/IRR/payback), ama mevcut sayılar üst-sınır; saat-bazlı tarife eşleştirmesiyle daha muhafazakâr hale getiriyorum."**
---

## 5. Web Uygulaması — sayfalar ve özellikler

Web app **Next.js 16 (frontend) + FastAPI (backend) + Azure PostgreSQL (DB)**. Power BI raporu "kilitli, versiyonlanmış bir şablon" (embedded, read-only); web app ise üstüne **navigasyon, erişim kontrolü, özel React sayfaları, AI Copilot, PDF export, audit log** ekliyor. Üç auth provider: Microsoft Entra ID + Google + Email/Password (bcrypt).

> **Neden ayrım?** Rapor = design-time şablon (PBI Desktop'ta değişir, publish edince embed güncellenir). App katmanı = runtime özellikler. Embedded view'da müşteri rapor düzenleyemez (sadece görür); özelleştirme app katmanında.

### Sayfa sayfa (her birinin amacı + ana özellikleri)

- **`/` (landing) + `/login` + `/signup` + `/forgot-password`:** Public giriş. Markalı (EnergyLens Emerald Pulse). 3-provider auth. Login sonrası callbackUrl'e döner.

- **`/onboarding`:** Zorunlu kurulum sihirbazı (5 adım): bina temel bilgileri → sistemler (solar kWp + modül + veri kaynağı) → review → done. `POST /buildings` ile bina yaratır, solar temelini atar. Binası olmayan kullanıcı buraya yönlendirilir.

- **`/portfolio`:** Ana gösterge paneli. Fabric Lakehouse'tan **SQL Analytics Endpoint** üzerinden okur (DAX değil, pyodbc/ODBC — DirectLake+SP+ExecuteQueries 401 bloğu nedeniyle seçildi). Özellikler: Portfolio KPI satırı (toplam kWh, maliyet, CO₂, EUI), On-site Solar KPI satırı, bina tablosu (her bina EUI/maliyet/anomali), "veriler bağlı değil" banner'ı (binası olup hepsi fabric_building_id=NULL ise), Export PDF linki, glossary tooltip'leri.

- **`/buildings` + `/buildings/[id]` + `/buildings/compare`:** Bina listesi (şehir silüeti motifli kartlar, seçim localStorage'da kalıcı, sticky Compare bar) → bina detay (embedded Power BI, service principal + V2 embed API + DirectLake, aspect-locked + persistent embed = tek mount in-place nav) → karşılaştırma. ReportNav ile modül-bazlı deep-link route'lar (`/buildings/[id]/reports/[page]`); IoT/battery modülü yoksa LockedReportPreview gösterir.

- **`/solar`:** Adanmış solar sayfası — custom SVG (bağımlılık yok). Solar KPI'lar, üretim/öz-tüketim görselleri.

- **`/compliance` (2026-06-02, AB-gündemi hub'ı — Schneider/Siemens konumlandırması):** 5 özellik, hepsi frontend-only (/portfolio verisini reuse, indikatif):
  1. **MEPS Radar** — EPBD 2030/2033 yenileme-risk bandı (EPC F-G=high, D-E=watch; EUI>200 ikincil sinyal)
  2. **CRREM Stranding** — bina/portföy "stranding yılı", 2025→2050 indikatif 1.5°C pathway
  3. **Flexibility Readiness** — asset-flag bazlı (battery/IoT/PV) talep-esnekliği hazırlığı (DR Network Code ~2027 bağlamı)
  4. **ESRS-E1 Summary** — E1-5 enerji + E1-6 Scope 1/2/3 özet (backend `/compliance/esrs`, gold_ghg_scope'tan; "ESRS-E1-aligned, not audited" uyarısı)
  5. **EU Taxonomy** — Activity 7.7 alignment indication (sadece climate-mitigation SC; "aligned/compliant DEME" caveat'ı)
  + Compliance PDF export. Her özellikte **anti-greenwashing caveat** her zaman görünür.

- **`/actions`:** Öneri/aksiyon yönetimi. Fabric `gold_recommendations` + Postgres overlay (status). 37 öneri. Status dropdown (new/in-progress/done/dismissed), filter chips, nav badge. Değişiklik audit log'a yazılır.

- **`/alerts`:** Portföy anomali izleme. `gold_anomaly_log` (read) + Postgres `alert_status` overlay (acknowledge). is_resolved (Fabric) × ack_status (Postgres) → "unhandled" = unresolved & not-acked → nav badge + triyaj kuyruğu. Server-side severity/resolution filtreleme. `?building_id` ile bina-scoped.

- **`/copilot`:** AI Copilot sohbet arayüzü (Bölüm 6).

- **`/glossary`:** 10 domain teriminin tek-kaynak public sayfası (lib/glossary.ts). Uygulama genelinde InfoTip/TermLabel tooltip'leriyle bağlı (portfolio/solar/actions/alerts/compliance inline).

- **`/settings`:** Org profili + üyeler + davet (copy-link / `/invite/[token]` kabul) + abonelik kartı (Stripe self-serve) + aktivite (audit log, admin-only) + billing dönüş banner'ı. JWT'de org_id, son-admin guard.

- **`/admin` (sadece founder — is_platform_admin):** Platform admin. Cross-org read (StatsCards + organizations/buildings/users tabloları) + mutations (tier/status değiştir, modül toggle → /reports kilidini açar, fabric_id link) + audit activity tablosu. Tüm admin mutation'ları audit_logs'a (actor + IP/UA).

- **`/billing` + `/pricing`:** Stripe self-serve (4 tier: Free/Basic/Monitor-featured/Enterprise). Checkout + Portal + webhook. Public /pricing sayfası → /signup → /settings Checkout.

- **`/demo`:** Kayıtsız public erişim — 6 örnek bina + RLS-restricted embed. EXIST/BSBI/Avrupa için pazarlama URL'i.

- **`/reports/*` + `/*/report` route'ları:** PDF export — ayrı açık-temalı A4-landscape route'lar + `window.print()` (sıfır bağımlılık). Portfolio, actions, alerts, compliance, building-level raporlar — hepsi ortak `reportKit.tsx` üstünde.

### Cross-cutting (uygulama geneli)
- **Audit log:** Tüm mutation'lar (admin + settings + building + action + alert) audit_logs'a yazılıyor (actor + IP/UA + action). Müşteri tarafı /settings'te, admin tarafı /admin'de görünür.
- **Graceful degradation:** Fabric tablosu düşerse global pyodbc.Error → 503 {fabric_unavailable} → sakin amber "temporarily unavailable" notice (500 yerine).
- **Edge-state:** markalı 404 / error boundary / loading skeleton'lar.
- **Mobile responsive** + a11y (focus-visible, skip-to-content, prefers-reduced-motion).
- **SEO/paylaşım:** OG kartları, sitemap, robots, metadata.

---

## 6. AI Copilot — derin dive

Bu, app'in en "wow" özelliği ve EXIST'te inovasyon argümanın. **Fark:** Çoğu BI ürünü "Copilot" deyince rapor sayfasını **metin olarak özetler**. EnergyLens Copilot ise **tool use** ile Lakehouse'a *gerçek sorgu* atar — yani "uyduran" değil, "veriden okuyan" bir asistan.

### Mimari akış
```
Kullanıcı sorusu (doğal dil)
   → Orchestrator (services/copilot/orchestrator.py)
   → LLM (provider abstraction) tool_use kararı verir
   → Dispatcher (dispatcher.py) tool'u çalıştırır → Fabric/Postgres'e GERÇEK sorgu
   → tool_result LLM'e geri döner
   → LLM nihai doğal-dil cevabı üretir
   → SSE (Server-Sent Events) ile UI'a stream edilir (kelime kelime)
```

### 6 production tool (kodda doğrulandı — `TOOL_HANDLERS`)

| Tool | Ne yapar | Veri kaynağı |
|---|---|---|
| **`query_kpi`** | Bina(lar) için KPI sorgular (kWh, EUI, maliyet, CO₂, dönem karşılaştırması/delta) | Fabric gold_kpi |
| **`compare_buildings`** | Binaları bir metrikte karşılaştırır, sıralar | Fabric gold_kpi |
| **`list_recommendations`** | Bir bina için önerileri priority'ye göre listeler | Fabric gold_recommendations |
| **`get_anomalies`** | Anomalileri severity/tip filtreyle getirir | Fabric gold_anomaly_log |
| **`simulate_battery_scenario`** | Batarya senaryosu çalıştırır (payback/NPV/IRR) | Fabric battery tabloları |
| **`update_action_status`** | Bir aksiyonun durumunu değiştirir (yazma işlemi) | Postgres |

> **Hocaya gösterebileceğin nüans:** Bu 6 tool sadece okuma değil — `update_action_status` bir **yazma** işlemi. Yani Copilot sadece "anlatmıyor", aksiyon da alabiliyor. Her tool'un input'u JSON schema ile doğrulanır; org/building-level RLS her tool çağrısında uygulanır (kullanıcı sadece yetkili olduğu binayı sorgulayabilir).

### LLM Provider abstraction
Tek bir environment variable ile sağlayıcı değişir — kod aynı kalır:
- **Anthropic (Claude)** — production hedefi
- **Azure OpenAI (GPT-4o)** — Microsoft-native alternatif
- **Mock** — şu an aktif (Anthropic kredisi €0 olduğu için); deterministik sahte cevaplar, gerçek tool çağrılarıyla, demo/test için

> **EXIST argümanı:** "Provider abstraction zaten yerinde — production'a geçiş tek environment variable. Azure OpenAI kredisi gelince Mock'tan GPT-4o'ya geçmek anlık." Bu, "mühendislik olgunluğu" sinyali.

### Teknik detaylar (hoca derine inerse)
- **SSE streaming:** Cevap tek seferde değil, token-token akar (UX). Event tipleri: `tool_call_start`, `tool_call`, `tool_result`, sonra metin.
- **Tool-use loop:** LLM tool çağırır → sonuç döner → LLM tekrar düşünür → gerekirse başka tool → nihai cevap. Çok-adımlı.
- **Conversation persistence:** Sohbet Postgres'te saklanır (`copilot` tabloları); tool_calls JSONB, tool_call_id, tool_name — Anthropic/OpenAI tool-use şemasını birebir yansıtır.
- **JWT auth + RLS:** Her istek kimlik doğrular; tool'lar `_check_building_access` ile yetkiyi kontrol eder.

> **Bu neden bir "üçüncü veri yolu"?** Fabric'e erişimin 3 yolu var: (1) Power BI DirectLake embed, (2) custom React → SQL Analytics Endpoint, (3) **AI Copilot → LLM tool use → dispatcher → Fabric**. Üçü de uçtan uca doğrulandı. Bu çeşitlilik, "tek noktaya bağımlı değilim" demek — mühendislik olgunluğu.
---

## 7. Veri Modeli & 10 Temsili Bina

### 7.1 Neden 10 bina, 3.5 yıl, ~693K data point?

Henüz gerçek müşteri olmadığı için platform **10 temsili bina** üzerinde çalışıyor. Bu seçim bilinçli:
- **10 bina** → portföy mantığını (karşılaştırma, ranking, RLS, area-weighting) anlamlı göstermeye yetecek çeşitlilik, ama yönetilemeyecek kadar çok değil.
- **3.5 yıl** → mevsimsellik (HDD/CDD döngüsü), yıldan-yıla trend (A7 insulation degradation anomalisi yıl karşılaştırması ister), ve Prophet forecast'in eğitilmesi için yeterli tarih.
- **~693K data point** → saatlik granülerlik × bina × sensör × 3.5 yıl. Demo'nun "oyuncak" değil "production-scale" hissettirmesi için.

**Coğrafi/tip çeşitliliği:** Germany, Turkey, Austria, Netherlands. Farklı iklim zone'ları (Köppen: Cfb oceanic, BSk semi-arid), farklı bina tipleri (Office, Retail, Hotel, Logistics, Healthcare, Data Center, Lab), farklı teknoloji profilleri (kimi solar+battery, kimi sadece sayaç).

**Showcase'te öne çıkan binalar (Sayfa 7 genişletmesi):**
- B007 — Copenhagen Net-Plus (enerji-pozitif bina)
- B008 — Leipzig Plattenbau (eski prefabrik, kötü kabuk)
- B009 — Frankfurt Data Center (yüksek yoğunluk)
- B010 — Stockholm Lab (özel yük profili)

> **Dürüst not (Bölüm 9'da da var):** B003 ve B005'in kimliği bazı notebook'lar arası çelişiyor (B003: Vienna Hotel mi Hamburg Logistics mi; B005: Berlin Healthcare mi Frankfurt mı). Bu demo-data tutarsızlığı düzeltme listesinde. **Demoda B003/B005'i tek tek şehir-ismiyle anmaktan kaçın** ya da düzeltilene kadar B001/B002/B007-B010'a odaklan.

### 7.2 building_master — veri modelinin omurgası

`silver_building_master` tüm mantığı yöneten boyut tablosu. Her bina için: kimlik (building_id, organization_id), coğrafya (country_code, city, climate_zone), alan (gross/conditioned m²), tip, abonelik tier, **teknoloji bayrakları** (has_pv, has_battery, has_heat_pump, has_ev_charging, has_led_lighting), PV detayı (kWp, roof orientation/tilt), batarya detayı (kWh, technology, strategy), ısı pompası (cop_rated, capacity), **kabuk** (wall/roof/floor/window U-value, WWR, air-tightness ACH, thermal mass, insulation year), uyumluluk (energy_certificate A+→G, iso50001_certified, regulatory_profile_id).

> **Teknoloji-profili gating'in gücü:** `has_pv=False` olan binada solar görselleri hiç çıkmaz (boş "N/A" hücreler yerine). Her bina sadece kendi ilgili analitiğini görür. Bu, kurumsal BMS ürünlerinin çalışma şekli.

### 7.3 Gold tablolar (Power BI'ın okuduğu iş-hazır katman)
`gold_kpi_hourly` (32 kolona yakın: tüketim, demand, solar, batarya, COP, maliyet, CO₂), `gold_kpi_daily`, `gold_kpi_monthly`, `gold_anomaly_log`, `gold_ghg_scope`, `gold_compliance_results`, `gold_recommendations`, `gold_incentive_matches`, `gold_hvac_analytics`, `gold_iot_realtime/fdd/daily_summary`, batarya tabloları (`gold_battery_dispatch/simulation/...`), `gold_data_health_log`. Hepsi `building_id` FK ile bağlı.

---

## 8. EU Compliance — derinlik (hocanın asıl alanı)

Hoca enerji yönetimi akademisyeni — regülasyon kısmında en çok burayı kurcalayabilir. Her birini "EnergyLens bunu *nasıl* hesaplıyor" düzeyinde bil.

### 8.1 CRREM stranding — nasıl hesaplanıyor
1. Binanın **carbon intensity**'sini bul: `(CO₂_son30gün × 365.25/30) / conditioned_area` → kg CO₂/m²/yıl.
2. Bina tipi + bölge için **1.5°C uyumlu pathway** eğrisini al (yıldan yıla düşen kg CO₂/m²/yıl). EnergyLens'te [2025, 2050] arası lineer interpolasyonlu anchor'lar.
3. Binanın yoğunluğu pathway eğrisini hangi yıl **keserse** (üstüne çıkarsa) → o yıl **stranding yılı**. "Stranded now" / "stranding 20XX" / "on track" olarak sınıflandır.

> **Önemli düzeltme (hoca sorarsa anlat):** Başta CRREM karşılaştırması **Scope-2-only** yoğunluğu **Scope 1+2** pathway'iyle kıyaslıyordu (yani Scope 1 gazı hariç tutup binayı olduğundan iyi gösteriyordu — stranding'i hafife alıyordu). v57 DAX'ta Scope 1+2 intensity ölçüsü kurdum; CRREM Scope 3'ü zaten hariç tutar. Bu, doğru metodoloji.

### 8.2 Scope 1/2/3 ayrımı — EnergyLens nasıl yapıyor (`09_ghg_scope_engine.py`)
- **Scope 2 (elektrik):** `net_grid_kwh × emission_factor` — faktör artık `ref_grid_emission_factors`'tan **yıl-indeksli** JOIN ile (location-based). Market-based mekanizması supplier_ef kolonuyla var.
- **Scope 1 (gaz):** Gaz sayacı varsa onu kullanır; yoksa ısıtma payını elektrikten proxy'ler (`tüketim × 0.25 / ... × 2.04 m³`) — screening tahmini. Tek gaz faktörü (0.201, DEFRA).
- **Scope 3:** `(Scope1+Scope2) × %8` — açıkça `scope3_disclosure_grade=False` etiketli screening.

### 8.3 EU Battery Regulation 2023/1542 — uyumluluk kontrolü (Page 9)
Ocak 2024+ AB'de satılan her batarya için zorunlu alanlar: carbon footprint (PEF — Product Environmental Footprint etiketi), recycled content %, warranty cycles, cycle durability, State of Health. EnergyLens `gold_battery_technologies` tablosunda her kimya (LFP/NCA/NMC/Solid-State) için bu alanları tutar ve `eu_compliant` bayrağıyla işaretler. Page 9 senaryolarına **sadece EU-compliant bataryalar** girer.

### 8.4 ESRS E1 → EnergyLens sayfa eşlemesi (hocaya tablo göster)
| ESRS E1 kodu | Ne açıklar | EnergyLens |
|---|---|---|
| **E1-1** | İklim azaltım geçiş planı | Sayfa 4–5 (forecast, karar desteği) |
| **E1-5** | Enerji tüketimi ve karışımı | Sayfa 1–3 |
| **E1-6** | Brüt Scope 1, 2, 3 ve Toplam GHG | Sayfa 6 + /compliance ESRS-E1 export |
| **E1-9** | İklim risklerinin finansal etkileri | Sayfa 9 (batarya ROI, senaryo) |

> **Anti-greenwashing duruşu (bunu mutlaka iç dünyanda netleştir):** Biz bir **yazılım aracıyız, denetçi değiliz.** Pazarlamada/hocaya "ESRS-E1-aligned reporting support" de — "CSRD-compliant garantisi" / "audited disclosure" **DEME.** Sınır = veri kalitesi (Scope 3 estimated) + assurance (biz onaylamıyoruz) + metodoloji. Bu dürüstlük, bir akademisyenin gözünde profesyonellik işaretidir; abartı ise anında güven kaybettirir.
---

## 9. ⭐ Dürüstlük Katmanı — neyi savunursun, neyi nasıl çerçevelersin

> **Bu bölümü iki kez oku.** Bir enerji akademisyeniyle görüşmenin en büyük riski, abartılmış bir iddiayı savunamamak. En büyük fırsatı ise: zayıf noktayı *senin* önce, dürüstçe, roadmap'le söylemen. İkincisi seni "satıcı"dan "mühendis"e çevirir. Hoca dürüstlüğü ödüllendirir.

### 9.1 Temel duruş
Üç cümlelik zihinsel çerçeve:
1. **"Mühendislik tarafı güçlü"** — temiz medallion, idempotent Delta MERGE, schema-adaptive notebook'lar, gerçek NPV/IRR, çok-ülkeli regülasyon motoru, per-building Prophet, tam EU 2023/1542 batarya alanları. Bu doğru ve savunulabilir.
2. **"Bazı enerji-mantığı sayıları şu an gösterge düzeyinde"** — özellikle Scope 3, market-based Scope 2, CRREM resmî eğrileri, HVAC split, batarya ROI. Bunları "indicative / screening / modeled, with a clear roadmap to refine" diye çerçevele.
3. **"Bunu ben zaten denetledim"** — kendi gap register'ımı yazdım (`docs/audit/2026-05-30_gap_register.md`), açıkları severity etiketleyip fix sırası belirledim, çoğunu kapattım. Bu öz-denetim yeteneği, akademik bir zihne en güçlü sinyal.

### 9.2 Neyi GÜVENLE savunabilirsin (solid + düzeltilenler)

| Konu | Durum | Neden savunulabilir |
|---|---|---|
| Medallion mimarisi + lineage | Solid | Her kg CO₂ ham faktöre kadar izlenebilir; Fabric'in doğru kullanımı |
| **Reference layer (tek doğruluk kaynağı)** | ✅ Düzeltildi | ref_grid_emission_factors/tariffs/fuel — kaynak+URL+yıl. TR=0.442 (TEİAŞ), DE yıl-indeksli (UBA), gaz 0.201 (DEFRA). Eski 4-dosya çelişkisi bitti |
| **climate_adjusted_EUI** | ✅ Düzeltildi | Artık ratio metot, HDD **ve** CDD, referans baseline ile (eski sadece-HDD bölme düzeltildi) |
| **EPC area-weighting** | ✅ Düzeltildi | v57 DAX: `DIVIDE(SUMX(alan×skor),SUMX(alan))` — gerçekten alan-ağırlıklı (eski düz AVERAGE'dı) |
| **CRREM Scope 1+2 intensity** | ✅ Düzeltildi | v57: pathway ile aynı scope'ta karşılaştırma |
| **Tek anomali motoru** | ✅ Düzeltildi | anomaly_detection.py tek otorite (eski iki-motor çakışması bitti) |
| Çok-ülkeli regülasyon motoru (Sayfa 5) | Solid | DE/AT/NL/TR/EU gerçek kural mantığı + teşvik eşleştirme — gerçek farklılaştırıcı |
| Batarya finansal model **yapısı** | Solid | Enflasyon+salvage'lı NPV, Newton-Raphson IRR, payback — doğru finans |
| **Page 8 IoT / AFDD** | ✅ Flagship | ASHRAE Guideline 36, 12 kural, frozen FAULT_CODES, teşhis-düzeyi çıktı, ~31 sensör tipi, çok-protokol — sektör-grade |
| Prophet forecast (Sayfa 4) | Solid | Per-building, HDD/CDD+occupancy regressor, graceful degradation |
| Gerçek dış veri | ✅ Eklendi | Open-Meteo hava (211k satır gerçek HDD/CDD), ENTSO-E fiyat, ElectricityMaps CO₂ |
| AI Copilot (tool use) | Solid | 6 tool, provider abstraction, SSE, RLS, conversation persistence — uçtan uca test |

### 9.3 Bilinen sınırlar + DÜRÜST çerçeve (ezberle)

Her satır: **sınır → hocaya/müşteriye söyleyeceğin dürüst cümle (İngilizce) → roadmap.**

**1. Scope 3 = (S1+S2)×%8**
- *Sınır:* Düz oran; gerçek binalarda Scope 3 (özellikle Kat. 13 downstream leased assets) çoğu zaman en büyük kovadır.
- *Dürüst cümle:* "Scope 3 is currently a screening estimate — I flag it as not disclosure-grade in the data itself. For real reporting I'd model the material categories from activity data; that's on the roadmap."
- *Roadmap:* Kategori-bazlı Scope 3 input tablosu.

**2. Market-based Scope 2 = location-based**
- *Sınır:* Mekanizma var (supplier_ef) ama gerçek tedarikçi/yeşil-tarife verisi olmadan iki sayı eşit çıkar.
- *Dürüst cümle:* "The dual-method mechanism is in place. Right now the market-based figure equals location-based because I don't yet have per-building supplier contract data — once that's connected, the two diverge."
- *Roadmap:* Tedarikçi/contract EF tablosu.

**3. CRREM pathway'leri indikatif**
- *Sınır:* Resmî CRREM v2 tool verisi değil, temsili 1.5°C anchor'ları.
- *Dürüst cümle:* "The CRREM pathways are illustrative anchors. Embedding the official curves requires a CRREM License Partner agreement; I've isolated them in one module so I can swap in the official values once licensed."
- *Roadmap:* CRREM License Partner.

**4. HVAC heating/cooling/ventilation split modellenmiş (Sayfa 7)**
- *Sınır:* Sub-metered değil; bina-tipi katsayısı + hava şekliyle türetiliyor.
- *Dürüst cümle:* "The HVAC breakdown is a modeled split using the HDD/CDD method and type coefficients — not sub-metered. Sub-metering would refine it, and that's a Tier-3 upsell."
- *Roadmap:* Sub-meter ingestion.

**5. Batarya ROI üst-sınır (Sayfa 9)**
- *Sınır:* Tüm deşarj peak-tarifeyle değerleniyor; demand tasarrufu peak-kW yerine enerjiyle orantılı → payback fazla kısa.
- *Dürüst cümle:* "The ROI model structure is correct — proper NPV, IRR, payback — but the current savings are an upper bound: I value all discharge at the peak tariff. I'm refining it to price discharge by the hour it actually displaces, which makes payback more conservative."
- *Roadmap:* Saat-bazlı tarife eşleştirmesi; peak-kW bazlı demand tasarrufu.

**6. Forecast MAPE in-sample (Sayfa 4)**
- *Sınır:* Doğruluk eğitim verisinde ölçülüyor → iyimser.
- *Dürüst cümle:* "The accuracy number is in-sample fit right now. For a client-facing figure I'd use Prophet's rolling-origin cross-validation."
- *Roadmap:* cross_validation.

**7. Scope 1 refrigerant (soğutucu gaz) hariç**
- *Sınır:* HVAC soğutucu gaz kaçağı Scope 1'e dahil değil.
- *Dürüst cümle:* "Refrigerant fugitive emissions are Scope 1 and routinely missed — I don't capture them yet, but I know they belong there. A refrigerant log would close it."
- *Roadmap:* `silver_refrigerant_log` (gaz tipi, kg, GWP).

**8. Solar üretim sentetik / PR gürültüsü**
- *Sınır:* Gerçek irradiance (Open-Meteo) geldi ama solar üretim hâlâ sentetik → PR/anomalide gürültü.
- *Dürüst cümle:* "Weather is now real, but solar generation is still synthetic for the demo buildings, so the performance-ratio signal has some noise. With a real inverter feed it's clean."

**9. Demo-bina kimlik çakışması (B003/B005)**
- *Sınır:* Bazı notebook'larda B003/B005 farklı şehir/tip.
- *Dürüst cümle:* (Bunu hocaya söylemene gerek yok — sadece demoda o iki binayı şehir-ismiyle anma.) Roadmap: tek kanonik building registry.

**10. DAX patch sprawl (68 dosya)**
- *Sınır:* DAX 68 artımlı patch dosyasında; tek otoritatif model henüz konsolide değil (PBI-side).
- *Dürüst cümle:* "The measure layer grew as incremental patches; consolidating into a single authoritative TMDL model is a cleanup task — a clean semantic model is itself a sellable artifact."

### 9.4 "Gotcha" sorularına genel taktik
Hoca zor bir soru sorarsa panik yapma. Üç adım:
1. **Kabul et:** "That's a fair point / good question."
2. **Mevcut durumu dürüstçe söyle:** ne yapıyorsun, neden (screening/indicative/modeled).
3. **Roadmap'i ver:** nasıl güçlendireceğin.

Asla uydurma, asla "publicly available so it's fine" deme. Bir akademisyen için **"bilmiyorum ama şöyle bulurum"** > **yanlış kendinden-emin cevap.**
---

## 10. Pazar & Konumlandırma

### 10.1 Problem (hocaya "neden bu iş" hikayesi)
AB ticari binaları, toplam AB enerji tüketiminin **%40'ı** ve CO₂ emisyonlarının **%36'sı**. Ama çoğu portföy hâlâ aylık fatura + Excel ile yönetiliyor — anomalilere, regülasyon riskine, dekarbonizasyon fırsatlarına kör. Bu arada AB regülasyonu hızla sıkışıyor (CRREM 2030, EnEfG, GEG, CSRD, EU 2023/1542). Mülk sahipleri **€10B+/yıl uyumluluk riskiyle** modern enerji-zekâsı aracı olmadan karşı karşıya.

### 10.2 Rakipler (hoca "rakip kim?" derse net cevap)

| Rakip | Konum | EnergyLens'in doldurduğu boşluk |
|---|---|---|
| **Measurabl** | US enterprise, $200M+ fon | Mid-market EU |
| **Aquicore** | US ofisler, $40M | AB regülasyon spesifikleri |
| **Cortexa** | EU enterprise, $30M | Mid-market erişilebilirlik |
| **BuildingIQ** | Enterprise BMS | SaaS fiyatlama, Fabric-native |
| **Honeywell Forge** | Enterprise, dahili | Standalone ürün |
| **Schneider EcoStruxure Resource Advisor** | Akran (denetlenebilir raporlama, benchmarking, AI Copilot) | Biz akranız; bizde çok-protokol IoT + Fabric-native + mid-market fiyat |
| **Siemens Desigo CC / INSIGHT** | BMS (bina otomasyonu) | Biz analitik/zekâ katmanıyız, BMS değil |

> **EnergyLens'in tek cümlelik açısı:** "Microsoft Fabric-native + AB regülasyon nişi + mid-market fiyatlama (€99-699/bina/ay) + Lakehouse üzerinde tool-use ile akıl yürüten bir AI Copilot." Schneider/Siemens'le boşluk: denetlenebilir ESG export, akran benchmarking, M&V — bunlar roadmap'te.

### 10.3 Neden Fabric / mid-market / DACH?
- **Neden Microsoft Fabric?** Mayıs 2024 GA — yeni, uzman havuzu küçük (DP-600/700 sahipleri dünyada on-binler). OneLake lineage CSRD denetimi için biçilmiş kaftan. Sen DP-600 sertifikalısın → nadir konum.
- **Neden mid-market?** Solo founder 6-aylık enterprise satış döngüsünü kaldıramaz. Mid-market + akademik pilotlar 2-8 haftada kapanır. Mid-market SaaS = €17k+ ARR/müşteri, %85 brüt marj.
- **Neden DACH?** En yüksek-değerli enerji-uyumluluk pazarı (EnEfG, GEG, BEG). Berlin merkezli olman + federal Almanya programı (EXIST) için kritik.

### 10.4 TAM / SAM / SOM
- **TAM (AB):** ~5 milyon ticari bina × €100-700/bina/ay → ~€18B/yıl
- **SAM (DACH odak):** ~€4.3B/yıl
- **SOM (3 yıl):** 100-200 müşteri → €1-2M ARR

### 10.5 Fiyatlama (per building per month)
| Tier | Fiyat | Hedef |
|---|---|---|
| Insight | €99/bina/ay | SME ofisler |
| Monitor | €299/bina/ay | Mid-market mülk yönetimi |
| Copilot | €699-1500/bina/ay | Enterprise, healthcare, IoT'lu |
| Portfolio Custom | €5k-50k/ay | 10+ bina portföyleri |

**Unit economics:** CAC €500-1500; LTV (3 yıl) ~€54k; LTV/CAC 36-108x; payback 2-4 ay; %85 brüt marj. Pilot (ilk 3 ay) ücretsiz → referans kazan.

---

## 11. EXIST & Hoca Hikayesi

### 11.1 Mert profili (kendini nasıl anlatacaksın)
- **Eğitim:** B.Sc. Energy Engineering (Yaşar Üniversitesi, İzmir) + M.Sc. Energy Management (BSBI Berlin, Haziran 2026 mezuniyet)
- **Sertifika:** Microsoft **DP-600** (Implementing Analytics Solutions Using Microsoft Fabric) — Microsoft'un en güncel/talep gören sertifikalarından, çok az solo founder'da var
- **Deneyim:** ~1 yıl mühendislik + önceki girişimcilik denemeleri
- **Yürütme:** EnergyLens'in tüm stack'ini (Fabric medallion + 9-sayfa PBI + IoT adapter + batarya simülatörü + web app + AI Copilot) **~5 haftada, solo, uçtan uca** çıkardı
- **Vize:** Mezuniyet sonrası 18-ay Job Search Visa → Almanya'da kalma + UG kurma runway'i

### 11.2 Neden solo bu kadarını yapabildi (hocanın merak edeceği)
İki nadir şeyin kesişimi: **domain (enerji mühendisliği + M.Sc.)** + **modern veri stack (Fabric/DP-600)**. Çoğu BI geliştirici kWh/m²/Scope 2'yi bilmez; çoğu enerji mühendisi medallion/DAX/tool-use bilmez. Mert ikisini birleştirip, AI-destekli geliştirmeyle (Claude/Copilot) hızını katladı. "Küçük takım, büyük iş" hikayesi.

### 11.3 EXIST Gründerstipendium — ne, ne kadar, ne istiyorsun
- **Ne:** Federal Almanya (BMWK) öğrenci/yeni-mezun startup teşviki, üniversite üzerinden yürür.
- **Paket:** ~**€65K / 12 ay** = €30K stipend (yaşam) + €30K material (ekipman/yazılım/danışmanlık) + €5K coaching.
- **Zaman:** Başvuru Tem-Ağu 2026 → karar Eyl 2026-Şub 2027 → başlangıç Q1 2027.
- **Hocadan ZORUNLU olan:** akademik **mentor/supervisor letter** (EXIST bunsuz kabul etmez) + BSBI üniversite commitment letter.
- **Mentor letter ne içerir:** kısaca — projenin akademik temeli (M.Sc. çalışmasından doğdu), founder'ın yeterliliği, üniversitenin desteklediği. Sen taslağını hazırlayıp hocanın onayına sunabilirsin.

### 11.4 Kabul olasılığını artıran / azaltan faktörler
**Artıran:** DP-600 sertifikası, BSBI bağı + hocanın olumlu yanıtı, hazır pitch package + 2 video, DACH pazar derinliği, EU regülasyon nişi, solo yürütme kanıtı.
**Azaltan (ve nasıl yumuşatırsın):** solo founder ("co-founder + advisor + mentor ile ekosistem göster"), Türk vatandaşı ("Almanya'da kalma planı net: Job Search Visa → UG"), pre-incorporation ("12 ay sonunda UG kurma planı somut tarihli"), pilot yok ("BSBI kampüs pilotu aktif görüşmede" — eğer Ağustos öncesi pilot başlarsa kabul olasılığı ~%20 artar).

### 11.5 12 ay planı (onay gelirse)
BSBI pilot → 5 ödeyen müşteri → UG kurulumu → €5-10K MRR. Material bütçesi: Fabric F4-F8 + Power BI Premium + Azure OpenAI + donanım + müşteri kazanımı + hukuki (UG/GDPR) + marka + pilot setup.

---

## 12. ⭐ Hocanın Muhtemel 20 Sorusu + Hazır Cevapların

Sesli prova yap — soruyu oku, cevabı kapatıp kendi sözlerinle söyle, sonra karşılaştır.

**Domain / teknik:**
1. **"EUI'yi nasıl hesaplıyorsun, iklim düzeltmesi var mı?"** → Yıllık kWh / şartlandırılmış m². İklim düzeltmesi ratio metot, HDD+CDD, referans baseline (EN ISO 15927-6, HDD 15°C / CDD 22°C).
2. **"Scope 2 location mı market mı?"** → Her ikisi gerekli (ESRS E1-6). Location-based canlı (yıl-indeksli resmî faktör); market-based mekanizması var, gerçek tedarikçi verisiyle ayrışacak.
3. **"Scope 3'ü nasıl yapıyorsun?"** → Şu an %8 screening, `disclosure_grade=False` etiketli; roadmap: kategori-bazlı aktivite verisi.
4. **"CRREM stranding'i nasıl buluyorsun?"** → Carbon intensity vs tip/bölge 1.5°C pathway kesişimi = stranding yılı. Pathway'ler şu an indikatif (License Partner sonra resmî).
5. **"COP düşünce nasıl alarm veriyorsun, mevsimi nasıl ayırıyorsun?"** → Eşdeğer dış-sıcaklık bandında karşılaştırırım; <0.80 MEDIUM, <0.60 HIGH. Kış düşüşünü arıza sanmam.
6. **"Emisyon faktörlerin nereden, tutarlı mı?"** → Tek referans tablosu, kaynak+URL+yıl. TR=0.442 (TEİAŞ), DE yıl-indeksli (UBA). Eskiden dağınıktı, denetleyip tek kaynağa indirdim.
7. **"Veri gerçek mi sentetik mi?"** → Hava/fiyat/şebeke-CO₂ gerçek (Open-Meteo/ENTSO-E/ElectricityMaps); bina tüketim/solar 10 temsili bina için sentetik (henüz müşteri yok). Pilotla gerçek veri gelir.
8. **"Forecast doğruluğun ne?"** → Prophet, per-building, HDD/CDD+occupancy regressor. MAPE şu an in-sample; client-facing için rolling-origin cross-validation roadmap'te.
9. **"IoT tarafı gerçek mi çalışıyor?"** → Evet, flagship — ASHRAE Guideline 36 AFDD, 12 kural, ~31 sensör tipi, çok-protokol adapter (BACnet/Modbus/MQTT). Statik snapshot demoda canlı; EventStream'le production'da gerçek-zaman.
10. **"Batarya ROI'sı gerçekçi mi?"** → Model yapısı doğru (NPV/IRR/payback); mevcut sayılar üst-sınır (tüm deşarj peak-tarifeyle), saat-bazlı eşleştirmeyle muhafazakârlaştırıyorum.

**Mimari / Microsoft:**
11. **"Neden Microsoft Fabric?"** → OneLake tek veri katmanı = denetlenebilir lineage (CSRD için kritik), DirectLake hız+tazelik, ben DP-600 sertifikalıyım.
12. **"DirectLake nedir?"** → PBI'ın OneLake Parquet'lerini doğrudan okuması — import yok, DirectQuery yok; import hızı + canlı tazelik.
13. **"AI Copilot gerçekten veri mi okuyor yoksa uyduruyor mu?"** → Tool use — 6 tool ile Lakehouse'a/Postgres'e gerçek sorgu atıyor, metin özeti değil. RLS her çağrıda.
14. **"Veri izolasyonu nasıl?"** → 3 katman: RLS (veri), app-nav (modül), subscription (tier). Veri asla müşteri sınırını geçmez.

**İş / EXIST:**
15. **"Rakiplerin kim, farkın ne?"** → Measurabl/Aquicore (US, enterprise), Schneider/Siemens (akran/BMS). Farkım: Fabric-native + AB regülasyon nişi + mid-market + tool-use Copilot.
16. **"Pazar ne kadar büyük?"** → TAM €18B (AB), SAM €4.3B (DACH).
17. **"Bunu tek başına nasıl yaptın?"** → Domain (enerji M.Sc.) + Fabric (DP-600) kesişimi + AI-destekli geliştirme; 5 hafta uçtan uca.
18. **"Benden tam olarak ne istiyorsun?"** → EXIST için akademik mentor letter + BSBI commitment; ve isterse aylık/çeyreklik advisory.
19. **"BSBI'ya ne faydası var?"** → Ücretsiz 6-ay kampüs pilotu (risk yok, RLS'li, ben yönetirim) + M.Sc. capstone + named case study; BSBI sürdürülebilirlik görünürlüğü kazanır.
20. **"Sırada ne var / 12 ayda ne yapacaksın?"** → BSBI pilot → 5 ödeyen müşteri → UG kurulumu → €5-10K MRR; Scope 3/market-based S2/CRREM resmî eğri/sub-metering güçlendirmeleri.

> **Bilmediğin bir soru gelirse:** "That's a great question — I don't have a confident answer right now, but here's how I'd find out…" Bu, uydurmaktan **her zaman** daha iyi.

---

*— Master Referans Dokümanı sonu. İyi çalış, sakin ol, dürüst ol. Hazırsın. — EnergyLens prep*
