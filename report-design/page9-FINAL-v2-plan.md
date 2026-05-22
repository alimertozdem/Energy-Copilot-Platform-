# PAGE 9 — Final Action Plan v2
**Battery Dispatch & Financial Simulation**
Last updated: 2026-05-09 | DAX active: v47 base + v50 C1/C2/C3 fix + v51 patch

---

## DURUM: Ne Çalışıyor, Ne Bozuk

### ✅ Çalışıyor (dokunma)
| Görsel/Ölçü | Durumu | Not |
|---|---|---|
| C1 Annual Savings | ✅ | Binaya göre değişiyor (Frankfurt=37k, Hamburg=100k) |
| C2 Payback Years | ✅ | Değer geliyor, C2 Label ✓⚠✗ gösteriyor |
| C3 CO2 Avoided | ✅ | Binaya göre değişiyor |
| V2 Monthly Charge/Discharge | ✅ | Bar + line chart, aylık verileri doğru |
| V1 SoC Monthly Trend | ✅ | Veri doğru (aşağıda açıklama) |
| V3 Scenario Table | ✅ (küçük sorun) | Çoklu strateji satırları görünüyor |
| CAPEX vs Payback Scatter | ✅ | Balonlar görünüyor |

### ❌ Düzeltilecek (5 adım)
| Sorun | Sebep | Çözüm |
|---|---|---|
| V4 ROI Gauge bozuk | Dispatch €37k / Simulation €387k = %9 → hep boş | DAX yeniden yaz (payback-based) |
| EU Compliance kartı yok | Kullanıcı sildi | Yeniden ekle |
| Sol panel "See details" kartlar | TOPN direct lake'te çalışmıyor | Sade DAX + kart yeniden ekle |
| C4 format 0.94 gösteriyor | Sadece format ayarı | Modeling → Percentage |
| V3 boş satır | Veri: kWh=0 olan sahte satır | Visual filter ekle |

---

## ADIM 1 — v51 DAX Patch (4 ölçü)

**Dosya:** `semantic-model/62_dax_v51_final_fixes.dax`

Önce sil (varsa):
- `[V4 ROI Gauge Pct]`
- `[V4 ROI Status Label]`
- `[EU Compliance Portfolio Label]`
- `[Active Strategy Short Label]`

Sonra 4'ünü de Modeling → New Measure ile yapıştır.

**Yeni V4 mantığı (neden daha iyi):**
```
Payback 1.5 yr → Skor 87.5% → Gauge dolu  ✅
Payback 7 yr   → Skor 41.7% → Gauge orta
Payback 12 yr  → Skor 0%    → Gauge boş   ✅
```
Enerji yöneticisi için anlaşılır: kısa geri ödeme = iyi skor.

---

## ADIM 2 — C4 Format (DAX yok)

Modeling sekmesi → `[C4 Round Trip Efficiency Pct]` ölçüsüne tıkla
→ **Format = Percentage** → **Decimal places = 1**

Sonuç: 0,94 → **94,0%** (LFP Hamburg), 0,90 → **90,0%** (NMC Frankfurt)

---

## ADIM 3 — Sol Panel Kartları Yeniden Kur

**Sil:** "See details" gösteren 2 kart (X butonuna bas)

**Ekle — Kart 1 (Active Strategy):**
- Insert → Card (new)
- Value: `[Active Strategy Short Label]`
- Subtitle: `[Page9 Data As Of]`
- Pozisyon: sol panel orta bölge

**Ekle — Kart 2 (Battery Status):**
- Insert → Card (new)
- Value: `[Active Battery Label]`
- Subtitle: `[EU Compliance Portfolio Label]`
- Pozisyon: sol panel, strateji kartının altı

---

## ADIM 4 — V4 Gauge Ayarları

Gauge visuala tıkla → Format Visual:
- **Value** → `[V4 ROI Gauge Pct]`
- **Minimum** → 0
- **Maximum** → 100
- **Target value** → 42 (7 yıllık eşik = iyi yatırım sınırı)
- **Callout value** → `[V4 ROI Status Label]`
- **No data message** → "No data" (veya boşalt)

---

## ADIM 5 — V3 Boş Satır Filtresi

V3 tablosuna tıkla → Filters bölmesi → "Add data field to filter"
→ `gold_battery_simulation[battery_capacity_kwh]` → **is greater than 0** → Apply

---

## GÖRSELLERİN NE ANLATTIKLARI (Enerji Yöneticisi için)

| Görsel | Soru cevaplıyor | Nasıl okumak |
|---|---|---|
| **C1 Annual Savings** | "Yıllık ne kadar tasarruf ediyorum?" | Yüksek = iyi. Bina + strateji filtresiyle değişir |
| **C2 Payback Period** | "Ne zaman amorti olur?" | Düşük = iyi. 7 yıl altı = yeşil ✓ |
| **C3 CO2 Avoided** | "Karbon ayak izime katkısı ne?" | Yüksek = iyi. ESG raporlama için |
| **C4 Efficiency + EU** | "Batarya sağlıklı mı, uyumlu mu?" | 90%+ = normal. LFP>NMC. EU ✓ = satışa uygun |
| **V2 Charge/Discharge** | "Batarya ne zaman ne kadar dolup boşalıyor?" | Yazın PV şarj yüksek, kışın grid şarj artar |
| **V1 SoC Trend** | "Batarya doluluk seviyesi ay ay nasıl?" | Min SoC çizgisinin üstünde kalmalı |
| **V3 Scenario Table** | "Hangi strateji en iyisi?" | Score > 80 = yeşil, Payback en düşük = önerilen |
| **CAPEX vs Payback** | "Hangi yatırım makul fiyat/süre dengesinde?" | Sol alt köşe = ucuz + hızlı geri dönüş |
| **V4 ROI Gauge** | "Yatırım kalitesi bir bakışta" | Yüksek = kısa geri ödeme = iyi |

