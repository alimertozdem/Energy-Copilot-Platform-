# Decision memo — dynamic tariff portfolio, Feb–Apr 2025 cohort

**To:** Product Management, Energy Products & Tariffs
**From:** Ali Mert Özdemir
**Date:** 8 August 2026
**Data:** synthetic portfolio, 28 customers, 235,709 usable quarter-hourly intervals, German day-ahead price shape. Every figure below is reproducible with `python 02_run_pipeline.py`.

> **TR — bu doküman nedir:** Bir ürün yöneticisinin gerçekten teslim ettiği çıktı. Analiz değil, *karar*. Yapı: bulgu → sayı → öneri → riskin adı. Görüşmede "ne üzerinde çalışırdın?" sorusuna bu formatta cevap ver.

---

## Recommendation in one line

Ship the dynamic tariff to heat-pump households, **stop quoting a savings percentage in marketing**, and fund one Marktkommunikation fix (MaLo-ID validation at signup) that is worth more than the entire battery-optimisation story.

---

## 1 · The saving is real, but it is a price-level effect, not an optimisation effect

| Scenario | Portfolio bill, 90 days | vs fixed |
|---|---:|---:|
| A — fixed tariff | € 52,292.71 | — |
| B — dynamic, no behaviour change | € 46,693.09 | **−10.71%** |
| C — dynamic + battery optimisation | € 46,411.12 | −11.25% |

**The finding that matters:** every single unoptimised customer has a realised/average price ratio **above 1.00** (mean 1.068). They consume disproportionately in *expensive* quarter-hours — the household evening peak sits exactly on the price peak. So the 10.71% saving does **not** come from smart consumption. It comes from the average spot (8.81 ct/kWh) being far below the fixed energy component (15.40 ct/kWh).

**Consequence:** the saving evaporates when the market moves, not when the customer misbehaves. Break-even is at an average spot of **13.60 ct/kWh**. Above that, every dynamic customer is worse off than on fixed.

**Recommendation:** market the product as *"you pay what the market pays"*, never as a fixed percentage. Put the break-even price in the customer-facing material. Over-promised savings are the top churn driver in this segment and a regulatory exposure.

> **TR:** Tasarruf gerçek ama sebebi optimizasyon değil, **fiyat seviyesi**. Müşterilerin hepsi akşam zirvesinde tükettiği için realised/average oranı 1'in üstünde — yani "akıllı tüketim"den değil, borsa ortalamasının sabit tarifeden düşük olmasından kazanıyorlar. Ortalama spot 13,60 ct/kWh'yi geçerse herkes zarara döner. Bu yüzden yüzde vaat etme, "piyasa ne öderse onu ödersin" de.

---

## 2 · Battery arbitrage is worth far less than the pitch implies — here is the arithmetic

Incremental value of full battery optimisation across 20 battery customers over 90 days: **€ 282**. That is roughly **€ 57 per battery per year** from spot arbitrage.

Why it is so small — the derivation is four lines and it should be in every pitch review:

```
To deliver 1 kWh from the battery you first buy 1/η kWh from the grid.
Every grid kWh pays the FULL retail stack, not the spot price.
    basis = P_charge/η + (1/η − 1) × (markup + grid fee + levies)
With η = 0.88 and the 2026 German stack (1.80 + 21.87 ct):
    basis = 1.136 × P_charge + 3.22 ct/kWh
```

**Residential spot arbitrage must clear a ~3.2 ct/kWh spread before it earns its first cent**, because the round-trip loss is priced at retail. This is why a home battery earns its money on **self-consumption** (displacing ~37 ct retail with own PV), not on trading the curve.

**Recommendation:** keep battery optimisation as a *retention and comfort* feature, not a savings claim. If we want a defensible flexibility number, it has to come from balancing-market participation, not the spot spread. The model uses **€18/kW/yr** as a measured floor rather than the €65/kW/yr that would have made the business case look good.

