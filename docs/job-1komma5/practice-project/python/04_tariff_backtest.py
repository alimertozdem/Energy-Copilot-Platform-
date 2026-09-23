"""
04_tariff_backtest.py -- the work sample.

Backtests three tariff/asset scenarios per customer over the observed period:
  A  FIXED     flat energy component
  B  DYNAMIC   quarter-hourly spot passthrough, NO behaviour change
  C  DYNAMIC + BATTERY   greedy price arbitrage inside the customer's own battery

Reports the euro delta, the realised/average price ratio, and a sensitivity
sweep on the spot level. Every assumption is a named constant at the top.

ASSUMPTIONS (state these before quoting any number):
  - Depth of discharge 90%, round-trip efficiency 88%, C-rate 0.5 (LFP-like)
  - Max 1.5 equivalent full cycles per day (warranty-friendly)
  - Battery serves LOAD only; no export arbitrage, no grid-charging limits
  - Perfect foresight of day-ahead prices within the delivery day. Day-ahead is
    published at ~12:45 for the next day, so this is a CEILING on achievable
    value, not a forecast of it. Real HEMS capture is materially lower.
  - Observed window is Feb-Apr 2025: heating-heavy, low-solar. Not annual.
  - No battery degradation cost charged. Adding it reduces scenario C.
"""
import duckdb, os, numpy as np, pandas as pd
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
DB   = Path(os.environ.get("DUCKDB_PATH", HERE.parent / "output" / "energy.duckdb"))
OUT  = HERE.parent / "output"; OUT.mkdir(exist_ok=True, parents=True)

DOD, ETA, C_RATE, MAX_CYCLES = 0.90, 0.88, 0.5, 1.5   # LFP-like, warranty-friendly

con = duckdb.connect(str(DB), read_only=True); con.execute("SET TimeZone='UTC'")
p = con.execute("SELECT * FROM v_params").df().iloc[0]
df = con.execute("""
    SELECT malo_id, segment, tariff_type, local_date, ts_utc,
           kwh_import, spot_ct_kwh, battery_kwh
    FROM gold_interval ORDER BY malo_id, ts_utc""").df()
con.close()

NON_COMMODITY = p.grid_fee_ct_kwh + p.levies_tax_ct_kwh
VAT           = 1 + p.vat_rate

def gross_ct(energy_ct):                      # -> customer price incl. all fees + VAT
    return (energy_ct + NON_COMMODITY) * VAT

# ---------------------------------------------------------------------------
# THE ECONOMIC DISPATCH RULE  (derive this on a whiteboard, it takes 4 lines)
# ---------------------------------------------------------------------------
# To deliver 1 kWh from the battery you must first buy 1/ETA kWh from the grid.
# EVERY grid kWh pays the full stack: energy + markup + grid fee + levies + VAT.
# So the loss is not priced at the spot price -- it is priced at the RETAIL
# price. Cost basis per delivered kWh, in ct:
#
#     basis = P_charge / ETA  +  (1/ETA - 1) * (markup + non_commodity)
#
# Discharge is only profitable when P_discharge > basis. VAT appears on both
# sides and cancels, so it drops out of the rule (but not out of the bill).
#
# Plug in ETA = 0.88 and the German 2026 stack (markup 1.8 + 21.87 ct):
#     basis = 1.136 * P_charge + 3.22 ct/kWh
# i.e. residential spot arbitrage needs roughly a 3.2 ct/kWh spread BEFORE it
# earns anything. That single line explains why home batteries in Germany make
# their money on SELF-CONSUMPTION (avoiding ~37 ct retail) rather than on
# trading the spread -- and why "battery + dynamic tariff" is a weaker story
# than the marketing suggests once grid fees are on the losses.
# ---------------------------------------------------------------------------
LOSS_FACTOR = 1.0 / ETA


