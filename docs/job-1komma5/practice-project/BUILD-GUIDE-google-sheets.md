# Build guide — build the unit-economics model yourself in Google Sheets

The finished workbook is in `output/unit_economics_model.xlsx`. **Build it once from scratch anyway.** You will not remember a file you were given; you will remember a model you built. Budget 45–60 minutes.

> **TR:** Bitmiş dosya elinde ama bir kez sıfırdan kur. Verilen dosyayı hatırlamazsın, kurduğun modeli hatırlarsın. 45–60 dakika.

---

## Step 0 · Open the finished file first, then close it

Upload `unit_economics_model.xlsx` to Google Drive → right-click → *Open with* → *Google Sheets*. Look at the seven tabs for two minutes so you know where you are going. Then close it and open a blank sheet.

**Note on conversion:** all formulas convert cleanly. The one thing that does not exist in Google Sheets is Excel's *Data Table* feature — which is why tab `04_Sensitivity` is built as an explicit formula grid. That is the correct approach in Sheets, not a workaround.

---

## Step 1 · Seven tabs, named in this order

```
01_README   02_Inputs   03_Model   04_Sensitivity   05_SQL_Actuals   06_Dashboard   07_Checks
```

Number them. In a shared sheet, tab order is documentation.

---

## Step 2 · `02_Inputs` — the only place you are allowed to type a number

Four columns: **Driver | Value | Unit | Source/note**.

Fill column B with a **yellow background** (`Format → Fill colour`). From now on the rule is absolute: *yellow means input, anything else is a formula*. When someone hands you a model, the first thing you check is whether this rule was respected.

Enter these, grouped with section headers:

| Driver | Value | Unit |
|---|---:|---|
| Annual consumption | 9500 | kWh/yr |
| PV capacity | 10 | kWp |
| Specific yield | 980 | kWh/kWp/yr |
| Eigenverbrauchsquote, PV only | 0.30 | share |
| Eigenverbrauchsquote uplift, battery | 0.28 | share |
| Autarkiegrad cap, PV only | 0.30 | share |
| Autarkiegrad uplift, battery | 0.30 | share |
| Battery usable capacity | 10 | kWh |
| Controllable capacity for VPP | 8 | kW |
| Average day-ahead spot | 8.81 | ct/kWh |
| Realised/average price ratio | 0.987 | x |
| Supplier markup on spot | 1.80 | ct/kWh |
| Base fee, dynamic tariff | 12.99 | EUR/month |
| HEMS software fee | 9.90 | EUR/month |
| Grid fee (Netzentgelt) | 9.26 | ct/kWh |
| Levies + taxes | 12.61 | ct/kWh |
| VAT | 0.19 | share |
| Fixed tariff energy component | 15.40 | ct/kWh |
| Customer acquisition cost | 420 | EUR |
| Service + billing cost | 28 | EUR/yr |
| Imbalance cost | 0.35 | ct/kWh |
| Flexibility revenue | 18 | EUR/kW/yr |
| Annual churn | 0.12 | share |

**Column D is not optional.** Every row gets a source, and where there is no source it says `ASSUMPTION`. The interview question "where did that number come from?" has to have an answer on the sheet, not in your memory.

> **TR:** Sadece sarı hücrelere yazılır. Her satırda birim ve kaynak olacak; kaynağı yoksa açıkça "ASSUMPTION" yazacak. "Bu sayı nereden geldi?" sorusunun cevabı sayfada duracak, aklında değil.

### Optional upgrade: named ranges
Select B4 → `Data → Named ranges` → call it `annual_kwh`. Then your formulas read `=annual_kwh*...` instead of `=02_Inputs!$B$4`. Much more readable, and it is what separates a model someone else can audit from one only you can.

---

## Step 3 · `03_Model` — five blocks, in this order

Structure matters more than the numbers. Use dark header rows for each block.

### Block 1 — Volumes
```
PV generation            = PV capacity * Specific yield
Eigenverbrauchsquote     = EVQ_PV_only + IF(battery>0, EVQ_uplift, 0)
Autarkiegrad cap         = Autarkie_PV_only + IF(battery>0, Autarkie_uplift, 0)
Self-consumed PV         = MIN( PV generation * Eigenverbrauchsquote ,
                                Annual consumption * Autarkiegrad cap )
Grid import              = Annual consumption - Self-consumed PV
PV export                = MAX( PV generation - Self-consumed PV , 0 )
```

