# Power BI Design Skill

A [Claude Code](https://claude.com/claude-code) skill that helps Power BI
developers — human **and** agentic — build report pages faster and more
consistently. A short, native interview (or a branding source such as a
company deck, website, or logo) produces a binding page scaffold: colors,
typography, an 8-px grid, the page "chrome" (navigation, logo, footer,
filter panel), and a tile structure — delivered as an importable
`theme.json`, a human-readable design spec, and a machine-readable agent
brief.

> The German original of this skill lives in the
> [Daten-WG PowerBI-Kitchen repo](https://github.com/Losveratos/PowerBI-Kitchen-)
> (`.claude/skills/powerbi-design-framework/`), alongside optional companion
> skills (ChartKitchen report builder, Deneb template deployment). This repo
> is the standalone English edition — it works without them.

## What it does

| Capability | How |
| --- | --- |
| **Scaffold interview** | ~10 short questions with sensible defaults ("just use the standards" works): purpose, canvas size, navigation, logo, footer, filter panel side, KPI tiles, accessibility level |
| **Branding extraction** | Derives color roles (ink, accent, backgrounds, gray ladder, data colors) from a PowerPoint theme, a website's CSS, or a logo's pixels — instead of asking for hex codes |
| **Modern design rules** | 8-px grid, Gestalt principles, visual hierarchy, tile rules, type scale, and the named default look **modern-soft** (no shadows, light backgrounds, softly rounded corners) |
| **Accessibility, measured** | WCAG AA contrast checks with automatic fix suggestions (`scripts/check_contrast.py`), minimum font sizes, color-blind-safe rules, tab order, alt text |
| **IBCS mode** | Notation over branding: AC/PY/PL/FC semantics, and structural elements (title block, notation band, variance strip, comment column) as named layout slots |
| **Component page** | A hidden `_Design-System` page built on atomic-design levels — buttons in all states, KPI tile, header with logo, filter panel — to copy from instead of re-formatting |
| **Bulk restyle + linter** | `scripts/bulk_restyle.py` applies design changes across every page of a PBIP/PBIR project ("remove all shadows, round the corners") and lints reports against the spec |
| **Visual feedback loop** | `scripts/render_wireframe.py` renders SVG wireframes of every report page straight from the PBIR coordinates — agents can *see* their layout without opening Power BI Desktop |
| **Dark mode** | A second, contrast-validated theme template with the same color-role logic |
| **CI gate** | GitHub Actions + pre-commit templates that run the linter and contrast checks on every change |

Safety model throughout: **prepare + plan**. The skill never writes into
your `*.Report/` files unasked — it hands over artifacts in `design-out/`
and you confirm in Power BI Desktop. Direct PBIR writes happen only on
explicit request, dry-run first, with automatic backups.

## Installation

The skill is the `skill/` folder of this repo. Claude Code discovers skills
in `.claude/skills/` (per project) or `~/.claude/skills/` (personal).

**Per project** (recommended — versioned with your report repo):

```bash
git clone https://github.com/Losveratos/Power-BI-Desgin-Skill.git
mkdir -p your-project/.claude/skills
cp -r Power-BI-Desgin-Skill/skill your-project/.claude/skills/powerbi-design-framework
```

**Personal** (available in every project):

```bash
cp -r Power-BI-Desgin-Skill/skill ~/.claude/skills/powerbi-design-framework
```

Requirements: Claude Code, Python 3.10+ (standard library only — no pip
installs), and for the PBIR features a report saved as a **Power BI
project** (`File → Save as → Power BI project file` in Desktop; `.pbix`
binaries are not supported).

## Quick start

Open Claude Code in your project and say something like:

- *"Build me a page scaffold for a management report — derive the colors
  from https://my-company.com"*
- *"Create a Power BI theme from our brand deck `brand.pptx`, filter panel
  on the left, 3 KPIs, otherwise use the standards"*
- *"Remove all shadows in my report and give every visual softly rounded
  corners"* (bulk restyle on a PBIP)
- *"Check my report design"* (linter + wireframes)
- *"IBCS layout for a plan/actual page with a comment column"*

The skill triggers automatically on requests like these; you don't need to
name it.

### What you get (`design-out/`)

| File | Purpose |
| --- | --- |
| `theme.json` (+ `theme-dark.json`) | Import in Desktop: **View → Themes → Browse for themes** |
| `DESIGN-SPEC.md` | The design system for humans: color roles with measured contrast, type scale, zone dimensions, wireframe, do/don't |
| `AGENT-BRIEF.md` | Compact rule set for coding agents: zones as `x,y,w,h`, tile slots, mandatory visual properties, forbidden deviations |
| `zones.json` | The zones machine-readable — feeds the linter and wireframe renderer |
| `STEPS.md` | Exact Desktop click-steps for everything a theme cannot do (chrome, filter panel, bookmarks, tab order) |
| `wireframes/*.svg` | Rendered page wireframes for visual review |

## Using the scripts directly

All scripts are dependency-free Python and also work standalone, outside
Claude Code:

```bash
# WCAG contrast: single pair, whole palette, or gray ladder
python skill/scripts/check_contrast.py "#1F2937" --bg "#FAFAFB"
python skill/scripts/check_contrast.py --palette design-out/palette.json
python skill/scripts/check_contrast.py --ladder "#1F2937" --bg "#FAFAFB"

# Bulk restyle a PBIP project (dry-run by default; --apply writes with backup)
python skill/scripts/bulk_restyle.py path/to/project --preset modern-soft
python skill/scripts/bulk_restyle.py path/to/project --preset modern-soft --apply

# Remove manual overrides so the theme wins again
python skill/scripts/bulk_restyle.py path/to/project --strip dropShadow,border --apply

# Lint the report against the spec (never writes; exit code 1 on violations)
python skill/scripts/bulk_restyle.py path/to/project --check \
  --zones design-out/zones.json --fonts "Segoe UI,Segoe UI Semibold"

# Render SVG wireframes of every page
python skill/scripts/render_wireframe.py path/to/project \
  --zones design-out/zones.json --html
```

Close Power BI Desktop before applying writes — Desktop holds the files
open and overwrites external changes on save. Open the project afterwards
to verify; every `--apply` keeps a backup under `design-out/backup-…/`.

## Repo structure

```
skill/
├── SKILL.md                       ← entry point Claude Code loads
├── references/                    ← detail knowledge, loaded on demand
│   ├── design-rules.md            ← grid, Gestalt, hierarchy, type, a11y
│   ├── chrome-layouts.md          ← zone layouts with exact coordinates
│   ├── branding-extraction.md     ← colors from pptx / website / logo
│   ├── theme-json.md              ← theme structure + dark mode
│   ├── ibcs-mode.md               ← IBCS notation + named structure slots
│   ├── components-page.md         ← atomic-design component page
│   ├── pbir-integration.md        ← verified PBIR facts + risk ladder
│   ├── ci-gate.md                 ← linter as CI/pre-commit gate
│   └── service-deployment.md      ← Fabric REST / semantic-link-labs (outlook)
├── scripts/                       ← dependency-free Python tools
├── assets/
│   ├── theme-template.json        ← light theme base (AA-validated)
│   ├── theme-template-dark.json   ← dark theme base (AA-validated)
│   ├── pbir-snippets/             ← real visual.json examples (textbox, button, shape, image)
│   └── ci/                        ← GitHub Action + pre-commit templates
└── evals/                         ← trigger test queries for skill tuning
```

## License

MIT — see [LICENSE](LICENSE).
