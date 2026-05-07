# Energy Copilot Platform — Rapor Tasarım Rehberi

> Bu rehber Power BI raporunu arka planlarla birlikte nasıl kuracağını ve her görseli nasıl optimize edeceğini adım adım açıklar.

---

## 1. Dosya Yapısı

```
report-design/
├── backgrounds/
│   ├── 01_portfolio_overview.png       ← Sayfa 1 arka planı
│   ├── 02_building_detail.png          ← Sayfa 2 arka planı
│   ├── 03_anomalies_alerts.png         ← Sayfa 3 arka planı
│   ├── 04_forecast_recommendations.png ← Sayfa 4 arka planı
│   ├── 05_occupancy_analysis.png       ← Sayfa 5 arka planı
│   └── 06_sustainability_compliance.png← Sayfa 6 arka planı
├── theme/
│   └── EnergycopilotTheme.json         ← Power BI tema dosyası
└── DESIGN_GUIDE.md                     ← Bu dosya
```

---

## 2. Power BI Desktop Kurulum Adımları

### Adım 1 — Temayı Yükle
1. Power BI Desktop'ı aç
2. **View** → **Themes** → **Browse for themes**
3. `EnergycopilotTheme.json` dosyasını seç
4. Tüm renk/font ayarları otomatik uygulanır

### Adım 2 — Canvas Boyutunu Ayarla
Her sayfa için:
1. Sayfaya sağ tıkla → **Page settings**
2. **Type:** Custom
3. **Width:** 1280 &nbsp;&nbsp; **Height:** 720
4. **Wallpaper:** None &nbsp;(arka planı ayrıca ekleyeceğiz)

### Adım 3 — Arka Planı Her Sayfaya Ekle
Her sayfa için:
1. **Format** panel → **Page background**
2. **Image:** Sayfaya ait PNG'yi seç (`01_portfolio_overview.png` vs.)
3. **Image fit:** Fit (Sığdır)
4. **Transparency:** **0%** ← çok önemli, görünsün diye
5. **Color:** siyah veya `#040A18`

### Adım 4 — Görsellerin Arka Planını Kaldır
Her görseli seçip **Format** → **Background** → **Transparency: 100%**
Böylece görseller saydam olur ve arka plan panelleri görünür.

### Adım 5 — Görsel Başlıklarını Kapat (isteğe bağlı)
Tasarımda başlıklar arka plana gömülü. Görsellerde:
**Format** → **Title** → **Off**
Veya başlık metnini koru ama arka planı transparan yap.

---

## 3. Renk Paleti

### Ana Renkler
| Renk | Hex | Kullanım |
|------|-----|----------|
| **Arkaplan Koyu** | `#040A18` | Sayfa arka planı |
| **Panel** | `#0A1528` | Görsel arka planları |
| **Sidebar** | `#050D1C` | Filtre bölgesi |
| **Header** | `#060E24` | Tablo başlıkları, slicer header |
| **Border** | `#1E2D5F` | Kenarlıklar |

### Veri Renkleri (Grafiklerde Kullan)
| Sıra | Renk | Hex | Ne İçin |
|------|------|-----|---------|
| 1 | **Electric Blue** | `#00C8FF` | Ana metrik, tüketim çizgisi |
| 2 | **Mint Green** | `#00E5A0` | Pozitif, solar, tasarruf |
| 3 | **Purple** | `#A064FF` | Tahmin/forecast |
| 4 | **Amber** | `#FFC107` | Doluluk/occupancy, uyarı |
| 5 | **Orange** | `#FF6B35` | Anomali, kritik |
| 6 | **Bright Green** | `#00D264` | CO2 tasarrufu, sürdürülebilirlik |
| 7 | **Light Blue** | `#4DB8FF` | İkincil enerji serisi |
| 8 | **Red** | `#FF4560` | Kritik hata, kırmızı alert |
| 9 | **Soft Purple** | `#7B61FF` | Tahmin alt/üst bant |
| 10 | **Gold** | `#FFD166` | Ek vurgu |

