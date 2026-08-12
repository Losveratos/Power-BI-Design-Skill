# CI Gate — Enforcing Design Consistency Permanently

## Why

A design system erodes without a gate: any manual fix in Power BI Desktop
or any visual built by an agent can introduce shadows, wrong fonts, or
positions outside the content zone — unnoticed until someone happens to
look. Agents (including this skill itself) also need automated feedback:
"violation found" as an exit code is something an agent can react to in
its next step; a human manually clicking through reports during review is
not. Both scripts (`bulk_restyle.py --check`, `check_contrast.py
--palette`) are already CI-ready: pure stdlib Python, exit code ≠ 0 on
violations, no network access.

## Setup — Variant A: GitHub Actions

1. Copy the scripts into the report repo:
   ```bash
   mkdir -p tools/design
   cp .claude/skills/powerbi-design-framework/scripts/bulk_restyle.py tools/design/
   cp .claude/skills/powerbi-design-framework/scripts/check_contrast.py tools/design/
   ```
2. Copy `assets/ci/design-lint.yml` to `.github/workflows/design-lint.yml`.
3. In the `env:` block at the top of the file, adjust `TOOLS_DIR`,
   `REPORT_PATH`, and `ALLOWED_FONTS` to match your own repo layout.
4. Generate `design-out/zones.json` and `design-out/palette.json` once
   with the `powerbi-design-framework` skill (step "store artifacts")
   and commit them — without them, the workflow skips the checks (see
   below).
5. Create a commit/PR — the workflow runs on `pull_request` and on
   `push` to the default branch.

## Setup — Variant B: Local Pre-Commit Hook

1. Copy the scripts into `tools/design/` as above (if not already done).
2. Install the hook:
   ```bash
   cp .claude/skills/powerbi-design-framework/assets/ci/pre-commit.sh .git/hooks/pre-commit
   chmod +x .git/hooks/pre-commit
   ```
3. Adjust the paths at the top of the script (`TOOLS_DIR`, `REPORT_PATH`,
   `ALLOWED_FONTS`) as needed. The hook then runs before every
   `git commit`.

## What the Checks Verify

- **`bulk_restyle.py --check`**: positions on the 8px grid, visuals
  outside the content zone (`--zones`), forbidden shadows
  (`dropShadow.show`), font sizes below the minimum, disallowed
  `fontFamily` values (`--fonts`), optionally missing `tabOrder`
  (`--require-taborder`).
- **`check_contrast.py --palette`**: every color pair from `palette.json`
  against WCAG AA (4.5:1 for normal text, 3:1 for large text/UI), with a
  fix suggestion on FAIL.

## Reading Violations

Both scripts print one line per violation with page/visual or color pair
and ratio, followed by a summary. For `check_contrast.py`, a FAIL is
immediately followed by a fix suggestion (the nearest color shade that
reaches the target ratio) — which you can copy 1:1 into `palette.json`.
Exit code 0 means "clean", ≠ 0 means "at least one violation", regardless
of how many there are.

## Limits

The linter checks **geometry and format rules** (grid, zones, fonts,
shadow flag, contrast values) — it has no notion of aesthetics: whether a
layout actually looks balanced, whitespace feels right, or a color choice
fits the corporate design is invisible to the gate. `render_wireframe.py`
(built by a colleague in parallel) is intended for the visual review — an
image of the page instead of a rule list, for the kind of look no script
can replace. Until then, manually opening the report in Power BI Desktop
remains necessary before a report counts as finished.
