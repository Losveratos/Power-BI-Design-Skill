# Power BI Theme (`theme.json`) — Structure & Population

The report theme is the lever for consistency that works **without** manual
formatting on every visual. It's based on
[`../assets/theme-template.json`](../assets/theme-template.json) — copy it
and fill in the keys marked below from the interview/branding.

Import in Desktop: **View → Themes → Browse for themes** →
`design-out/theme.json`. Theme changes apply immediately to all visuals that
haven't been manually overridden — so: put as much as possible into the
theme, and format by hand as little as possible.

## Structure and what goes where

```jsonc
{
  "name": "…",                    // descriptive name: "<Company> Report Theme v1"
  "dataColors": ["#…", …],        // DATA colors (series), 6–8 entries,
                                  // colorblind-checked — NOT the chrome palette
  "foreground": "#…",             // Ink: default text color
  "background": "#FFFFFF",        // tile/visual background
  "tableAccent": "#…",            // accent in tables/matrix (gridlines, totals)

  "textClasses": {                // global typography scale (pt) — covers
    "title":    { … },            //   visual titles
    "header":   { … },            //   headers (tables, card headers)
    "label":    { … },            //   axes, data labels, legends
    "callout":  { … }             //   KPI card value (default would be 45pt — too big!)
  },

  "visualStyles": {
    "*": { "*": { … } },          // wildcard: applies to ALL visuals
    "page": { "*": { … } }        // page background + wallpaper (outspace)
  }
}
```

### `textClasses` — recommended values (1280×720)

| Class     | fontSize | Note                                              |
| --------- | -------- | -------------------------------------------------- |
| `title`   | 11–12    | visual titles, Semibold via `fontFace`             |
| `header`  | 10       |                                                     |
| `label`   | 9–10     | never below 9 — accessibility limit                |
| `callout` | 24–28    | Power BI default is 45pt and blows out KPI tiles   |

Each class: `{ "fontFace": "Segoe UI", "fontSize": 10, "color": "<Ink>" }`
(title: `"Segoe UI Semibold"`). Only set a corporate font if it's available
in the service; otherwise use Segoe UI and document the desired font in the
DESIGN-SPEC as "if installed."

### `visualStyles."*"."*"` — the global defaults

The most important blocks (each an array with one object — a Power BI
quirk):

```jsonc
"*": { "*": {
  "background": [{ "show": true, "color": { "solid": { "color": "#FFFFFF" }}, "transparency": 0 }],
  "border":     [{ "show": false }],                       // OR a subtle outline — never both plus a shadow
  "dropShadow": [{ "show": false }],
  "visualHeaderTooltip": [{ "transparency": 0 }],
  "title": [{
    "show": true,
    "fontColor": { "solid": { "color": "<Ink>" }},
    "background": { "solid": { "color": "" }},
    "alignment": "left",
    "fontSize": 12,
    "fontFamily": "Segoe UI Semibold"
  }]
}}
```

Subtle tile look instead of a border: `background` white on a slightly
tinted page background (see below) carries the structure; if an outline is
desired: `"border": [{ "show": true, "color": {"solid": {"color": "<Gray-200>"}}, "radius": 8 }]`.

### `visualStyles.page` — page background

```jsonc
"page": { "*": {
  "background": [{ "color": { "solid": { "color": "<BG, e.g. #FAFAFB>" }}, "transparency": 0 }],
  "outspace":   [{ "color": { "solid": { "color": "<BG>" }}, "transparency": 0 }]
}}
```

`outspace` is the area around the canvas (wallpaper) — the same color as
`background` reads calmest in the service.

## Population logic from the interview

| Interview result             | Theme key                                          |
| ----------------------------- | --------------------------------------------------- |
| Ink (from branding/neutral)   | `foreground`, `textClasses.*.color`, title `fontColor` |
| Accent color                  | `tableAccent`; first `dataColors` slot only if it works as a data color |
| Page BG (tinted)              | `page.background` + `outspace`                     |
| Tile BG (white)                | `background` + `visualStyles.*.*.background`       |
| Data palette                  | `dataColors` (6–8, checked)                         |
| Typography scale               | `textClasses`                                       |

**Contrast requirement:** `foreground` on `background` AND on the page BG,
title color on header-band color, footer gray on page BG — all checked via
`scripts/check_contrast.py` (target ≥ 4.5:1; footer/secondary text too —
"it's just metadata" is not an exemption).

## Limits of the theme (→ STEPS.md)

Not everything can be a theme: canvas size, chrome shapes/buttons, filter
panel, bookmarks, tab order, alt text are manual work in Desktop and belong
in STEPS.md. The theme delivers colors + typography + visual defaults; the
chrome delivers the spec.

## Dark-mode variant

Base: [`../assets/theme-template-dark.json`](../assets/theme-template-dark.json)
— same structure/role logic as `theme-template.json`, just with the values
flipped. Reference derivation (AA-checked):

| Role                    | Light     | Dark      |
| ------------------------ | --------- | --------- |
| `ink` (foreground)       | `#1F2937` | `#E7EAF0` |
| `accent`/`tableAccent`   | `#2563EB` | `#5B8DEF` |
| `gray` (label/secondary) | `#3F4A5A` | `#A9B4C3` |
| `bg` (page/outspace)     | `#FAFAFB` | `#10151D` |
| `bg-card` (tile/`background`) | `#FFFFFF` | `#1B222D` |
| `border` (subtle outline) | — | `#2A3341` |
| `dataColors[0..5]` | `#2563EB #0D9488 #D97706 #7C3AED #DB2777 #64748B` | `#5B8DEF #2DD4BF #FBBF24 #A78BFA #F472B6 #94A3B8` |

**Derivation rules:**

1. **No pure black/white.** Page BG dark, but tinted toward ink (blue-gray
   instead of `#000`), text color light but not `#FFFFFF` — both avoid
   glare/halation during long reading sessions on a dark background.
2. **The tile is lighter, not darker.** In light mode the tile is white on a
   tinted page BG; in dark mode the relationship doesn't invert — the tile
   stays the *lighter* surface, just both values are now dark (`bg-card` one
   step lighter than `bg`), otherwise the structure disappears.
3. **The gray ladder is inverted**, not reinvented: same ink family, just
   stepped toward white instead of toward `bg`.
4. **Lighten/desaturate dataColors**, keeping the same order/color family
   (e.g., blue stays series 1), so legends/screenshots from both modes
   remain comparable.
5. **Contrast requirement unchanged:** `check_contrast.py --palette` for the
   roles (target AA ≥ 4.5:1) and each `dataColors` value individually
   against `bg-card` (target ≥ 3:1, UI/graphics contrast) — same as in light
   mode.

**No automatic switching:** Power BI Desktop/Service have no system
dark-mode switching for reports — a `theme.json` applies fixed to the whole
report. Two options: (a) deliberately pick just *one* mode for the report,
or (b) maintain two report copies (identical layout, one theme each). Either
way, deliver both `theme.json` files (light + dark) to `design-out/` so the
human has the choice.
