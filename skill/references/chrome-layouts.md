# Chrome Layouts — Zones, Measurements, Variants

"Chrome" = everything that isn't a data visual: header band, navigation,
logo, filter panel, footer. Below are fully worked-out variants for both
canvas sizes. All values in canvas pixels, all on the 8-px grid.

The zone coordinates (`x, y, w, h`) from the chosen variant go 1:1 into
`AGENT-BRIEF.md` — they are the contract between everyone placing visuals
on the page.

## Canvas sizes

| Canvas     | When                                             | Margin | Gutter |
| ---------- | ------------------------------------------------ | ------ | ------ |
| 1280×720   | Standard, Desktop + Service, default             | 16     | 8–16   |
| 1920×1080  | Large monitors, wall screens, dense cockpits     | 24     | 16     |

Set in Desktop: click the page → Format → Page information / Canvas
settings → Type "Custom", enter width/height.

---

## Variant A · Header-band navigation (default)

```
┌────────────────────────────────────────────────────────────┐
│ [Logo]  Page title             [Nav: Overview|Detail|…]    │ Header band 56px
├────────────────────────────────────────────┬───────────────┤
│  KPI 1   KPI 2   KPI 3   KPI 4             │               │
│                                            │  Filter       │
│  ┌──────────────────────────┐ ┌──────────┐ │  Panel        │
│  │      Main visual         │ │  Detail  │ │  200px        │
│  └──────────────────────────┘ └──────────┘ │               │
├────────────────────────────────────────────┴───────────────┤
│ Data as of · Source · Contact                               │ Footer 24px
└────────────────────────────────────────────────────────────┘
```

Zones at **1280×720**, filter panel on the right:

| Zone            | x    | y   | w    | h   | Notes                              |
| --------------- | ---- | --- | ---- | --- | ----------------------------------- |
| Header band     | 0    | 0   | 1280 | 56  | Fill: ink or accent color          |
| Logo            | 16   | 12  | ≤120 | 32  | Height fixed 32, width proportional |
| Page title      | 152  | 14  | 400  | 28  | 16–20 pt Semibold                  |
| Nav buttons     | from x=800, right-aligned to 1264 | 12 | 96–128 each | 32 | active button = accent |
| Filter panel    | 1064 | 64  | 200  | 632 | own fill, one tone darker than BG  |
| Content area    | 16   | 72  | 1032 | 616 | KPI row + visuals live here        |
| Footer          | 0    | 696 | 1280 | 24  | 8–9 pt, gray                       |

Content grid within it (KPI row + 2 columns):

| Slot                     | x   | y   | w    | h   |
| ------------------------ | --- | --- | ---- | --- |
| KPI 1–4                  | 16 / 276 / 536 / 796 | 72 | 252 each | 96 |
| Main visual              | 16  | 184 | 672  | 400 |
| Detail visual            | 704 | 184 | 344  | 400 |
| Bottom strip (optional, e.g. table) | 16 | 592 | 1032 | 96 |

(Filter panel on the left: move the panel to x=0, content area to x=216;
logo stays in the header band.)

## Variant B · Left nav bar

For reports with many pages (>5) or an app-like character.

| Zone            | x   | y   | w    | h   | Notes                                |
| --------------- | --- | --- | ---- | --- | -------------------------------------- |
| Nav bar         | 0   | 0   | 64   | 720 | Icons + tooltips; active = accent      |
| Logo            | 12  | 12  | 40   | 40  | square mark at the top                 |
| Header band     | 64  | 0   | 1216 | 48  | Title + period                         |
| Filter panel    | 1064| 48  | 200  | 648 | on the right (left collides with nav)  |
| Content area    | 80  | 64  | 968  | 624 |                                         |
| Footer          | 64  | 696 | 1216 | 24  |                                         |

## Variant C · Native page tabs only (minimal)

No custom nav chrome; header band shrinks to 48 px (logo + title +
period), rest as Variant A. Choose this when the report is consumed in
the Service with the page area visible — that way you avoid double
navigation.

---

## Filter panel in detail

- **Fixed (default):** a rectangle shape as the panel background (one tone
  darker than the page BG, or ink at 4–6% opacity), slicers stacked on top:
  panel title "Filter" (11 pt Semibold), then 8 px spacing per slicer.
  Slicer style: dropdown saves space; list only for ≤6 values.
- **Expandable (bookmark technique):** two bookmarks "Filter open" /
  "Filter closed" (group the panel + slicers in the Selection pane, toggle
  visibility, save the bookmark without a data state!), toggle button
  (funnel icon) in the header band on the right. Document the click
  sequence in STEPS.md.
- Always include: a **filter-reset button** (bookmark to the default
  state) and a visible filter context (a text box, or the `filterInfo`
  footer with ChartKitchen), so no one mistakes filtered numbers for
  totals.

## Footer in detail

A text box, 8–9 pt, secondary gray, pattern:
`As of: <data date> · Source: <system> · Contact: <team/email>`
The data-as-of date is ideally a measure (card instead of static text), so
it doesn't go stale. The footer belongs in the **same** position on
**every** page — consistency is the whole point here.

## Logo practice

- In the header band: fixed height (32 px in a 56-px band), left-aligned;
  never scale it differently from page to page.
- Dark header band → ask the user for a white/negative logo variant
  instead of squeezing the color logo onto a dark background.
- Insert image → as an image element, alt text "Logo <Company>", remove
  from tab order (decorative).

## Consistency across pages

The chrome (header band, nav, panel, footer) is built **once** and
duplicated onto every page (Ctrl+C/V keeps coordinates exact). Always
carry chrome changes through to all pages — record this as a rule in the
AGENT-BRIEF. Nav buttons: format the current page's button in the
"Disabled" state with the accent color (shows "you are here" and isn't
clickable).
