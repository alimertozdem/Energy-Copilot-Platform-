# Example: CSRD job → P1 package response (320 words)
# This is a FEW-SHOT EXAMPLE for the LLM. It is NOT sent as-is to clients.

## Mock job posting (the LLM is shown this as input)
Posted by: SustainEU GmbH, Munich
Title: "Need help producing first ESRS E1 report — Scope 1/2/3 dashboard"
Budget: €5,000-10,000 fixed
Description:
We are a mid-cap manufacturing company filing our first CSRD report in 2026
(FY2025). We have utility bills, fleet data, refrigerant logs in Excel and SAP.
Our auditor wants a traceable methodology. We have Microsoft 365 + Power BI Pro
but no Fabric yet. Looking for someone to build a Scope 1/2/3 dashboard mapped
to ESRS disclosures. Tight deadline — report due in 8 weeks.

## Expected output (the LLM produces something like this)

Hitting your first ESRS E1 filing in 8 weeks with utility bills in Excel and
fleet data in SAP is a real squeeze — and the audit-trail requirement is what
trips up most teams at this stage. Excel numbers do not survive a "show me the
row that produced this kg CO2e" question.

I built EnergyLens, a production analytics platform with a Scope 1/2/3 module
mapped directly to ESRS E1 disclosures E1-1, E1-5, E1-6, and E1-9. The medallion
architecture gives you single-click drill from disclosed total back to the raw
utility row — exactly what an auditor needs.

Two questions before I quote precisely: (a) have you decided yet on Scope 2
methodology — pure location-based, or both market-based and location-based as
ESRS E1-6 now requires? (b) for Scope 3, which categories are you treating as
material — purchased goods, downstream leased assets, business travel, or
others?

Best fit looks like my P1 CSRD Quickstart — 2 weeks fixed, €3,200, includes
Scope 1/2/3 dashboard in your Power BI tenant plus methodology documentation
for your auditor. If you want broader coverage with Scope 3 categories 1+6+13
modeled separately, that becomes a 4-week engagement at €5,800.

One technical note: Fabric is not required for this project. Power BI Pro plus
your existing Excel/SAP data sources are sufficient. Direct Lake mode becomes
valuable later if you want sub-minute refresh.

Happy to do a 30-minute discovery call this week. Calendly link below.

Best,
Mert