---

## SOC GRAFİĞİ NEDEN 20–25% ARALIĞINDA?

Bu bir hata değil, Peak-Shaving stratejisinin normal davranışı:
- Sabah: batarya PV ile veya gece tarifesiyle **%80'e şarj**
- Öğlen zirve saatlerinde: **%20'ye kadar boşalt** (şebeke alımını azalt)
- Gün sonu ortalama SoC: **%20–25** → grafik bu ortalamayı gösteriyor

**Grafik aylık ortalama gösteriyor** (günlük değil). Aylık ortalama
her zaman günlük döngünün orta noktasına yakın olacak.

Strateji filtresi S2'den "Self-Consumption" seçersen SoC daha yüksek
ve daha stabil görünecek (PV üretimini önce bataryaya doldurup akşam kullanım).

---

## EKSİK GÖRSEL ÖNERİSİ — Aylık Net Tasarruf Trendi

Şu an sayfada "ne zaman en çok tasarruf ediliyor?" sorusu cevapsız.
Bu görseli eklemek sayfayı çok daha anlamlı yapar:

**Görsel:** Line chart
**Başlık:** "Monthly Net Savings (€)"
**X-axis:** `gold_battery_dispatch[month_year_en]` (Categorical)
**Y-axis:** `[V2 Net Savings EUR Daily]` (SUM, aylık toplam)
**Legend:** `gold_battery_dispatch[strategy]`
**Pozisyon:** V1 SoC Trend yerine veya yanına

**Enerji yöneticisine ne söyler:**
- Yaz aylarında (PV yüksek) tasarruf nasıl artıyor?
- Hangi strateji hangi mevsimde daha iyi çalışıyor?
- Tasarruf trendi yukarı mı gidiyor (iyi) yoksa sabit mi?

Bu görsel V2 (kWh miktarı) ile birlikte okunduğunda güçlü:
V2 = "ne kadar enerji aktardım", Yeni = "bundan ne kadar para kazandım"

---

## C1 vs V3 FARK AÇIKLAMASI (beklenen durum)

Enerji yöneticisi "C1 ile V3 neden aynı değil?" diye sorabilir.

| | C1 Annual Savings | V3 Savings/yr |
|---|---|---|
| **Kaynak** | `gold_battery_dispatch` (günlük dispatch) | `gold_battery_simulation` (ön hesap) |
| **Hesap** | Günlük ortalama × 365 | Senaryo optimizatörü projeksiyonu |
| **Ne gösterir** | Simülasyonun gerçek performansı | Teorik maksimum potansiyel |
| **Neden farklı** | Tüm stratejilerin ortalaması | Tek senaryo, optimistik |

C1 her zaman V3'ten düşük olabilir çünkü C1 tüm strateji
dönemlerini ve geçiş dönemlerini içerir, V3 ise tek senaryo projektsiyon.
**Bu tasarım gereğidir, hata değil.**

---

## REFERANS DOSYALAR

| Dosya | Amaç |
|---|---|
| `semantic-model/58_dax_v47_page9_battery.dax` | 32 temel ölçü (base) |
| `semantic-model/61_dax_v50_comprehensive_fix.dax` | C1, C2, C3, V4 Target, Active Battery fix |
| `semantic-model/62_dax_v51_final_fixes.dax` | ⬅ ŞİMDİ UYGULA: V4 gauge, EU label, Active Strategy |

---

## BEKLENEN FINAL GÖRÜNÜM

```
Frankfurt seçili, S2 = All:
  C1: 36.990 €/yr     C2: 1,5 yr ✓    C3: 60,9 tCO₂    C4: 90,0% ✗ NON-EU
  Sol kart: — Select strategy (S2) —
  Batarya kart: NMC · 400 kWh
  EU kart: 1 NON-COMPLIANT · EU 2023/1670
  V4 Gauge: ~87% (Excellent ROI — payback 1.5yr)
  V3: 3 satır (Self-Consumption, Peak-Shaving, Backup)

Frankfurt seçili, S2 = backup:
  C2: 1,5 yr ✓
  Sol kart: ● Backup + Opportunistic
  V4 Gauge: ~87%

Hamburg seçili, S2 = All:
  C1: 99.977 €/yr     C2: 2,0 yr ✓    C3: 137,5 tCO₂   C4: 94,0% ✓
  Batarya kart: LFP · 5.600 kWh
  EU kart: All batteries EU-compliant ✓
  V3: 1 satır (Peak-Shaving)
```
