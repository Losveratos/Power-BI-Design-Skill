# PBIR Snippets — Reference Library for Standard Visuals

A small collection of real `visual.json` examples for the four most common
standard visuals on a components page (path B from
`../../references/components-page.md`): textbox, action button, shape,
image. No self-invented JSON — every file comes from a public repository
and was only neutralized for text/color values (see "What was changed"
per snippet).

## Provenance

All four files come from:

**Repo:** [`data-goblin/power-bi-agentic-development`](https://github.com/data-goblin/power-bi-agentic-development)
(plugin marketplace for Power BI agent skills, GPL-3.0)
**Path:** `plugins/pbip/skills/pbir-format/examples/visuals/`
**Index:** [`examples/visuals/__index.md`](https://github.com/data-goblin/power-bi-agentic-development/blob/main/plugins/pbip/skills/pbir-format/examples/visuals/__index.md)
lists 54 standalone `visual.json` examples there in total, across two
subfolders `default/` (minimal, theme only) and `formatted/` (with
individual formatting).

| Snippet here | Source file in repo (raw URL) |
| --- | --- |
| `textbox.visual.json` | `.../examples/visuals/formatted/textbox.json` — [raw](https://raw.githubusercontent.com/data-goblin/power-bi-agentic-development/main/plugins/pbip/skills/pbir-format/examples/visuals/formatted/textbox.json) |
| `action-button.visual.json` | `.../examples/visuals/formatted/actionButton.json` — [raw](https://raw.githubusercontent.com/data-goblin/power-bi-agentic-development/main/plugins/pbip/skills/pbir-format/examples/visuals/formatted/actionButton.json) |
| `shape.visual.json` | `.../examples/visuals/formatted/shape.json` — [raw](https://raw.githubusercontent.com/data-goblin/power-bi-agentic-development/main/plugins/pbip/skills/pbir-format/examples/visuals/formatted/shape.json) |
| `image.visual.json` (bonus) | `.../examples/visuals/default/image.json` — [raw](https://raw.githubusercontent.com/data-goblin/power-bi-agentic-development/main/plugins/pbip/skills/pbir-format/examples/visuals/default/image.json) |

**Schema version of the found files:** `$schema` points in all four files
to
`https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.7.0/schema.json`
— **carried over unchanged**, as required in `pbir-integration.md`. This
is the schema version the source report was saved with; it must be
reconciled against the other files of the target report before use (see
warnings below).

For `action-button.visual.json` and `shape.visual.json`, the original
`name` values were Desktop-generated random IDs
(e.g. `4e7f3679ee7ce6d4b914`) — replaced here with descriptive placeholder
names (`action_button_example`, `shape_example`), and the position
coordinates rounded to 2 decimal places (purely cosmetic, no structural
change). `textbox.visual.json` and `image.visual.json` already had
descriptive names from the source repo's default/formatted example set
and were left unchanged.

## What Was Changed (Text/Color → Neutral Placeholders)

- **`textbox.visual.json`:** the texts "Sales Overview" / "Year-to-date
  performance against targets" → `Example Title` / `Example Subtitle`.
  Text colors `#252423` / `#605E5C` → `#1F2937` (darker ink placeholder) /
  `#6B7280` (muted placeholder). Structure (title + subtitle as two
  paragraphs, `visualContainerObjects` turns off the card's own
  title/background/border) unchanged.
- **`action-button.visual.json`:** no literal text/colors in the original
  (fill color runs via `ThemeDataColor`, not a literal hex) — only
  name/position cleaned up, otherwise found as-is.
- **`shape.visual.json`:** tooltip and header literal colors
  `#E6DFCF` / `#3B4244` / `#F4F4F4` → neutral placeholder pair
  `#F3F4F6` (light) / `#1F2937` (dark) / `#FFFFFF`. The tile background
  color itself runs via `ThemeDataColor` (theme slot 0) and was left
  untouched.
- **`image.visual.json`:** `ItemName` of the referenced Registered
  Resource `logo.png` → `logo-placeholder.png` (see warning below, this
  is not an automatically working value).

## What's Missing

No fifth type was added as "found" that isn't — there are only the four
files listed above. If further standard visual types are needed later
(e.g. `slicer`, `card`, `basicShape` variants like arrow/line, or an
action button with a visible `text` object instead of just icon/fill),
they are **not included here** and would need to be either exported from
Desktop from a real report, or pulled from `examples/visuals/__index.md`
in the source repo (per the index, 50 more examples live there, likely
including slicer and card variants, but not individually
verified/downloaded for this set).

## Warnings — Read Before Use

1. **The reference-instance principle takes priority:** these snippets
   are starting points for the case where the target report doesn't yet
   contain **any** instance of the given visual type. As soon as the
   target report already has a textbox/button/shape, **that existing
   instance is always the better template** (see `pbir-integration.md`
   and the `chartkitchen-report` skill of the Daten-WG PowerBI-Kitchen
   repo, https://github.com/Losveratos/PowerBI-Kitchen-) — especially
   because it's guaranteed to work with the correct schema version and
   the same `ThemeDataColor` slots of the target report.
2. **Adjust before inserting:**
   - Assign a unique `name` (must be unique report-wide — avoid
     collisions with existing visual names).
   - Adjust `position` (x/y/z/height/width/tabOrder) to the target page
     and the spec's 8px grid; the coordinates included here come from
     the source report and won't fit anywhere automatically.
   - Reconcile the `$schema` version against an **existing** `visual.json`
     of the same target report (e.g. `grep '"$schema"' path/to/Report/definition/pages/*/visuals/*/visual.json | sort -u`)
     — if the version differs, when in doubt use the target report's
     version, not the one shipped here.
   - For `shape.visual.json` and `action-button.visual.json`:
     `ThemeDataColor` references (`ColorId: 0`, `ColorId: 2`) point to
     slots in the **source theme** — the target report may have
     different colors at the same slot numbers; check against
     `theme.json` of the target report.
   - For `image.visual.json`: `ItemName` references a **Registered
     Resource** (`RegisteredResources` package) — the image must
     actually be registered in the target report under exactly this
     name (Desktop: format pane → Image → Browse, which is how Desktop
     creates the resource entry). Without a matching registration the
     image stays empty/broken.
3. **Verify in Desktop after inserting:** open Desktop, look at the page,
   check the selection pane (name correct, no unwanted overlaps), and —
   if the skill previously ran with `bulk_restyle.py --check` — re-run
   the check to make sure the new visuals meet the spec rules (grid,
   font sizes, no shadow, `tabOrder`).