**Read the `Self-consumed PV` line twice.** There are **two** binding constraints and you need both:
- how much of your *generation* you can use on site (Eigenverbrauchsquote), and
- how much of your *load* solar can physically cover (Autarkiegrad).

My first version capped only by total consumption. Result: grid import of **zero** — a household that buys no electricity, which is impossible, because PV does not generate at night. The Checks tab now catches exactly this.

> **TR:** Bu satırda **iki** kısıt var: üretimin ne kadarını yerinde kullanabildiğin (Eigenverbrauchsquote) ve yükünün ne kadarını güneşin fiziksel olarak karşılayabildiği (Autarkiegrad). İlk versiyonumda sadece tüketimle sınırlamıştım ve şebeke ithalatı **sıfır** çıktı — imkânsız, çünkü PV geceleri üretmiyor.

### Block 2 — Price stack (this is the block that matters)
```
Customer effective spot      = Average spot * Realised/average ratio
Dynamic energy component     = Customer effective spot + Supplier markup
Non-commodity component      = Grid fee + Levies and taxes
Dynamic price, gross         = (Dynamic energy + Non-commodity) * (1 + VAT)
Fixed price, gross           = (Fixed energy comp + Non-commodity) * (1 + VAT)
Commodity share of net price = Dynamic energy / (Dynamic energy + Non-commodity)
Max saving from a 30% shift  = 0.3 * Commodity share of net price
```
Format the last two as percentages and make them bold. `Commodity share of net price` should land near **32–33%**. That single cell is the reason a "30% cheaper" claim is never true.

Note the use of the **realised/average ratio** rather than the plain average spot. A customer's *volume-weighted* price is what they actually pay. Using the simple average silently assumes flat consumption, which no household has.

> **TR:** Bu blokta iki şeye dikkat: (1) `Commodity share` ~%32-33 çıkmalı — "%30 indirim" iddiasının neden imkânsız olduğunun kanıtı; (2) düz ortalama spot değil **hacim-ağırlıklı** fiyat kullanılıyor. Düz ortalama, tüketimin sabit olduğunu varsayar — hiçbir hanede öyle değil.

### Block 3 — Customer bill
```
Annual bill dynamic = Grid import * Dynamic price gross / 100 + Base fee * 12
Annual bill fixed   = Grid import * Fixed price gross  / 100 + Base fee * 12
Saving vs fixed     = Annual bill fixed - Annual bill dynamic
Saving vs fixed %   = Saving / Annual bill fixed
```
The `/100` converts ct to EUR. Put the unit in every label so you never lose track — ct/kWh vs EUR/kWh errors are a factor of 100 and they do happen.

### Block 4 — Supplier P&L
```
Energy margin        = Grid import * Supplier markup / 100
Base fee revenue     = Base fee * 12
Software revenue     = Software fee * 12
Flexibility revenue  = Flex rate * Controllable capacity
Total revenue        = SUM of the four above
Imbalance cost       = -Grid import * Imbalance cost / 100
Service cost         = -Service cost input
Total cost           = SUM of the two above
Gross margin         = Total revenue + Total cost
```
Costs are entered as **negative numbers** and summed, never subtracted. Sign conventions inside formulas are where models go wrong.

Notice that flexibility revenue scales with **kW**, not kWh. Energy margin scales with kWh. Two different businesses in one P&L — say that out loud if asked.

### Block 5 — Return on acquisition
```
CAC payback (months)    = CAC / (Gross margin / 12)
Expected customer life  = 1 / Annual churn
Lifetime value          = Gross margin * Expected customer life
LTV / CAC               = Lifetime value / CAC
```
LTV here is **undiscounted**. If someone asks, the honest answer is: "a real model would NPV this at our cost of capital; over an 8-year life that materially reduces LTV." Knowing the limitation of your own model is worth more than hiding it.

---

## Step 4 · `04_Sensitivity` — two formula grids

Google Sheets has no Data Table, so build the grid explicitly. Put the varying input in the **row header (column A)** and the second one in the **column header (row 6)**, then write one formula in the top-left cell that recomputes the whole chain, using `$` correctly:

- row header reference: `$A7` (column locked, row floats)
- column header reference: `B$6` (row locked, column floats)
- everything else: fully absolute, e.g. `'02_Inputs'!$B$14`

Then drag it across and down. If your `$` are right, one formula fills the whole grid.