def dispatch_series(load, price, day_id, usable_kwh, power_kwh, markup, non_commodity,
                    mean_daily_load):
    """Causal, economically-gated battery dispatch. Returns (charge, discharge) kWh.

    THREE BUGS THIS FUNCTION EXISTS TO AVOID -- all three were in earlier drafts
    of this very script, which is why they are documented rather than hidden:

    1) TIME ORDER, NOT SORT ORDER.  "Discharge into the priciest quarter-hours,
       charge in the cheapest" discharges at 08:00 energy it only charges at
       13:00. A battery cannot borrow from the future. That bug reported a 66%
       bill cut for small-load customers -- physically impossible.

    2) SoC CARRIES OVER MIDNIGHT.  Resetting state of charge each day throws
       away energy that was paid for. That bug made the battery INCREASE the
       portfolio bill by EUR 3.8k.

    3) THE LOSSES PAY RETAIL, NOT SPOT.  Cycling without an economic gate buys
       energy whose round-trip loss costs more than the spread earns. That bug
       left the battery worth ~EUR 0 and made 9 customers worse off.

    The fix for (3) is the cost-basis rule above: we track the volume-weighted
    cost basis of the energy actually sitting in the battery and only discharge
    when the current price beats it.
    """
    n = len(load)
    charge, discharge = np.zeros(n), np.zeros(n)
    if usable_kwh <= 0:
        return charge, discharge

    # 4) DO NOT FILL A BATTERY THE HOUSEHOLD CANNOT EMPTY.
    #    A 15 kWh battery in a home that uses 7 kWh/day can never cycle its full
    #    capacity: the surplus is bought, held, and stranded. Cap the working
    #    capacity at ~1.25 days of load. This is also a real product finding --
    #    oversized storage cannot be monetised by a small consumer, no matter how
    #    good the optimiser is.
    usable_kwh = min(usable_kwh, 1.25 * mean_daily_load)
    if usable_kwh <= 1e-9:
        return charge, discharge

    adder = (LOSS_FACTOR - 1.0) * (markup + non_commodity)   # ct/kWh, fixed
    # Per day: the price we could plausibly exit at, and therefore the highest
    # price at which entering is still profitable.
    starts = np.flatnonzero(np.r_[True, day_id[1:] != day_id[:-1]])
    bounds = np.r_[starts, n]
    charge_cap = np.empty(n)
    for a, b in zip(bounds[:-1], bounds[1:]):
        exit_price = np.quantile(price[a:b], 0.88)            # a realistic peak
        charge_cap[a:b] = (exit_price - adder) * ETA          # invert the rule

    soc, basis = 0.0, 0.0            # kWh stored, ct/kWh cost basis of that energy
    day_budget, cur_day = usable_kwh * MAX_CYCLES, day_id[0]
    for i in range(n):
        if day_id[i] != cur_day:
            cur_day, day_budget = day_id[i], usable_kwh * MAX_CYCLES
        room = usable_kwh - soc
        # ENTER: cheap enough that a profitable exit exists, or the market is
        # paying us to consume (negative price is always worth absorbing).
        if room > 1e-9 and (price[i] <= charge_cap[i] or price[i] < 0):
            put = min(power_kwh, room)
            stored = put * ETA
            unit_basis = price[i] / ETA + adder
            basis = (soc * basis + stored * unit_basis) / (soc + stored)
            soc += stored
            charge[i] = put                                   # drawn FROM THE GRID
        # EXIT: only when the current price actually beats our cost basis.
        elif soc > 1e-9 and load[i] > 0 and day_budget > 1e-9 and price[i] > basis:
            take = min(power_kwh, load[i], soc, day_budget)
            discharge[i] = take
            soc        -= take
            day_budget -= take
    return charge, discharge


