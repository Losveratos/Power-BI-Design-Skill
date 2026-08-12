# PBIR Integration — Working Against the Project File (and What "API" Means)

## Reality Check: Which Interfaces Actually Exist?

| Path                               | Can Do Report Layout? | Use in This Skill                     |
| --------------------------------- | ------------------- | ------------------------------------ |
| **PBIP/PBIR files** (text JSON)   | ✅ yes               | **the path this skill takes**        |
| Power BI Desktop "API"            | ❌ doesn't exist for reports — External Tools speak XMLA to the local Analysis Services instance and thereby only reach the **semantic model** (measures, tables), not the layout | not usable for layout |
| Fabric/Power BI REST APIs (Service) | partially (definition import/export) | future extension, not v1 |
| Theme import in Desktop           | Colors/typography/defaults | always the first lever               |

Consequence: "Working against Power BI" concretely means: **working on the
PBIP files** while Desktop is closed (Desktop keeps the files open and
overwrites external changes on save). Always the same flow:
close Desktop → change files → open Desktop → verify.

## File Map (Short Version)

```
<Name>.Report/definition/
├── report.json                  ← report metadata/filters
├── pages/pages.json             ← page order, active page
└── pages/<pageName>/
    ├── page.json                ← name, displayName, width/height, visibility
    └── visuals/<visualName>/visual.json  ← position + type + formatting
```

Every file carries a `$schema` URL, with the version embedded in the URL
(e.g. `…/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json`).
When creating new files, take the URL **from an existing file of the same
report**. Rather than inventing JSON from scratch, replicate an existing
`visual.json` from the target report as the starting point — this is the
reference-instance principle. The full walkthrough of that trick (detailed
structure, step-by-step replication) lives in the `chartkitchen-report`
skill of the Daten-WG PowerBI-Kitchen repo:
https://github.com/Losveratos/PowerBI-Kitchen- — it applies here 1:1, also
for standard visuals (textbox, shape, button).

## Verified PBIR Facts for Formatting (Basis for `bulk_restyle.py`)

- **Position** (root level of `visual.json`): `x`, `y`, `z` (layer),
  `width`, `height`, optionally `tabOrder`.
- **Container formatting** (title, background, border, shadow) lives in
  **`visual.visualContainerObjects`** — object name → array of
  `{ "properties": { … } }`. Two pitfalls: the same properties under
  `visual.objects` are **silently ignored**; at the root level,
  `visualContainerObjects` is an error.
- **Literal encoding** `{"expr": {"Literal": {"Value": …}}}`:

  | Type    | Format            | Example                       |
  | ------- | ----------------- | ----------------------------- |
  | Boolean | no suffix         | `"true"` / `"false"`          |
  | Double  | suffix `D`        | `"14D"` (e.g. fontSize)       |
  | Integer | suffix `L`        | `"50L"` (pixels, transparency) |
  | String  | single-quoted     | `"'#FFFFFF'"`; double inner `'` |
  | Fill    | nested            | `{"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}}` |

  Which numeric suffix a given property expects isn't documented
  everywhere — `bulk_restyle.py` **learns it from existing examples in
  the report** and otherwise falls back to documented defaults.

## Risk Ladder for Write Access

From harmless to risky — the skill stays as far up this ladder as possible:

1. **Writing `design-out/`** (theme, spec, steps, zones.json) — always allowed.
2. **Importing a theme** — done by the human in Desktop, risk-free.
3. **Adding a new page** (components page, sample page): additive,
   existing pages untouched; folder + `pages.json` entry. Only on
   explicit request, with a backup.
4. **Changing container formatting of existing visuals** (`bulk_restyle.py`):
   only changes `visualContainerObjects`, never query/field bindings. Only
   on explicit request, with a backup, dry run first.
5. **Structurally rebuilding visuals/pages** — this skill does not do
   that; use Desktop or the `chartkitchen-report` path with a reference
   instance for that.

Backup means: a Git commit of the PBIP folder **before** step 3/4 (without
Git, `bulk_restyle.py` creates backup copies under `design-out/backup-…/`).
After every write: open in Desktop; if the report doesn't load, restore
the backup and document the case as Desktop click-steps in STEPS.md
instead of trying again.

## Bulk Changes: Theme First, Then Script

Maintainability comes from the right order:

1. **Can the theme do it?** (Colors, font sizes, visual defaults such as
   shadow/background/corners for *not manually overridden* visuals)
   → change `theme.json`, re-import. One file, all pages.
2. **Manually overridden visuals** don't listen to the theme — this is
   where `scripts/bulk_restyle.py` comes in: sets container properties
   across all `visual.json` files (filterable by page/visual type) or
   **removes the manual overrides** (`--strip`) so the theme takes effect
   again — the most sustainable option.
3. **Update the components page** (see `components-page.md`), so new
   items get copied correctly right away.

Example "no shadows, light backgrounds, slightly rounded corners":

```bash
python scripts/bulk_restyle.py path/to/project --preset modern-soft          # view dry run
python scripts/bulk_restyle.py path/to/project --preset modern-soft --apply  # write
```

## Linter (`bulk_restyle.py --check`)

Check mode never writes — it validates the report against the spec:
positions on the 8px grid, shadow ban, font families/sizes (min. 9pt),
missing `tabOrder` (`--require-taborder`), visuals outside the content
zone (`--zones design-out/zones.json` — this file is created by the skill
alongside the AGENT-BRIEF). Exit code ≠ 0 on violations — as a quality
gate before every publish, and as concrete feedback for agents that have
built pages.