**Grid 1 — Supplier LTV/CAC.** Rows = markup 0.8 → 3.6 ct/kWh. Columns = churn 6% → 20%.
**Grid 2 — Customer saving %.** Rows = average spot 4 → 18 ct/kWh. Columns = realised/average ratio 0.90 → 1.10.

Read grid 2 and find the row where the numbers turn negative. That is your **break-even**: with a 15.40 ct fixed component and a 1.80 ct markup, dynamic stops winning at an average spot around **13.6 ct/kWh**. You should be able to state this from memory.

> **TR:** Sheets'te Data Table yok, bu yüzden ızgarayı formülle kur. Püf noktası `$` yerleşimi: satır başlığı `$A7`, kolon başlığı `B$6`, gerisi tam absolute. Doğru yaparsan tek formül tüm ızgarayı doldurur. Grid 2'de sayıların negatife döndüğü satır **başabaş noktan** — ~13,6 ct/kWh. Bunu ezbere söyleyebilmelisin.

---

## Step 5 · `05_SQL_Actuals` — the handoff from SQL to Sheets

Paste the output of `gold_customer_summary` here, plus three **measured scalars** at the top: average spot, commodity share, realised/average ratio.

**Why scalars and not volumes:** the observed window is February–April, which is heating-heavy and low-solar. Annual volume cannot reconcile against a 90-day winter sample and pretending otherwise is dishonest. A *price average* reconciles exactly. Choose the thing that can legitimately be reconciled, and say why you chose it.

> **TR:** Modeli ölçülmüş **skalerlere** bağla, yıllıklandırılmış hacimlere değil. Gözlem penceresi Şubat–Nisan: ısıtma ağırlıklı, güneş az. Yıllık hacim 90 günlük kış örneğiyle mutabık kalamaz. Ama fiyat ortalaması tam mutabık kalır. Mutabık kalabilecek şeyi seç ve *neden* seçtiğini söyle.

---

## Step 6 · `06_Dashboard` — six numbers and four traffic lights

Large-font cells referencing `03_Model`. Nothing computed here — a dashboard that calculates is a dashboard nobody can audit.

Traffic lights with `IF()`:
```
=IF(LTV_CAC >= 3, "GREEN", "AMBER")
=IF(CAC_payback <= 18, "GREEN", "AMBER")
=IF(Saving > 0, "GREEN", "RED — do not sell this")
```
Add a bar chart from the segment backtest (`Insert → Chart → Column`).

---

## Step 7 · `07_Checks` — try to break your own model

Four columns: **Check | Result | Verdict | Why it matters**. Each verdict is an `IF()` returning `PASS` or `CHECK`.

Write at least these nine:

1. Volume identity: `import + self-consumed − consumption = 0`
2. Self-sufficiency below 85% — catches the impossible-autarky bug
3. Grid import is positive — a customer with no import generates no energy margin
4. Commodity share between 25% and 45% — outside this band a fee input is wrong
5. Saving below 30% — anything higher on a German bill is almost always a modelling error
6. Gross margin positive
7. Flexibility revenue is under 70% of total revenue — if the case rests on the least certain input, say so
8. Input spot price matches the measured pipeline within 2%
9. Commodity share matches the measured pipeline within 3 percentage points

**The rule:** if any verdict reads `CHECK`, the model is not presentable. Fix it, or put the caveat in the *first sentence* of your memo — never in a footnote.

> **TR:** Bu sekme modelin kendi kendini denetlemesi. Her satır `PASS`/`CHECK` döndüren bir `IF()`. Kural: tek bir `CHECK` varsa model sunulamaz. Ya düzelt, ya da çekinceyi memo'nun **ilk cümlesine** yaz — dipnota asla.

---

## Step 8 · The discipline checklist

Before you show a model to anyone:

- [ ] No number is hardcoded inside a formula — every one traces to `02_Inputs`
- [ ] Every input has a unit and a source (or the word `ASSUMPTION`)
- [ ] Inputs, calculations and outputs are on separate tabs
- [ ] `01_README` says in one sentence what decision the model supports
- [ ] Sensitivity exists, and you can name the two inputs the answer hinges on
- [ ] Every check on `07_Checks` says `PASS`
- [ ] You can reproduce every output number from memory of the logic, not by pointing at a cell

> **TR:** Bu listeyi modeli kimseye göstermeden önce geç. En sonuncusu en önemlisi: çıktıyı hücreyi göstererek değil, mantığı anlatarak yeniden üretebiliyor olman.