rows, day_example = [], None
for (malo, seg, ttype, batt), g in df.groupby(
        ["malo_id", "segment", "tariff_type", "battery_kwh"], sort=False):
    g = g.sort_values("ts_utc")
    usable = batt * DOD
    power_per_interval = batt * C_RATE * 0.25               # kWh movable per 15 min
    load  = g.kwh_import.to_numpy(float)
    price = g.spot_ct_kwh.to_numpy(float)
    dayid = pd.factorize(g.local_date)[0]
    mean_daily = load.sum() / max(g.local_date.nunique(), 1)
    ch, dis = dispatch_series(load, price, dayid, usable, power_per_interval,
                              p.dyn_markup_ct_kwh, NON_COMMODITY, mean_daily)
    net_c = load - dis + ch                                  # grid import, scenario C

    bill_A = (load  * gross_ct(p.fix_energy_ct_kwh)              ).sum()/100 + p.fix_base_fee_eur_month*3
    bill_B = (load  * gross_ct(price + p.dyn_markup_ct_kwh)      ).sum()/100 + p.dyn_base_fee_eur_month*3
    bill_C = (net_c * gross_ct(price + p.dyn_markup_ct_kwh)      ).sum()/100 + p.dyn_base_fee_eur_month*3

    vwap_B = (price*load ).sum()/max(load.sum(),1e-9)
    vwap_C = (price*net_c).sum()/max(net_c.sum(),1e-9)
    avg    = price.mean()

    rows.append(dict(malo_id=malo, segment=seg, tariff_type=ttype, battery_kwh=batt,
        kwh_load=load.sum(), kwh_grid_with_battery=net_c.sum(),
        bill_A_fixed=bill_A, bill_B_dynamic=bill_B, bill_C_dyn_battery=bill_C,
        save_B_vs_A=bill_A-bill_B, save_C_vs_B=bill_B-bill_C, save_C_vs_A=bill_A-bill_C,
        ratio_B=vwap_B/avg, ratio_C=vwap_C/avg,
        cycles_used=(dis.sum()/usable) if usable>0 else 0.0,
        kwh_shifted=dis.sum()))

    if day_example is None and batt >= 10:
        d0 = g[g.local_date == g.local_date.unique()[20]]
        i0 = g.index.get_indexer(d0.index)
        day_example = (d0, ch[i0], dis[i0])

res = pd.DataFrame(rows)

# ---------------------------------------------------------------------------
# SANITY GATE. Never publish a model output you have not tried to break.
# Each assertion encodes a physical or commercial law. If one trips, the model
# is wrong -- not the world.
# ---------------------------------------------------------------------------
days_obs = df.local_date.nunique()
problems = []
bad = res[res.kwh_grid_with_battery < -1e-6]
if len(bad): problems.append(f"{len(bad)} customers have NEGATIVE grid import (impossible)")
bad = res[(res.battery_kwh > 0) & (res.cycles_used / days_obs > MAX_CYCLES + 0.01)]
if len(bad): problems.append(f"{len(bad)} customers exceed {MAX_CYCLES} cycles/day")
bad = res[(res.battery_kwh == 0) & (res.kwh_shifted.abs() > 1e-6)]
if len(bad): problems.append(f"{len(bad)} customers shift energy without a battery")
bad = res[res.save_C_vs_A / res.bill_A_fixed > 0.45]
if len(bad): problems.append(f"{len(bad)} customers save >45% vs fixed -- implausible, check the model")
bad = res[res.kwh_shifted > res.kwh_load * 1.01]
if len(bad): problems.append(f"{len(bad)} customers discharge more than they consume")
# The ONLY way scenario C can legitimately lose money is the period boundary:
# energy bought before the last day and still sitting in the battery when the
# data ends. That loss is bounded by ONE full charge at retail price -- so that
# is the tolerance, derived rather than tuned. If a customer is worse off by
# MORE than that, the dispatcher really is broken.
retail_ct = p.fix_energy_ct_kwh + NON_COMMODITY
res["boundary_tolerance_eur"] = res.battery_kwh * DOD * retail_ct / 100.0
bad = res[(res.battery_kwh > 0) &
          (res.save_C_vs_B < -res.boundary_tolerance_eur)]
