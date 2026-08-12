# IBCS Mode — Structures as Elements

IBCS mode is a switch over the whole framework: same zones, same grid, but
**notation governs the colors** and **structural elements become named
layout slots**. Activate it when the user mentions IBCS/HICHERT/management
reporting, uses ChartKitchen (question 10), or the topic is plan/actual/
forecast comparisons.

For chart-internal IBCS rules (scenario notation within the chart, scaling,
variance charts), the optional companion skills `ibcs-charts` and
`chartkitchen-report` from the Daten-WG PowerBI-Kitchen repo
(https://github.com/Losveratos/PowerBI-Kitchen-) cover that ground — this
mode governs the **page level** and works standalone without them.

## Principle: notation beats branding

In data charts, **meaning** carries the color, not the brand:

| Scenario                | Representation                     |
| ------------------------ | ----------------------------------- |
| AC (Actual)              | solid, dark (near-black)            |
| PY (Prior Year)          | gray, solid                         |
| PL (Plan)                | outline/border, not filled          |
| FC (Forecast)            | hatched                             |
| Good/bad variance        | green/red (restrained, e.g. #8CB400/#FF3A21 family) |

Consequence: the corporate accent color stays **in the chrome** (nav, active
buttons) and never appears in a data chart. Mixing the two destroys the
semantics ("is that brand blue or Plan?").

## Structural elements = named slots

IBCS pages have recurring structural elements. The mode treats them as
**standalone elements with a fixed slot** (name + coordinates in the
AGENT-BRIEF), not as accessories to the charts:

| Slot name             | Content                                            | Placement (Variant A, 1280×720) |
| ---------------------- | --------------------------------------------------- | ---------------------------- |
| `slot/title-block`     | IBCS title block: line 1 unit/scope, line 2 metric + unit (e.g., "Revenue in EUR million"), line 3 period + scenarios | in place of the page title in the header band, left-aligned |
| `slot/message`         | key message (Say!) as a full sentence               | right of/below the title block |
| `slot/notation-band`   | scenario legend (AC · PY · PL · FC) **once per page**, not per chart | below the header band, 24px tall |
| `slot/variance-strip`  | variance charts (ΔPL, ΔPY %) over a category axis **shared** with the base chart | directly above/next to the main visual, aligned |
| `slot/comment-col`     | comments as numbered elements ➀➁ with reference lines | right-hand column, 200–260px, may replace the detail visual |
| `slot/filter-context`  | visible filter context (footer or `filterInfo` in ChartKitchen) | footer |

Comments are a **report component** in IBCS (Check!), not decoration — that's
why `slot/comment-col` gets real space instead of tooltips.

## Layout rules in IBCS mode

- **Time horizontal, structure vertical:** time series as columns/lines
  (x = time), structural comparisons (products, regions) as bars
  (y = structure).
- **Consistent scales per row/column:** charts meant to be compared share a
  scale and baseline; where that's not possible, mark the scale break
  explicitly. Note this as a per-chart-row rule in the AGENT-BRIEF.
- **Density over decoration:** smaller gutters (8px), more content per page
  is fine — IBCS pages may be denser than dashboard pages, because uniform
  notation lowers the reading cost.
- **Titles are three-line title blocks**, not marketing headlines; the
  message lives in `slot/message`.

## Overrides relative to standard mode

| Aspect            | Standard mode                    | IBCS mode                                     |
| ------------------ | ---------------------------------- | ----------------------------------------------- |
| `dataColors`       | brand-compatible palette           | IBCS: `["#404040", "#9E9E9E", "#FFFFFF", …]` — AC/PY first |
| Accent color       | chrome + possibly 1st data color    | chrome **only**                                 |
| Tile look          | white cards, radius up to 8         | radius 0–2, no card look for charts within a comparison group (shared surface) |
| Traffic lights     | sparingly allowed                   | only IBCS variance logic (good/bad), never additional status lights |
| Page title         | message headline                    | `slot/title-block` + `slot/message`             |
| Legends            | per visual                          | `slot/notation-band` once per page              |
| KPI tiles          | free-form                           | with scenario tag and ΔPL/ΔPY variance, identical notation |

Document these overrides in `theme.json` (store as a second variant,
`theme-ibcs.json`) and in the AGENT-BRIEF under a dedicated `## IBCS`
section, so agents don't mix standard and IBCS rules.

## Accessibility in IBCS mode

Green/red for variances is the classic colorblindness conflict. IBCS solves
this structurally with: sign (+/−), bar direction, and position — these
secondary channels are **mandatory**, and only then is the color coding
acceptable. Still check the contrast of the variance colors on white with
`check_contrast.py` (label text may need to be darker than the bar color).
