---
name: powerbi-design-framework
description: >
  Designs the skeleton of a Power BI report page through a short, native
  interview: derives branding/colors from a company presentation, website,
  or logo; sets navigation, header band, logo, footer, and filter panel;
  builds a tile grid following modern design rules; and stores everything
  as theme.json + Design Spec + Agent Brief — including accessibility
  checks (WCAG contrast, font sizes). Also includes: IBCS mode (structural
  elements as named slots), an Atomic-Design components page to copy from,
  bulk restyling across the PBIP/PBIR files (e.g. "turn off shadows
  everywhere, turn on rounded corners"), and a design linter. Optionally
  works with ChartKitchen visuals. Trigger when the user says something
  like "build me a report layout / page skeleton", "make me a Power BI
  design from our website/deck", "corporate design for my report",
  "theme/colors for Power BI", "set up filter panel + navigation", "make
  this report page consistent", "change the design everywhere at once",
  "check my report design" — even if they don't explicitly say
  "design framework".
---

# Power BI Design Framework — Interview → Page Skeleton

Helps human **and agentic** Power BI developers build report pages faster
and more consistently. Core idea: a short interview (or a branding source
such as a company deck/website) produces a binding skeleton: colors,
typography, grid, "chrome" (navigation, logo, footer, filter panel), and
tile structure.

> **Safety principle — "prepare + plan":** This skill does **not** write
> into an existing PBIP/PBIR file unprompted. It produces artifacts in
> `design-out/` (theme, spec, steps) — the human imports/confirms in Power
> BI Desktop. Writing directly into `*.Report/` only on explicit request,
> with a backup/commit beforehand.

## Why a framework (and not just a theme)

A theme alone makes colors consistent — but not layout, spacing, or
structure. Agentic developers additionally need **explicit,
machine-readable rules** (grid coordinates, zones, prohibitions), otherwise
every agent places visuals differently. That's why the output is split in
two: `DESIGN-SPEC.md` for humans, `AGENT-BRIEF.md` as a compact rule set
for agents.

## Workflow

### Step 0 · Capture context
- Does a project already exist (`*.Report/` + `*.SemanticModel/` = PBIP),
  or is the user starting from a blank slate? Either is fine — the skill
  doesn't need a PBIP, it produces specifications.
- Is there a **branding source**? (company presentation `.pptx`/`.pdf`,
  website URL, logo file, existing corporate design document). If yes:
  analyze it first (Step 2), **then** only ask the questions the source
  didn't already answer. This keeps the onboarding native and short.

### Step 1 · Interview (short, with defaults)
Ask the questions **compactly in one go**, and state a default for each —
so the user can simply say "use the defaults". Skip questions the branding
source has already answered.

1. **Purpose & audience:** management report · operational monitoring ·
   self-service analysis? (shapes density and level of detail)
2. **Branding:** source available (deck/website/logo)? Otherwise: name a
   primary color + accent, or a neutral modern palette?
   *(Default: neutral modern)*
3. **Canvas:** 1280×720 (standard 16:9) or 1920×1080?
   *(Default: 1280×720)*
4. **Navigation:** header band with page buttons · left nav bar · native
   page tabs only? *(Default: header band)*
5. **Logo:** available? Position? *(Default: left in header band)*
6. **Footer:** data-as-of date, source, contact/imprint? *(Default: yes,
   with data-as-of date + source)*
7. **Filter panel:** right · left · expandable (bookmark) · none?
   *(Default: right, fixed, ~200 px)*
8. **Tile structure:** KPI row at the top? How many core KPIs (3–5)?
   *(Default: 4 KPI tiles + 2×2 analysis grid)*
9. **Accessibility level:** WCAG AA (contrast ≥ 4.5:1, text ≥ 9 pt) is
   usually enough; AAA only if required. Color-blind-safe data colors?
   *(Default: AA + color-blind-checked palette)*
10. **IBCS mode?** Offer this for management reporting, plan/actual/
    forecast, or ChartKitchen usage: notation governs the colors,
    structural elements (title block, notation band, comment column, …)
    become named slots — see
    [`references/ibcs-mode.md`](references/ibcs-mode.md).
11. **ChartKitchen:** Should the project's ChartKitchen/IBCS visuals be
    used? *(optional — if yes, see Step 5)*
12. **Components page:** Should a hidden `_Design-System` page with ready
    building blocks (buttons, KPI tiles, header band with logo, …) be
    created for copying? *(Default: yes — it's the biggest consistency
    lever, see
    [`references/components-page.md`](references/components-page.md))*

### Step 2 · Extract and check branding
If a source exists, derive colors/typeface from it — the approach per
source type (PPTX theme, website CSS, logo pixels, PDF) is in
[`references/branding-extraction.md`](references/branding-extraction.md).
Ground rules:
- **One** accent color for the UI chrome, everything else neutral (a gray
  ramp derived from the ink color). Corporate colors are rarely good
  **data** colors — keep them separate: chrome palette vs. data colors.
- Run every text/background combination through the contrast check:
  `python scripts/check_contrast.py "#<fg>" --bg "#<bg>"` — the script
  automatically proposes an adjusted variant if it fails.
  Don't eyeball it; the check is the referee.

### Step 3 · Design the skeleton
Using the answers, define the layout:
- Zones & exact measurements (header band, nav, filter panel, footer,
  content grid) from
  [`references/chrome-layouts.md`](references/chrome-layouts.md) — it has
  ready, fully worked-out variants for both canvas sizes.
- Design rules (8-px grid, alignment, whitespace, visual hierarchy, tile
  rules, type scale, the default "modern-soft" look, accessibility) from
  [`references/design-rules.md`](references/design-rules.md).
- In IBCS mode, additionally the slot and override rules from
  [`references/ibcs-mode.md`](references/ibcs-mode.md).
Show the user a short ASCII wireframe of the chosen variant for
confirmation before writing the artifacts — that's cheaper than a redesign
afterward.

### Step 4 · Store artifacts (`design-out/`)
Create `design-out/` in the project (or current folder) with:

- **`theme.json`** — importable Power BI theme. Base:
  [`assets/theme-template.json`](assets/theme-template.json); structure and
  which keys get filled in how:
  [`references/theme-json.md`](references/theme-json.md).
- **`DESIGN-SPEC.md`** — the design system for humans: color roles (with
  checked contrast values!), type scale, zone measurements, wireframe,
  do/don't.
- **`AGENT-BRIEF.md`** — a compact rule set for agentic developers: canvas
  size, zones as `x,y,w,h`, grid/gutter, tile slots with coordinates,
  required properties per visual (title size, background, border),
  forbidden deviations, and in IBCS mode the named slots. Goal: an agent
  that reads only this file places visuals consistently with the rest.
- **`zones.json`** — the zones from the AGENT-BRIEF in machine-readable
  form (`{"content": [x,y,w,h], "ignorePages": ["_Design-System"]}`) —
  directly usable as input for the design linter (Step 6).
- **`STEPS.md`** — exact Desktop steps: import theme (View → Themes →
  Browse for themes), set canvas size, create chrome elements
  (shapes/buttons/text boxes) with the spec's measurements, build the
  filter panel (incl. bookmark technique, if expandable), build the
  `_Design-System` components page
  ([`references/components-page.md`](references/components-page.md)), set
  tab order + alt text.
- In IBCS mode, additionally **`theme-ibcs.json`** (overrides per
  [`references/ibcs-mode.md`](references/ibcs-mode.md)), so the standard
  and IBCS looks don't get mixed up.

### Step 4b · Work against the PBIP file (on request)
If a PBIP project exists, the skill can work directly with the report
files beyond `design-out/` — rules, the risk ladder, and the verified PBIR
facts (container objects, literal encoding) are in
[`references/pbir-integration.md`](references/pbir-integration.md). There
is no "Power BI Desktop API" for report layout — the file path **is** the
interface. The core tool is `scripts/bulk_restyle.py`:
- **Bulk changes** ("turn off shadows everywhere, light backgrounds,
  rounded corners"): `--preset modern-soft` or `--preset ibcs`, or a custom
  `--rules` file. Dry run is the default, `--apply` writes with a backup.
- **Remove overrides** (`--strip background,border,dropShadow`) so the
  theme governs again — more sustainable than hardcoding values.
- **Design linter** (`--check --zones design-out/zones.json`): checks the
  grid, shadow prohibition, font sizes/families, content zone, and
  `tabOrder` — as a quality gate before every publish. Run it once after
  every agentic page build and fix any violations.

### Step 5 · Optional: bring in ChartKitchen
If the user wants ChartKitchen visuals, **don't duplicate** — use the
optional companion skills `chartkitchen-report` and `deploy-to-powerbi`
from the Daten-WG PowerBI-Kitchen repo
(https://github.com/Losveratos/PowerBI-Kitchen-) for visual selection and
field mapping, if present in your setup. This design framework works
standalone without them. This skill supplies the "where and how big"
(slots in the AGENT-BRIEF) and the formatting requirements; the companion
skills supply the "what and with which fields". Note in the AGENT-BRIEF
which slots are reserved for ChartKitchen instances.

### Step 6 · Verify and hand off
- Carry the contrast-check output into the DESIGN-SPEC (evidence, not just
  claims).
- Validate `theme.json` as JSON syntax (`python -m json.tool`).
- If a PBIP exists: run the design linter
  (`python scripts/bulk_restyle.py <Report> --check --zones
  design-out/zones.json`) and report the result.
- **Look at the layout instead of guessing:** `python
  scripts/render_wireframe.py <Report> --zones design-out/zones.json
  --html` renders an SVG wireframe per page (zone overlay, tabOrder
  badges, zone violations in red) into `design-out/wireframes/` — the
  visual feedback loop without Desktop. Render after every agentic page
  build and check/show the result; the linter checks numbers, the
  wireframe shows proportions and gaps.
- Summarize: what lives where, which decisions are still open, what the
  human does next in Desktop.

## Guardrails
- Never write into `*.Report/` files unprompted; `design-out/` is the
  handoff point. Direct writes only on request + backup, following the
  risk ladder in `references/pbir-integration.md` (additive before
  mutating; always show `bulk_restyle.py` as a dry run first). `--check`
  is always allowed — it never writes.
- For ambiguous branding (e.g. three candidates for the primary color):
  present it as an **open decision** with preview hex values, don't guess.
- Contrast and font-size rules are not negotiable downward; if a corporate
  color fails AA, propose the adjusted variant and document the deviation.
- Never touch `.pbix` (binary); only PBIP/PBIR (text) and `design-out/`.
- Keep data-color recommendations color-blind-safe (no red/green-only
  encoding; traffic lights always paired with a second channel like symbol
  or position).

## Locking it in long-term & extension stages
- **CI gate:** anchor the linter + contrast check as a GitHub Action/
  pre-commit hook in the report repo — templates in `assets/ci/`,
  instructions in [`references/ci-gate.md`](references/ci-gate.md).
- **Trigger evals:** `evals/trigger-evals.json` is ready for the
  skill-creator optimization loop (deliberately not run yet — get queries
  approved by a human first).
- **Service layer (not in v1):** deployment without Desktop via Fabric
  REST / semantic-link-labs / Git integration — documented with verified
  facts and open questions in
  [`references/service-deployment.md`](references/service-deployment.md).