> **TR:** Batarya arbitrajı 90 günde sadece €282 kazandırdı (~€57/batarya/yıl). Sebebi: kayıp enerji **spot değil perakende** fiyat ödüyor — bu yüzden kazanmaya başlamak için ~3,2 ct/kWh makas gerekiyor. Ev bataryasının parası arbitrajda değil öz-tüketimde (37 ct perakendeyi kendi PV'siyle ikame etmek). Bu yüzden modelde €65/kW/yıl yerine ölçülmüş €18/kW/yıl kullandım.

---

## 3 · Only 32.8% of the bill can move at all

Measured commodity share of the net price: **32.8%**. The remaining **67.2%** is grid fees, levies, taxes and VAT, which do not follow the market.

A customer who shifts 30% of consumption into the cheapest quarter-hours therefore has a theoretical ceiling of roughly **30% × 32.8% ≈ 9.8%** bill reduction — before losses.

**Recommendation:** this number belongs in sales training. It is also the argument for prioritising **§14a Module 3 (time-variable grid fees)** on the roadmap: it is the only lever that puts a second ~25% of the bill in play. Spot plus time-variable grid fee is a two-signal optimisation problem, and the two signals do not always agree.

> **TR:** Faturanın yalnızca %32,8'i piyasayla hareket ediyor; %67,2'si şebeke+vergi. Yani %30 yük kaydırmanın teorik tavanı ~%9,8. Bu sayı satış eğitimine girmeli. Ve §14a Modül 3 bu yüzden yol haritasında öne alınmalı — faturanın ikinci %25'ini oynatan tek kaldıraç.

---

## 4 · Negative prices: we are capturing almost none of the upside

2025 had **542 negative-price quarter-hours (1.55% of the year)**. Our customers bought **465 kWh** in those intervals — **0.4% of total volume** — earning **€19.78** in credit.

**Recommendation:** this is the clearest HEMS product gap in the dataset. Pre-heating the buffer tank and pre-charging the EV on negative-price forecasts is cheap to implement, has no comfort cost, and is a marketing story that is actually true (the market paid you to use electricity). Size it properly before committing: the total pot is small today, but it grows with every GW of solar.

> **TR:** 2025'te 542 negatif fiyatlı çeyrek saat vardı; müşteriler bunun sadece %0,4'ünü yakaladı (€19,78). En net HEMS ürün boşluğu bu: negatif fiyat tahmininde tampon tankı ve elektrikli aracı önceden şarj etmek. Konfor maliyeti yok ve pazarlama hikâyesi *gerçek*. Ama potun bugün küçük olduğunu da söyle.

---

## 5 · The highest-return fix is not in the tariff at all — it is in Marktkommunikation

| Metric | Measured |
|---|---:|
| First-time-right switch rate | **82.1%** |
| Median days from signature to first supplied kWh | **24** |
| Top rejection cause | **MaLo-ID unknown at DSO** (14.3% of customers) |
| Extra delay when a switch is rejected | **+12.2 days** (35.3 vs 23.1) |
| Delayed revenue, rejected cohort | **€116 vs €66** per customer |
| Customers with a malformed MaLo-ID in the CRM | **4 of 28 (14%)** |

Where the days actually go:

| Hop | Days |
|---|---:|
| Signature → UTILMD sent (**us**) | 2.6 |
| UTILMD → acknowledgement (**DSO**) | 4.0 |
| Acknowledgement → supply start (**statutory**) | 18.3 |
| Supply start → first invoice (**us**) | 44.8 |

**Root cause, and it is embarrassingly cheap to fix:** the CRM export passed through Excel, which stripped leading zeros from MaLo-IDs. Four of 28 customers carry a 10-digit MaLo where the specification requires 11. A naive join on the raw string silently drops **14% of the customer base** from every downstream report — and those are precisely the customers whose UTILMD gets rejected as "MaLo-ID unknown at DSO".

**Recommendation, in priority order:**
1. **Validate MaLo-ID format at the point of capture** (11 digits, zero-padded). One regex. Removes the single largest rejection cause.
2. **Alert on unacknowledged UTILMD after 5 days.** One case in the sample never got acknowledged at all and would sit in limbo indefinitely.
3. **Attack the 44.8-day supply-to-invoice gap.** It is the largest single block of delay in the funnel and it is entirely ours — no DSO or statutory dependency. Two customers were supplied and never invoiced.

> **TR:** En yüksek getirili düzeltme tarifte değil, **Marktkommunikation**'da. İlk seferde doğru geçiş oranı %82,1; reddedilen geçiş +12,2 gün gecikiyor. Kök sebep utanç verecek kadar basit: CRM ihracı Excel'den geçtiği için MaLo-ID'lerin baştaki sıfırı silinmiş — 28 müşterinin 4'ü 11 hane yerine 10 hane. Ham string üzerinde join yapan her rapor müşteri tabanının **%14'ünü sessizce kaybediyor**, ve tam bu müşterilerin UTILMD'si "MaLo-ID unknown" diye reddediliyor. Çözüm: kayıt anında format doğrulaması (tek regex), 5 gün onaylanmayan UTILMD için alarm, ve tamamen bize ait olan 44,8 günlük tedarik→fatura boşluğu.

---

## 6 · What I would not claim

- **The data is synthetic.** Price shape and load profiles are modelled, not metered. The *method* transfers; the magnitudes need real data.
- **The backtest assumes perfect foresight of intraday prices within the delivery day.** Day-ahead is published around 12:45 for the next day, so scenario C is a **ceiling** on achievable value, not a forecast of it. Real HEMS capture is materially lower.
- **Annualised figures are flagged as assumptions in the column names.** The observed window is Feb–Apr: heating-heavy and low-solar. Scaling by 365/90 overstates annual consumption and understates PV.
- **No battery degradation cost is charged.** Including it reduces scenario C further.
- **CAC, service cost and flexibility revenue are assumptions**, and the model's own Checks tab flags when the business case leans too heavily on the flexibility input.
- **Three of 20 battery customers end the period marginally negative** (max €0.32) because of charge stranded in the battery when the data ends. That loss is bounded by one full charge, which is why the sanity gate tolerates exactly that much and no more.

> **TR:** Kasıtlı olarak iddia *etmediğim* şeyler. Sentetik veri, mükemmel öngörü varsayımı (yani C senaryosu bir tavan, tahmin değil), mevsimsel yıllıklandırma sapması, degradasyon maliyeti yok, CAC/servis/esneklik varsayım. Bu listeyi memo'nun sonuna koymak zayıflık değil — enerji sektöründe olgunluk sinyali. Karşı taraf bunları zaten bulacak; önce sen söyle.
