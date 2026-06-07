# Example: Fabric architecture/audit job → P3 + P4

## Mock job posting
Posted by: TechMittelstand AG, Hamburg
Title: "Power BI consultant — performance issues, possibly Fabric migration"
Budget: hourly $40-80
Description:
We have a Power BI Premium tenant. Our main reports are slow (15+ seconds
to load), and someone suggested Microsoft Fabric might help. We don't know
if we need to migrate or just optimize. Looking for a 2-3 day engagement
to figure out what to do.

## Expected LLM output

Fifteen-second Power BI load times after a Premium investment is the kind
of frustration that doesn't usually come from "wrong tool" — it usually comes
from semantic model design choices that compound under volume. Before
recommending a Fabric migration, the right move is a proper diagnosis.

I run a focused 3-day Fabric Audit & Roadmap engagement that covers exactly
this question. The deliverable is a written 90-day plan with a clear answer
to "should we migrate, optimize, or both." Across previous engagements the
typical answer is "fix DAX and the semantic model first, then evaluate
Direct Lake" — Direct Lake is excellent but it doesn't fix a poorly designed
star schema.

One question to scope: when you say "main reports are slow," do you know
whether the bottleneck is on initial load (model size / DirectQuery) or
on filter interaction (DAX measure complexity)? The two have different fixes.

Two paths I would offer:

P3 — Fabric Audit & Roadmap, 3 days, €1,200 fixed. You get a written audit
of your current setup, recommendations, and capacity-sizing guidance. No
implementation.

P4 — Power BI Performance Tune-up, 2 days, €800 fixed. If you already know
the slow report and just want it fixed, I profile with DAX Studio, refactor
the model, and deliver a before/after benchmark. Usually 3-10x speed gain.

Many clients start with P3 to scope properly, then P4 or a larger
implementation follows.

Happy to do a 30-minute discovery call. Calendly below.

Best,
Mert