if len(bad): problems.append(f"{len(bad)} customers worse off by MORE than one "
                             f"battery-fill -- dispatcher is broken, not a boundary effect")
stranded = res[(res.battery_kwh > 0) & (res.save_C_vs_B < 0)]
if len(stranded):
    print(f"  NOTE: {len(stranded)} of {(res.battery_kwh>0).sum()} battery customers end the "
          f"period marginally negative (max EUR {-stranded.save_C_vs_B.max():.2f}); this is "
          f"stranded end-of-period charge, bounded by one fill, not a dispatch error.")
print("SANITY GATE:", "PASS - all 5 physical checks green" if not problems
      else "FAIL\n  - " + "\n  - ".join(problems))
print(f"  battery cycles/day: mean {res[res.battery_kwh>0].cycles_used.mean()/days_obs:.2f}"
      f"  max {res[res.battery_kwh>0].cycles_used.max()/days_obs:.2f}  (cap {MAX_CYCLES})")

res.to_csv(OUT / "backtest_by_customer.csv", index=False)

days = df.local_date.nunique()
seg = (res.groupby("segment")
          .agg(customers=("malo_id","count"), kwh=("kwh_load","sum"),
               A=("bill_A_fixed","sum"), B=("bill_B_dynamic","sum"), C=("bill_C_dyn_battery","sum"),
               ratio_B=("ratio_B","mean"), ratio_C=("ratio_C","mean"),
               cycles=("cycles_used","mean"), shifted=("kwh_shifted","sum"))
          .assign(B_vs_A_pct=lambda d: 100*(d.A-d.B)/d.A,
                  C_vs_A_pct=lambda d: 100*(d.A-d.C)/d.A,
                  C_vs_B_eur=lambda d: d.B-d.C)
          .round(2).sort_values("C_vs_A_pct", ascending=False))

print("="*100)
print(f"TARIFF BACKTEST  ·  {len(res)} customers  ·  {days} days observed  ·  {len(df):,} priced intervals")
print(f"period average spot: {df.spot_ct_kwh.mean():.2f} ct/kWh   "
      f"fixed energy component: {p.fix_energy_ct_kwh:.2f} ct/kWh   "
      f"dynamic markup: {p.dyn_markup_ct_kwh:.2f} ct/kWh")
print("="*100)
print(seg[["customers","kwh","A","B","C","B_vs_A_pct","C_vs_A_pct","C_vs_B_eur",
           "ratio_B","ratio_C","cycles","shifted"]].to_string())

tot = res[["bill_A_fixed","bill_B_dynamic","bill_C_dyn_battery"]].sum()
print(f"""
PORTFOLIO TOTAL over {days} days
  A  fixed                    EUR {tot.bill_A_fixed:10,.2f}
  B  dynamic, no change       EUR {tot.bill_B_dynamic:10,.2f}   ({100*(tot.bill_A_fixed-tot.bill_B_dynamic)/tot.bill_A_fixed:5.2f}% vs A)
  C  dynamic + battery        EUR {tot.bill_C_dyn_battery:10,.2f}   ({100*(tot.bill_A_fixed-tot.bill_C_dyn_battery)/tot.bill_A_fixed:5.2f}% vs A)
  incremental value of the battery only: EUR {tot.bill_B_dynamic-tot.bill_C_dyn_battery:,.2f} over {days} days
  mean realised/average price ratio:  B {res.ratio_B.mean():.4f}  ->  C {res.ratio_C.mean():.4f}
""")

