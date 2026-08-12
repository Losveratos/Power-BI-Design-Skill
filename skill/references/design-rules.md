# Design Rules for Power BI Pages

These rules are the "why" behind the framework. They apply to every page,
regardless of branding and layout variant.

## 1 · Grid & spacing (8-px system)

All measurements are multiples of 8 px (canvas pixels, not inches). This
makes layouts reproducible — especially for agents that set coordinates.

- **Outer margin:** 16 px to every canvas edge (24 px at 1920×1080).
- **Gutter (spacing between tiles):** 8 px, 16 px for an airy management
  look.
- **Padding inside tiles:** 12–16 px; a title should never touch the edge.
- Visuals **snap to the grid**: x, y, width, height all divisible by 8.

## 2 · Gestalt principles applied

- **Proximity = belonging together.** Whatever belongs together
  functionally (a KPI + its trend) sits closer to each other than to
  anything else. The gutter within a group is smaller than the gap between
  groups.
- **Alignment.** Every tile edge sits on a shared alignment line. A single
  "almost aligned" visual ruins the impression of the whole page — so take
  coordinates from the AGENT-BRIEF, don't eyeball them.
- **Similarity.** Same role = same look: all KPI tiles have identical
  height, title size, background. Deviation only as a deliberate signal
  (e.g. the one critical metric).
- **Whitespace is structure, not wasted space.** Better one fewer visual
  than sacrificing the gutter. Rule of thumb: ≤ 6–8 visuals per page (KPI
  tiles count as half).
- **Figure/ground.** Page background minimally tinted (e.g. `#FAFAFB`),
  tiles white — so the tiles carry the structure without border lines.
  Use borders and shadows sparingly: either a subtle outline **or** a
  subtle shadow, never both.

## 2b · Default look "modern-soft"

The framework's default look has a name so the spec, theme, and
`bulk_restyle.py` preset all mean the same thing: **no shadows**,
structure through **tonal value** (white tiles on a slightly tinted
background), a **subtle outline** (gray-200), and **slightly rounded
corners (radius 8)**. Shadows are almost always noise in BI reports —
tonal separation achieves the same effect more calmly. In IBCS mode the
look becomes stricter (radius 0, no outline) — see
[`ibcs-mode.md`](ibcs-mode.md).

## 3 · Visual hierarchy (reading order)

Western readers scan in a Z-/F-pattern: top-left → top-right → diagonally
down. This implies:

1. **Top-left:** page title + core message (when in doubt, the most
   important number).
2. **Top row:** KPI tiles (overview — "where do we stand?").
3. **Middle:** main analysis visual (the largest element on the page,
   ~40–50% of the content area). A page has **one** main act.
4. **Bottom/right:** detail, drivers, tables.

This matches Shneiderman's mantra (overview → zoom/filter → details) and
fits the IBCS structure of the other project skills.

## 4 · Tile rules (KPI row)

- **3–5 KPI tiles**, no more — beyond 6, no one compares them anymore.
- Equal width: content width minus gutter, divided by the count.
- Structure per tile (top to bottom): label (small, gray) → value (large)
  → comparison/delta (small, with sign and direction).
- Don't encode deltas by color alone (color blindness): add a sign, arrow,
  or ▲▼.
- Tile height 88–120 px (1280 canvas); all identical.

## 5 · Typography scale

Power BI renders Segoe UI reliably on all clients — for corporate fonts,
check whether they're available in the Service/browser, otherwise fix
Segoe UI as the fallback. Scale (for 1280×720; at 1920×1080 ×1.25–1.5):

| Role                  | Size (pt) | Weight             |
| ---------------------- | ---------- | ------------------ |
| Page title            | 16–20      | Semibold           |
| Visual title          | 11–12      | Semibold           |
| KPI value (callout)   | 24–28      | Regular/Semibold   |
| Axes/labels/body      | 9–10       | Regular            |
| Footer/metadata       | 8–9        | Regular, gray      |

**Floor 8 pt, target ≥ 9 pt** for anything meant to be read. Anything
smaller is illegible on projectors/screenshots — this is an accessibility
boundary, not a matter of taste.

## 6 · Color roles (separate chrome from data)

- **Chrome palette** (navigation, header band, tiles): ink (near-black), a
  gray ramp (derived from ink, not pure gray), background, **one** accent
  color (the corporate primary color). Use the accent only for
  interaction/emphasis (active nav button, selection), never as a large
  area behind text without a contrast check.
- **Data colors**: max. 6–8, color-blind-safe, mutually distinguishable.
  Corporate blue may be the first data color; derive the rest from it
  (don't force 8 corporate tones).
- **IBCS context** (when ChartKitchen/IBCS is in play): AC = dark/solid,
  PY = gray, PL = outline, FC = hatched — then semantics carries the
  colors, and the corporate color stays reserved for the chrome.
- Traffic-light logic (red/green) sparingly, and always with a second
  channel (symbol, position, text).

## 7 · Accessibility checklist (WCAG AA as the standard)

- **Contrast text↔background ≥ 4.5:1** (large titles ≥ 18 pt: ≥ 3:1).
  Check with `scripts/check_contrast.py` — never by eye.
- **Contrast of UI elements** (buttons, icons, chart lines against
  background) ≥ 3:1.
- **Font sizes** per the scale above; nothing below 8 pt.
- **Color blindness:** no information encoded *only* via red-vs-green.
  Deltas with sign/arrow, series additionally distinguishable via
  label/position.
- **Tab order** set in Desktop (Selection pane): follows the reading order
  (title → KPIs → main visual → details). Remove decorative elements
  (shapes, lines) from the tab order.
- **Alt text** per visual: one line naming the message ("Revenue AC vs.
  PL by month, AC falls below plan from June"), not the chart type.
- **Not hover-only:** core messages must not live exclusively in tooltips.

## 8 · Do / Don't quick list

| Do                                          | Don't                                        |
| ------------------------------------------- | --------------------------------------------- |
| One main visual per page                    | 10 equally sized visuals in a patchwork      |
| Tiles on the 8-px grid                       | Freehand placement "by feel"                 |
| One accent color, gray for context           | Squeezing in every corporate color somewhere |
| Title as a message ("X grows 12%")           | Title as a field name ("Sum of Sales by …")  |
| Leave whitespace                             | Fill every gap with a visual                 |
| Measure contrast                             | Letting "looks good" decide                  |
