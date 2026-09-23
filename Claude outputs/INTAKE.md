# Who to approach, and what to ask them for

## The one thing that decides everything: interval data, not the invoice

This report needs **8,760 readings a year (hourly) or 35,040 (quarter-hourly)**.
An invoice has twelve numbers. You cannot see "the site draws 71 kW at 03:00 on a
Sunday" in a monthly total — the information is not in there. No amount of
cleverness recovers it.

So a client who offers "our last twelve invoices" is not refusing you; they have
misunderstood what you asked for. The data you want exists as a separate thing
and it is usually free.

**In Germany it is called `Lastgang`** (also *Lastgangdaten*, *Viertelstundenwerte*,
*15-Minuten-Werte*). In English: *interval data*, *half-hourly data*, *load profile*.

[Likely — verify against the current rules before quoting them to a client]
Any German site metered with **RLM** (*registrierende Leistungsmessung*) has this
data recorded automatically. RLM is mandatory above roughly **100,000 kWh a year
or 30 kW of connected load**. Below that, small sites are on **SLP**
(*Standardlastprofil*) — only an annual reading exists, and those sites are not
candidates for this report at all. Sites between about 6,000 and 100,000 kWh may
have an *intelligentes Messsystem* that records intervals too.

The client requests it from their **Messstellenbetreiber** (metering operator,
often the local grid operator) or from their supplier. It is normally free and
arrives as CSV or Excel.

## Therefore: how to qualify a target before you write to them

You cannot see a load profile before they send one. But you can filter hard on
things you can look up, and it costs nothing:

**Wanted**
- A building that is genuinely **shut for part of the day** — offices, schools and
  universities, municipal buildings, libraries, sports halls, courts, museums,
  showrooms, larger retail with fixed opening hours.
- **Above ~100,000 kWh a year.** That is roughly a 2,000 m² office or bigger. It
  buys two things at once: the interval data exists by law, and the site is large
  enough for the findings to be worth a fee.
- Somebody with the title *Facility Manager*, *Technischer Leiter*,
  *Energiemanager*, *Objektleiter*, or *Head of Operations*. Not procurement.

**Not wanted — do not waste the email**
- Hospitals, data centres, hotels, 24-hour production, cold stores, care homes.
  They never switch off, so there is no closed period to measure. The tool refuses
  to issue a report for these and it is right to.
- Anything small enough to be on SLP. No data, no report.

## The final qualification happens during the free sample

You will still be wrong about some of them, and that is fine — it is cheap. Send
the offer, they send a file, you run one command, and the tool tells you in ten
seconds whether the site is a candidate (it fails the *"stated hours describe this
building's actual pattern"* check when it is not). If it is not, say so plainly and
move on; you have lost ten minutes and gained a contact who now knows you were
honest about it.

---

## What to send them — paste this into the email body

Do not attach a form. An attachment halves the reply rate.

> **Two things, and the second takes two minutes.**
>
> **1. Your interval data — not the invoices.** One file covering the last 12
> months with a timestamp and the kWh used in each interval. Quarter-hourly or
> hourly, either is fine. In Germany this is the *Lastgang* and your metering
> operator or supplier will send it on request, usually free and within a few days.
> Any column names, any language, any date format — I will handle it.
>
> *Monthly invoice totals will not work for this. The whole point is what happens
> at 3am, and a monthly figure cannot show that.*
>
> **2. Five answers:**
> - Building name, and floor area in m² if you have it
> - Normal operating hours (e.g. Mon–Fri 07:30–18:00)
> - Days the building was closed last year — public holidays, shutdowns
> - Your electricity price in €/kWh (the all-in rate on your bill is fine)
> - If the file has no timezone in it, which timezone the timestamps are in
>
> No site visit, no access to your systems, nothing to install.

## The three questions they always ask

**"Is my data safe?"**
It stays on one machine, is used only for your report, and is deleted when you say
so. Happy to sign your NDA before you send anything. If you would rather not send
building names, label them A, B and C — the analysis does not need to know.

**"We only have monthly totals."**
Then ask your metering operator for the Lastgang; it is recorded whether or not
anyone has ever looked at it. If the site turns out to be on a standard load
profile rather than a recording meter, this particular review is not possible and
I will tell you straight away rather than dress up a guess.

**"What if the data is messy?"**
Expected. Gaps, duplicate rows, daylight-saving jumps and German decimal commas are
all handled, and every one of them is reported back to you. Nothing is silently
corrected, and nothing is filled in.

---

## Turning their answers into a run

Their five answers become a job file — the only thing that differs per client:

```json
{
  "building": "Werk Nord, Hannover",
  "client": "Beispiel GmbH",
  "author": "Ali Mert Ozdemir",
  "csv": "clients/beispiel/lastgang_2025.csv",
  "timezone": "Europe/Berlin",
  "unit": "kwh",
  "open_hour": 7.5,
  "close_hour": 18,
  "workdays": [0,1,2,3,4],
  "price_eur_kwh": 0.276,
  "area_m2": 9100,
  "holidays": ["2025-01-01","2025-10-03"],
  "shutdowns": [["2025-12-22","2026-01-02"]],
  "out": "clients/beispiel/report.html"
}
```

Then, in order:

```
python audit.py                 jobs/beispiel.json   # the report
python export_verification_xlsx.py jobs/beispiel.json   # the Excel proof
python export_powerbi.py        jobs/beispiel.json   # only if they want a dashboard
```

If the client sends kW instead of kWh per interval, set `"unit": "kw"`.
If column detection guesses wrong, add `"timestamp_col"` and `"value_col"`.
