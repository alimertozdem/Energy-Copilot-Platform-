# Design Philosophy — *Quiet Photosynthesis*

> Reference for `components/SustainabilityMotif.tsx`. Not user-facing.
> Documents the aesthetic decisions encoded in the SVG, so any future
> refactor maintains intent rather than just markup.

---

## The Movement

**Quiet Photosynthesis** is a botanical-engineering aesthetic — the visual
language of a discipline that has not yet been named, somewhere between
phyllotaxis, energy modeling, and Bauhaus diagram. It treats the renewable
energy stack the way a 19th-century field botanist treated wildflowers:
with reverence, exhaustive line work, and the assumption that the viewer
will look closely.

The composition is meant to be *barely there* — never above 12% opacity —
but built as though it would survive scrutiny at 100%. Every curve is a
deliberate intersection of growth and machinery, and nothing is decorative
for its own sake. This is the work of someone who would draw a single
turbine blade fifty times before placing the line.

## Visual Expression

**Form.** A single vertical stem rises from the lower-left corner.
At its apex sits a wind rotor reduced to three precise sweeps — not
illustrated, *engraved*. Mid-stem, a solar disc emits a measured
fan of rays in equal angular steps, the way a botanical diagram
fans the stamens of an exposed flower. At the base, root-like vein
networks dissolve into a low-amplitude pulse wave that extends
horizontally — the brand's Emerald Pulse, restated as a botanical
ground-line. Every line shares the same hairline weight; the entire
composition lives in one register, like a copperplate engraving.

**Color.** Three notes only, all from the Emerald palette. Deep
emerald for structure (the stem, the rotor, the root system); a
lighter mint for radial elements (rays, pulse); the merest hint of
glow at one or two intersection points, like sap catching morning
light. No fills. Everything is line. The 90% absence of color is the
point — it lets the composition recede into the page chrome the way
a watermark recedes into paper.

**Scale and rhythm.** The piece is anchored at one corner only,
never centered. Its proportions follow the golden section without
announcing it: the wind rotor sits exactly where the eye expects
the next botanical organ. Spacing between rays is constant — the
sound of metronomic, deliberate craftsmanship. The pulse wave is
long enough to register as a horizon, short enough not to compete
with the page's primary content.

**Composition.** The motif is fundamentally *quiet*. It does not
crowd, does not animate, does not assert. It functions like a
botanist's printer's mark — present, attributable, almost invisible.
A viewer working with energy data above it should feel the work is
"signed" without ever consciously seeing the signature.

**Typography.** Two scientific annotations are permitted: a single
unit ("kW · m⁻²" near the solar disc) and a quietly placed catalog
number ("EL-001" at the lower right of the stem). Both are set in
the host font at extreme small size, in the same mint tone as the
lines. They are the only words. They exist to suggest this is a
specimen card, not decoration.

## Craftsmanship Standard

This is the work of someone who has drawn this exact composition for
fifteen years and refines it monthly. Every angle is the result of
ten discarded versions. The radial spacing of the rays would, if
measured, prove to be exactly equal. The endpoints of the pulse wave
fall on the same baseline as the lowest root. Nothing is approximate.
The viewer who notices these things should feel the room go quiet.

## What This Is Not

- Not an illustration of renewable energy.
- Not a stack of icons.
- Not animated, not interactive, not "alive."
- Not the focal point of any page it appears on.

It is a watermark, drawn with the patience of a watermark, by someone
who knows that watermarks are the part of a printed thing that costs
the most and that almost no one sees.

---

*Encoded in: `web-app/frontend/components/SustainabilityMotif.tsx`*