### Sayfa Bazlı Vurgu Renkleri
| Sayfa | Accent | Hex |
|-------|--------|-----|
| Portfolio Overview | Electric Blue | `#00C8FF` |
| Building Detail | Mint Teal | `#00E5B4` |
| Anomalies & Alerts | Alert Orange | `#FF6432` |
| Forecast & Rec. | Purple | `#A064FF` |
| Occupancy | Amber | `#FFC107` |
| Sustainability | Bright Green | `#00D264` |

---

## 4. Yazı Tipi Hiyerarşisi

| Element | Font | Boyut | Renk |
|---------|------|-------|------|
| KPI Değeri (büyük sayı) | Segoe UI Semibold | 28-36px | `#FFFFFF` |
| Grafik başlığı | Segoe UI Semibold | 12-14px | `#FFFFFF` |
| Eksen etiketleri | Segoe UI | 10px | `#4A6E96` |
| Legend | Segoe UI | 10px | `#7DB4DC` |
| Tablo header | Segoe UI Semibold | 11px | `#7DB4DC` |
| Tablo değerleri | Segoe UI | 10px | `#C8DCF0` |
| Slicer başlık | Segoe UI Semibold | 10px | `#7DB4DC` |
| Slicer öğeler | Segoe UI | 10px | `#C8DCF0` |
| Tooltip başlık | Segoe UI Semibold | 11px | `#FFFFFF` |

---

## 5. Görsel Yerleşim Koordinatları

Canvas: **1280 × 720 px** (piksel cinsinden)

### Her Sayfada Ortak Bölgeler
| Bölge | X | Y | Genişlik | Yükseklik |
|-------|---|---|----------|-----------|
| Sol sidebar (filtreler) | 0 | 68 | 200 | 652 |
| Header bar | 0 | 0 | 1280 | 68 |
| İçerik alanı başlangıcı | 210 | 76 | 1062 | — |
| Footer | 0 | 686 | 1280 | 34 |

### Sayfa 1 — Portfolio Overview
| Görsel | X | Y | G | Y |
|--------|---|---|---|---|
| KPI kart 1-5 | 212–1272 | 78 | ~210 her biri | 92 |
| Bar Chart (bina karşılaştırma) | 212 | 180 | 636 | 238 |
| Donut Chart (bina tipi) | 852 | 180 | 420 | 238 |
| Line Chart (aylık trend) | 212 | 428 | 578 | 228 |
| Map (coğrafi) | 798 | 428 | 474 | 228 |

### Sayfa 2 — Building Detail
| Görsel | X | Y | G | Y |
|--------|---|---|---|---|
| KPI kart 1-6 | 212–1272 | 78 | ~175 her biri | 80 |
| Line+Temp Chart | 212 | 168 | 695 | 160 |
| Gauge (EUI) | 911 | 168 | 361 | 160 |
| Solar Stacked Bar | 212 | 338 | 529 | 172 |
| Battery Area Chart | 745 | 338 | 527 | 172 |
| HDD Scatter | 212 | 520 | 529 | 138 |
| CDD Scatter | 745 | 520 | 527 | 138 |

### Sayfa 3 — Anomalies & Alerts
| Görsel | X | Y | G | Y |
|--------|---|---|---|---|
| Alert KPI 1-5 | 212–1272 | 78 | ~210 her biri | 92 |
| Anomaly Table | 212 | 180 | 636 | 260 |
| Donut (tip dağılımı) | 852 | 180 | 420 | 260 |
| Stacked Col (aylık) | 212 | 452 | 529 | 206 |
| 100% Stacked Bar (bina) | 745 | 452 | 527 | 206 |

### Sayfa 4 — Forecast & Recommendations
| Görsel | X | Y | G | Y |
|--------|---|---|---|---|
| Forecast KPI 1-3 | 212–1272 | 78 | ~350 her biri | 78 |
| Line+CI Chart | 212 | 166 | 636 | 188 |
| MAPE Bar Chart | 852 | 166 | 420 | 188 |
| **Ayırıcı çizgi** | 212 | 362 | 1060 | 2 |
| Rec KPI 1-4 | 212–1272 | 374 | ~260 her biri | 78 |
| Rec Table | 212 | 462 | 529 | 196 |
| Scatter (payback/saving) | 745 | 462 | 527 | 196 |

