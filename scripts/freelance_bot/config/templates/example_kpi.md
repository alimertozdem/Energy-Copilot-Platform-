# Example: Building KPI job → P2 package response

## Mock job posting
Posted by: NordicProperty Holdings, Stockholm
Title: "Power BI dashboard for our 8-building office portfolio energy data"
Budget: €2,000-3,000 fixed
Description:
We manage 8 commercial office buildings across Stockholm and Copenhagen.
Energy bills come monthly from suppliers, EPC certificates on file. We want
a single dashboard our asset managers can use to see kWh/m², year-over-year,
and which buildings are dragging the portfolio score down. Bonus if it shows
which buildings need EPC renovation under EU Taxonomy.

## Expected LLM output

Eight buildings across two countries, supplier bills monthly, and no live
benchmark across the portfolio — the "which building is dragging us down"
question is one of the most expensive questions in property to leave
unanswered. Without it, every renovation budget conversation is anecdotal.

In my EnergyLens platform I built exactly this view across a 10-building
portfolio: EnPI per building, kWh/m² normalized for floor area, and an
EPC-weighted portfolio compliance score that highlights buildings needing
upgrades before Taxonomy reporting. Building-type-aware thresholds (Office
35, Hotel 130, Logistics 60) prevent false positives.

A couple of questions before I scope precisely: (a) are the EPC certificates
all from the same scheme, or do you have a mix of Swedish and Danish methodologies
that need to be harmonized? (b) what is the refresh cadence you need — monthly
when bills arrive, or do some suppliers offer daily/hourly meter data?

Best fit is my P2 Building Energy KPI Dashboard — €2,200 fixed for 8 buildings
(base €1,800 for 5, plus €250 each for the extra 3), 1-week sprint. Delivers
EnPI, kWh/m², year-over-year, EPC compliance heatmap, and anomaly detection.

If you also want a quick Fabric audit to evaluate whether Direct Lake makes
sense for your refresh frequency, that's an additional 3 days at €1,200 and
delivers a written roadmap.

Happy to walk through EnergyLens on a 30-minute call. Calendly below.

Best,
Mert
