# Page 5 — v54 Decision-Support Visual Plan

**Date:** 2026-05-19  
**Sayfa:** `05_occupancy_analysis`  
**Bağlam:** v54 measure deployment sonrası, decision-support layer'ı görselleştir.

---

## 1. Kapsam

v54 ile 4 yeni measure + 1 update'ten sonra Page 5'e **alt-şerit (Row 5)** ekleniyor. Bu şerit sayfayı descriptive'den prescriptive'e taşıyan kritik UX katmanı.

**Mevcut layout (Row 1-4):** korunuyor, dokunulmuyor.

**Yeni Row 5:** 3 KPI card + 1 wide insight text box.

---

## 2. Mevcut Page 5 Layout (referans, değişmeyecek)

```
Row 1 : Title bar + EnergyLens logo + page-nav icons       [y=0,   h=80]
Row 2 : Slicers (Date / Building / Profile / DayName)      [x=0,   w=240, full height]
Row 3 : KPI cards C1-C4                                    [y=80,  h=150]
        - C1 Avg Occupancy Rate (%)
        - C2 Peak Occupancy Hour
        - C3 After-Hours Activity Share %
        - C4 Energy / Occupant (kWh/mo)  [now showing 1545.0, Goal 1200 after v54]
Row 4 : 7x24 Occupancy Heatmap (full width)                [y=240, h=240]
Row 5 : Hourly Weekday/Weekend + Building Avg Bar          [y=490, h=230]
```

**Footer alanı (y=730 sonrası):** boş — Row 6 buraya gelecek.

---

## 3. Yeni Row 6 — Decision-Support Strip

### 3.1 Genel Yerleşim

```
Y baslangic: 740 px (mevcut Row 5'in 10 px altinda)
Yukseklik:   110 px
X baslangic: 260  (slicer column'unun sagindan basla)
Toplam genislik: 1570 px (sayfa kenarina kadar)

┌────────────┬────────────┬────────────┬──────────────────────────────┐
│ C5         │ C6         │ C7         │  T1 - Top Insight            │
│ Ghost Load │ Annual €   │ Occupied   │                              │
│ Risk %     │ Wasted     │ Hrs / Day  │  (prescriptive text)         │
│            │            │            │                              │
│ 280px      │ 280px      │ 280px      │  710px                       │
└────────────┴────────────┴────────────┴──────────────────────────────┘
```

---

### 3.2 Card C5 — Ghost Load Risk %

**Visual type:** Card (new) — NOT "Card (new)" — kullanacağın **Card** (klasik) veya **KPI**.  
Önerim: **Card (klasik)** + altına Text box olarak Status. Çünkü "Card (new)" subtitle binding daha zayıf.

| Property | Value |
|---|---|
| **Visual type** | Card |
| **Value field** | `[Phantom Load Risk Pct]` |
| **Display unit** | None |
| **Decimal places** | 1 |
| **Position** | X=260, Y=740, W=280, H=110 |
| **Background** | Transparent (page background görünür) |
| **Border** | 1px solid `#1F2A2E` (EnergyLens dark teal) |
| **Border radius** | 8px |
| **Title** | "GHOST LOAD RISK" — font: Segoe UI Semibold 11pt, color #8FA8B0, letter-spacing 1px |
| **Data label** | font: Segoe UI Bold 32pt, color: conditional (aşağıda) |
| **Category label** | OFF |

**Conditional formatting for data label color:**

```
Format: Field value
Based on field: [Ghost Load Risk Status]
Rules:
  When value is "Efficient"           → color #2DC653 (green)
  When value is "Review schedule"     → color #F4A261 (amber)
  When value is "Critical ghost load" → color #E63946 (red)
  Default                              → color #8FA8B0 (grey)
```

**Subtitle (Text box overlay):**
- Yeni Text box, C5 card'ının altına yerleştir
- Position: X=260, Y=820, W=280, H=20
- Content: bind to `[Ghost Load Risk Status]`
- Font: Segoe UI Regular 10pt
- Color: same conditional as data label (use Field formatting)
- Horizontal align: Center

---

### 3.3 Card C6 — Annual € Wasted

