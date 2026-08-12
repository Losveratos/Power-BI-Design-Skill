# Components Page — Atomic Design in Power BI

A hidden page called **`_Design-System`** in the report, where all building
blocks sit ready-formatted. Developers (and agents) **copy** from there
instead of reinventing formatting — Ctrl+C/V between pages preserves
position and format exactly. This is the most effective consistency lever
after the theme, and it makes maintenance easy: change a component on the
system page → the next copy picks up the new version.

## Atomic design levels mapped to Power BI

| Level      | Power BI equivalent                             | Examples on the page                          |
| ----------- | -------------------------------------------------- | ----------------------------------------------- |
| Atoms       | individual elements                                | Textbox H1/H2/Body/Caption, button (3 states), "card" shape, color swatch, divider, logo placeholder |
| Molecules   | group of 2–4 atoms                                 | KPI tile (card + label + value + delta), nav button with icon, slicer with title |
| Organisms   | a complete chrome zone as a group                  | header band (logo + title + nav), filter panel (panel + slicer stack + reset), footer, KPI row |
| Template    | the sample page itself                              | an empty "template page" with all zones, duplicated as a whole |

## Naming convention (maintain in the Selection pane!)

Every element/group gets a descriptive name in the **Selection pane**
(View → Selection) following the pattern `level/name-variant`:

```
atom/h1-title          atom/btn-nav-default    atom/swatch-accent
atom/h2-section         atom/btn-nav-active     atom/card-bg
mol/kpi-tile            atom/btn-nav-disabled   atom/logo-placeholder
org/header-band         org/filter-panel        org/footer
```

Why this matters: display names from the Selection pane are written by
Desktop into the PBIR files (the exact field varies by schema version — after
naming, verify once with `grep -rl "mol/kpi-tile" …/visuals/`). This lets an
agent **find the component in the filesystem** and replicate its
`visual.json` folder as a template — the reference-instance trick from the
optional `chartkitchen-report` companion skill (Daten-WG PowerBI-Kitchen
repo), applied to design building blocks. If `grep` finds nothing, maintain
a mapping table `Component → visuals/<folder-name>` in the AGENT-BRIEF
instead — same effect, one more layer of indirection.

## What belongs on the page (minimum set)

1. **Color swatches:** one shape per color role with the hex value and role
   as its label (ink/accent/bg/bg-card/gray ladder/data colors) — the page
   documents itself.
2. **Typography rows:** one textbox per text class with a plain-language
   name + size ("H1 · 18pt Semibold").
3. **Buttons in all states:** nav button default/hover/active/disabled
   (Power BI buttons have state-based formatting — set it up once cleanly,
   then just copy), filter reset, filter toggle (funnel icon), info button.
4. **KPI tile molecule** in the agreed geometry (plus a "critical/
   highlighted" variant).
5. **Chrome organisms:** header band with logo placeholder, filter panel,
   footer — grouped, at the exact spec coordinates.
6. In IBCS mode, additionally: `slot/title-block`, `slot/notation-band`,
   `slot/comment-col` patterns (numbered comment with reference line).

## Creating it — two approaches

**Approach A · Desktop (default, describe in STEPS.md):** create the page,
build elements per spec, name them, group them, hide the page via "Hide
page." One-time effort ~30–45 min, then just copy afterward.

**Approach B · PBIR-generated (only on explicit request):** the skill writes
the page as a new folder under `*.Report/definition/pages/` plus an entry in
`pages.json`. This is **additive** (existing pages remain untouched) and
therefore the lowest-risk kind of PBIR write access — the rules from
`pbir-integration.md` still apply: back up/commit first, Desktop closed,
then open in Desktop afterward and verify. Textboxes, shapes, and buttons
are standard visuals; replicate their `visual.json` structure from an
existing instance in the report — don't guess it. If the target report
doesn't yet contain an instance, real, cleaned-up examples live under
[`../assets/pbir-snippets/`](../assets/pbir-snippets/) (textbox, action
button, shape, image — provenance and caveats in the README there; check the
`$schema` version against the target report!). Mark the page as hidden in
`page.json` (carry over the visibility field the way Desktop writes it).
Review the result with `scripts/render_wireframe.py` before opening Desktop.

## Usage & maintenance

- **Building a new page:** duplicate the template page (template level) or
  copy organisms individually; place visuals into the content slots from
  the AGENT-BRIEF.
- **Changing the design:** first check whether the theme can do it (if so,
  do it there!); otherwise change the component on `_Design-System` and
  roll it out to existing instances with `scripts/bulk_restyle.py`.
- **Drift control:** `bulk_restyle.py --check` reports visuals that deviate
  from the component/spec rules (shadow on, wrong font, off the grid …).
- The page stays in the published report (hidden) — it doesn't get in the
  way and documents the design system directly on the object. Anyone who
  doesn't want to ship it in the service removes it deliberately before
  publishing.