# ---- SENSITIVITY: the honest part. What does the answer hinge on? -----------
print("SENSITIVITY -- scenario B saving vs fixed, if the spot LEVEL shifts")
print("(the level, not the shape, is what drives the headline saving)")
sens = []
for shift in [-40, -20, 0, 20, 40, 60]:
    pr = df.spot_ct_kwh.to_numpy(float) * (1 + shift/100)
    ld = df.kwh_import.to_numpy(float)
    b = (ld*gross_ct(pr + p.dyn_markup_ct_kwh)).sum()/100
    a = (ld*gross_ct(p.fix_energy_ct_kwh)).sum()/100
    sens.append(dict(spot_shift_pct=shift, avg_spot_ct_kwh=round(pr.mean(),2),
                     fixed_eur=round(a,0), dynamic_eur=round(b,0),
                     saving_pct=round(100*(a-b)/a,2)))
print(pd.DataFrame(sens).to_string(index=False))
print("\nBreak-even: dynamic beats fixed while (avg spot + markup) < fixed energy component "
      f"= {p.fix_energy_ct_kwh:.2f} ct/kWh, i.e. while avg spot < {p.fix_energy_ct_kwh-p.dyn_markup_ct_kwh:.2f} ct/kWh.")

# ------------------------------------------------------------------- CHARTS
fig, ax = plt.subplots(3, 1, figsize=(11, 13))

d0, c0, s0 = day_example
t = pd.to_datetime(d0.ts_utc).dt.tz_convert("Europe/Berlin")
ax[0].plot(t, d0.spot_ct_kwh, color="#0b7a5a", lw=1.8, label="Day-ahead spot (ct/kWh)")
ax[0].axhline(0, color="#c0562f", lw=0.8, ls=":")
ax[0].set_ylabel("ct/kWh"); ax[0].legend(loc="upper left", fontsize=8)
ax[0].set_title(f"One day of dispatch — {d0.local_date.iloc[0]} — 15-minute MTUs", fontsize=11)
ax2 = ax[0].twinx()
ax2.bar(t, d0.kwh_import, width=0.008, color="#bcd8cf", label="Load (kWh)")
ax2.bar(t, -s0, width=0.008, color="#0b3d33", label="Battery discharge")
ax2.bar(t,  c0, width=0.008, color="#c0562f", alpha=.75, label="Battery charge")
ax2.set_ylabel("kWh / 15 min"); ax2.legend(loc="upper right", fontsize=8)

x = np.arange(len(seg)); w = 0.27
ax[1].bar(x-w, seg.A, w, label="A fixed",           color="#9aa8a4")
ax[1].bar(x,   seg.B, w, label="B dynamic",         color="#58b79a")
ax[1].bar(x+w, seg.C, w, label="C dynamic+battery", color="#0b3d33")
ax[1].set_xticks(x); ax[1].set_xticklabels(seg.index, fontsize=8)
ax[1].set_ylabel(f"EUR over {days} days"); ax[1].legend(fontsize=8)
ax[1].set_title("Bill by scenario and segment", fontsize=11)

ax[2].scatter(res.ratio_B, res.ratio_C, s=28+res.battery_kwh*7,
              c=np.where(res.battery_kwh>0, "#0b7a5a", "#c0562f"), alpha=.8)
lim = [min(res.ratio_C.min(), res.ratio_B.min())-.02, res.ratio_B.max()+.02]
ax[2].plot(lim, lim, ls="--", c="#9aa8a4", lw=1)
ax[2].axhline(1.0, c="#c0562f", lw=.9, ls=":")
ax[2].set_xlabel("realised/average ratio — no battery (B)")
ax[2].set_ylabel("realised/average ratio — with battery (C)")
ax[2].set_title("Does the battery move the customer below 1.00?  "
                "(red dots = no battery; dotted line = flat consumer)", fontsize=10)
plt.tight_layout(); plt.savefig(OUT / "backtest_charts.png", dpi=135)
print(f"\ncharts  -> {OUT/'backtest_charts.png'}")
print(f"detail  -> {OUT/'backtest_by_customer.csv'}")
seg.to_csv(OUT / "backtest_by_segment.csv")