| Property | Value |
|---|---|
| **Visual type** | Card |
| **Value field** | `[Ghost Load Annual Cost EUR]` |
| **Display unit** | None (format string "€#,##0" zaten measure'da) |
| **Position** | X=550, Y=740, W=280, H=110 |
| **Background** | Transparent |
| **Border** | 1px solid `#1F2A2E` |
| **Border radius** | 8px |
| **Title** | "EST. ANNUAL € WASTED" — font: Segoe UI Semibold 11pt, color #8FA8B0 |
| **Data label** | font: Segoe UI Bold 32pt, color #E63946 (always red — financial waste) |
| **Tooltip** | Manual text: "Estimated annual energy cost from after-hours waste. Assumes 20% baseload factor and €0.20/kWh (DE avg). See methodology in docs/business-logic/kpi-formulas.md" |

**Subtitle Text box (X=550, Y=820, W=280, H=20):**
- Static text: "vs. €0 efficient target"
- Font: Segoe UI Regular 10pt, color #8FA8B0
- Horizontal align: Center

---

### 3.4 Card C7 — Occupied Hours / Day

| Property | Value |
|---|---|
| **Visual type** | Card |
| **Value field** | `[Avg Occupied Hours per Day]` |
| **Display unit** | None |
| **Decimal places** | 1 |
| **Position** | X=840, Y=740, W=280, H=110 |
| **Background** | Transparent |
| **Border** | 1px solid `#1F2A2E` |
| **Border radius** | 8px |
| **Title** | "OCCUPIED HRS / DAY" — font: Segoe UI Semibold 11pt, color #8FA8B0 |
| **Data label** | font: Segoe UI Bold 32pt |
| **Goal indicator** | Subtitle text box ile (aşağıda) |

**Subtitle Text box (X=840, Y=820, W=280, H=20):**
- Bind to: `[Occupied Hours Variance Hours]`
- Format: "+0.0;-0.0;0" (zaten measure'da)
- Prefix metni: "Variance: " (text box içinde manuel ekle)
- Font: Segoe UI Regular 10pt
- Color: conditional
  - When variance < -1.5 → #F4A261 (amber, under-utilized)
  - When variance > +1.5 → #00B4D8 (teal, over-utilized)
  - Otherwise → #2DC653 (green, on-target)
- Horizontal align: Center

**Pro-tip:** Card visual'ında "Goal" field yok (KPI visual'ında var). Eğer KPI visual seçersen direkt `[Occupied Hours Goal]`'u Target field'ına koyarsın ve %-variance otomatik gelir. Ama renk/font kontrolü daha az. **Card öneriyorum, custom subtitle ile.**

---

### 3.5 Text Box T1 — Top Insight (Prescriptive)

Bu sayfanın **en önemli yeni elementi**. Page 5'i decision-support sayfası yapan görsel.

| Property | Value |
|---|---|
| **Visual type** | Text box (Insert -> Text box) — Power BI Desktop standart |
| **Position** | X=1130, Y=740, W=700, H=110 |
| **Background** | Linear gradient #0E1A1F → #1F2A2E (dark teal radial) — alternatif: tam transparent |
| **Border** | 2px solid #00B4D8 (EnergyLens emerald-cyan accent) |
| **Border radius** | 10px |
| **Padding** | 16px all sides |

**Content (3 layered text elements):**

**Layer 1 — Header strip (top 24px):**
```
DECISION INSIGHT                                     [PAGE 4 →]
```
- Sol: "DECISION INSIGHT" — font: Segoe UI Semibold 10pt, color #00B4D8, letter-spacing 1.5px
- Sağ: "PAGE 4 →" — Button visual (görünmez border, transparent bg)
  - Action: Page navigation -> "04_forecast_recommendations"
  - Font: Segoe UI Bold 10pt, color #00B4D8

**Layer 2 — Insight text (middle 50px):**
- Visual type: **Card (klasik)** veya **Text box with measure binding**
- Power BI'da text box static, measure bind etmek için: **Visual type = Card**, kategori label OFF, data label sol-hizalı, wrap on.

| Card properties for insight text | Value |
|---|---|
| **Visual type** | Card |
| **Value field** | `[Occupancy Top Insight]` |
| **Position** | X=1146, Y=770, W=668, H=50 |
| **Background** | Transparent (parent text box rengini görsün) |
| **Border** | None |
| **Title** | OFF |
| **Data label font** | Segoe UI Regular 13pt |
| **Data label color** | conditional (aşağıda) |
| **Word wrap** | ON |
| **Horizontal align** | Left |

**Conditional color rules for insight text:**

```
Format: Field value
Based on field: [Phantom Load Risk Pct]
Rules:
  When value >= 35      → #E63946 (red, critical)
  When value >= 20      → #F4A261 (amber, moderate)
  When value < 20       → #2DC653 (green, healthy)
  When value is BLANK   → #8FA8B0 (grey, no data)
```

**Layer 3 — Footer note (bottom 16px):**
- Static text: "Methodology: 20% baseload assumption, €0.20/kWh DE avg. Stated assumptions: docs/assumptions/stated-assumptions.md"
- Font: Segoe UI Italic 8pt, color #5A6E76
- Position: X=1146, Y=824, W=668, H=16

---

## 4. Cross-Page Navigation (Page 4 Button)

T1 içindeki "PAGE 4 →" button'unun davranışı:

1. **Visual type:** Button (Insert -> Buttons -> Blank)
2. **Action:**
   - Type: **Page navigation**
   - Destination: `04_forecast_recommendations`
3. **State styling:**
   - Default: bg transparent, text #00B4D8
   - Hover: bg rgba(0,180,216,0.15), text #FFFFFF
   - Press: bg #00B4D8, text #0E1A1F

**Bookmark fallback (opsiyonel):**
Eğer Page 4'te Page 5'ten gelen filtreyi korumak istiyorsak:
- Bookmark oluştur: "From Page 5 — Occupancy Insights"
- Slicer state'leri sync et (Date + Building Name)
- Button action: Bookmark -> "From Page 5 — Occupancy Insights"

---

## 5. Renk Paleti Referansı (EnergyLens Brand)

| Token | Hex | Kullanım |
|---|---|---|
| Dark Bg | `#0E1A1F` | Sayfa arka plan |
| Card Surface | `#1F2A2E` | Card border, gradient end |
| Text Primary | `#FFFFFF` | Ana sayılar |
| Text Secondary | `#8FA8B0` | Başlıklar, subtitle |
| Text Muted | `#5A6E76` | Footer notlar, methodology |
| Accent Cyan | `#00B4D8` | Insight border, link, CTA |
| Status Green | `#2DC653` | Efficient / Healthy |
| Status Amber | `#F4A261` | Review / Moderate |
| Status Red | `#E63946` | Critical / Wasted |

Brand standart: `spaces/brand_identity.md` (memory referansı).

---

## 6. Uygulama Sırası (Checklist)

```
[ ] 1. Power BI Desktop'ta .pbix dosyasini ac
[ ] 2. External Tools -> Tabular Editor 2
[ ] 3. C# Script -> page5_v54_install.cs icerigi yapistir
[ ] 4. F5 (Run) -> "Updated: 1, Created: 4" mesajini gor
[ ] 5. TE'de Ctrl+S -> Save
[ ] 6. Power BI Desktop -> Home -> Refresh
[ ] 7. Page 5 -> sayfa altina (y=740) bos alan acildigini dogrula
[ ] 8. Card C5 ekle (Ghost Load Risk %) — section 3.2
[ ] 9. Card C5 subtitle text box ekle (Ghost Load Risk Status)
[ ] 10. Card C6 ekle (Annual EUR Wasted) — section 3.3
[ ] 11. Card C7 ekle (Occupied Hrs/Day + Variance subtitle) — section 3.4
[ ] 12. Text Box T1 cerceve ekle — section 3.5
[ ] 13. T1 icindeki Card (Top Insight) ekle, conditional renk uygula
[ ] 14. Page 4 button ekle (page navigation) — section 4
[ ] 15. Tum filtreleri test et (Building Name = "Frankfurt Klinikum" -> insight degisiyor mu?)
[ ] 16. Page navigation test et (Page 4 butonuna basinca yonleniyor mu?)
[ ] 17. Save .pbix
[ ] 18. Publish to Service (workspace: Energy-Copilot-Platform)
```

---

## 7. Test Senaryoları

Measure'ların farklı bina seçimlerinde doğru tepki verdiğini doğrula:

| Bina Seçimi | Beklenen C5 (Ghost Load %) | Beklenen C6 (€/yr) | Beklenen T1 |
|---|---|---|---|
| All (portfolio) | 30-50% | €1,000-3,500 | "MODERATE after-hours waste..." veya "CRITICAL..." |
| Berliner Bürogebäude (ofis) | < 20% | €100-400 | "Healthy utilization pattern..." |
| Frankfurt Klinikum (healthcare) | 45-65% | €2,000-5,000 | "CRITICAL ghost load..." (healthcare = 24/7, beklenen) |
| Hamburg Logistics | 25-40% | €500-1,500 | "MODERATE after-hours waste..." |

**Healthcare için not:** 24/7 operasyon doğal, "critical" görünmesi normal. Eğer her healthcare binasında critical alarmı saçmaysa (false positive), v55'te bina tipine göre threshold ayarlanmalı (Healthcare için 50%/70% kullan).

---

## 8. Backlog (v55+)

- [ ] Country-specific `eur_per_kwh` (DE 0.20 / TR 0.14 / AT 0.25)
- [ ] Building-type-specific phantom load thresholds (Healthcare için 50/70)
- [ ] MoM occupancy trend (gold_kpi_daily'de occupancy_pct varsa)
- [ ] Tooltip page on C5/C6/C7 cards (tooltip_page_master_plan'den gelecek)
- [ ] Page 4'e "From Page 5" bookmark + filtered landing state
- [ ] Notebook fix: 08_occupancy_prediction.py OPTIMIZE IF EXISTS — fallback measure'ları kaldır

---

**Bu plan repo'ya commit edildikten sonra Power BI'da uygulanır. Her adım yapıldıkça checklist'i güncelle.**
