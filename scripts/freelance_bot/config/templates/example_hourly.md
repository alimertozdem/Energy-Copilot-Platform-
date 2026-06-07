# Example: Ad-hoc work, no clean package fit → hourly fallback

## Mock job posting
Posted by: Anonymous (NDA), Amsterdam
Title: "DAX expert needed for one-off measure refactor"
Budget: hourly €40-70
Description:
We have a Power BI report with ~80 measures, some are slow and some return
wrong totals when filtered. Need someone to audit, fix, and document. Probably
20-30 hours of work spread over 2 weeks.

## Expected LLM output

Eighty measures with mixed performance and incorrect filter behavior usually
points to two underlying issues — measure dependency chains that recompute
unnecessarily, and context-transition bugs (often missing CALCULATE wrappers
or unintended iterator behavior). Both are fixable, neither is exotic.

I have a production DAX library at version 56 across a 9-page enterprise
energy reporting solution — self-contained measures, building-type-aware,
optimized for Direct Lake. The pattern I use eliminates chain dependencies,
which is usually the root cause of the symptoms you describe.

One question to scope: are the "wrong totals" appearing consistently in
specific visuals, or only when certain slicers are applied? If consistent,
it's likely a CALCULATE / SUMX issue. If slicer-specific, it's likely
context-transition.

For ad-hoc DAX work I bill €60/hour or €450/day. For 20-30 hours of work,
my suggestion is a fixed-scope variant: 3 days at €1,350 covers a full audit
of all 80 measures, fixes for the top 15-20 problematic ones, and a documented
DAX style guide your team can apply going forward. If we identify more than
20 measures needing refactor, we extend by half-day increments.

Alternatively, P4 (Power BI Performance Tune-up) at €800 over 2 days targets
the specific slow report you mention — narrower scope, lower price.

Happy to do a 30-minute discovery call. Calendly below.

Best,
Mert