### Sayfa 5 — Occupancy Analysis
| Görsel | X | Y | G | Y |
|--------|---|---|---|---|
| Occupancy KPI 1-4 | 212–1272 | 78 | ~265 her biri | 90 |
| Matrix Heatmap (7×24) | 212 | 180 | 1060 | 260 |
| Clustered Bar (bina) | 212 | 452 | 529 | 206 |
| Line Chart (saatlik) | 745 | 452 | 527 | 206 |

### Sayfa 6 — Sustainability & Compliance
| Görsel | X | Y | G | Y |
|--------|---|---|---|---|
| ESG KPI 1-5 | 212–1272 | 78 | ~210 her biri | 90 |
| CO2 Line Trend | 212 | 180 | 582 | 240 |
| Country Bar | 798 | 180 | 474 | 240 |
| HDD/CDD Column | 212 | 430 | 529 | 228 |
| Treemap (emisyon) | 745 | 430 | 527 | 228 |

---

## 6. Görsel Başına Ayar Tablosu

### KPI Kartları
```
Background: Transparency 100%
Border: Off
Title: Off
Data Label: White, 28pt, Bold
Category Label: #7DB4DC, 10pt
```

### Çizgi Grafikleri
```
Background: Transparency 100%
Line width: 2px, Smooth: On
Data colors: Tema paletinden (#00C8FF birincil)
X/Y eksen: #4A6E96, 10pt
Gridlines: #0E1E38
Legend: Top, #7DB4DC
Markers: Off (daha temiz görünüm için)
```

### Tablolar
```
Background: Transparency 100%
Header: #7DB4DC, Bold, #060E24 bg
Row padding: 6px
Banded rows: #070F20
Grid: Yalnızca yatay, #0E1E38
```

### Slicerlar (Sol Sidebar'a Yerleştir)
```
Background: #050D1C, 5% transparan
Border: #1E2D5F, 1px, Radius 4px
Header: Bold, #7DB4DC
Item font: #C8DCF0, 10pt
Her slicer: X=8, Genişlik=184
```

---

## 7. Koşullu Biçimlendirme (Conditional Formatting)

### Anomaly Severity Renkleri
| Değer | Renk |
|-------|------|
| critical | `#FF4560` |
| high | `#FF6B35` |
| medium | `#FFC107` |
| low | `#00E5A0` |

### Öneri Priority Renkleri
| Değer | Renk |
|-------|------|
| Critical | `#FF4560` |
| High | `#FF6B35` |
| Medium | `#FFC107` |
| Low | `#00C8FF` |

### KPI Trend Okları (Tüketim)
- Azalma ↓ → `#00E5A0` (iyi)
- Artış ↑ → `#FF4560` (kötü)

### MAPE Renklendirme (Forecast kalitesi)
| Aralık | Renk |
|--------|------|
| < 10% | `#00E5A0` — Mükemmel |
| 10–20% | `#FFC107` — İyi |
| > 20% | `#FF4560` — Zayıf |

---

## 8. Tooltip Ayarları

Her görsele özel tooltip sayfası oluştur:
1. Yeni sayfa ekle → **Page type: Tooltip**
2. Boyut: 320×240 px
3. Aynı dark tema arka planını kullan
4. İlgili detay measure'ları ekle
5. Görselden **Format → Tooltip → Type: Report page** → tooltip sayfasını seç

---

## 9. RLS Test Etme (Müşteri Görünümü)

1. Power BI Desktop → **Modeling** → **View as Roles**
2. `building_viewer` rolünü seç
3. Müşterinin göreceği filtrelenmiş veriyi simüle eder
4. Building adını gir → sadece o binanın verisini görürsün

---

## 10. Publish & Embed Akışı

```
Power BI Desktop
  ↓ Publish
Fabric Workspace (EnergycopilotWorkspace)
  ↓ Rapor + Semantic Model bağlantısı
Power BI Embedded (müşteri uygulaması)
  ↓ Embed token (building_id bazlı RLS)
Müşteri tarayıcısı — sadece kendi binasını görür
```
