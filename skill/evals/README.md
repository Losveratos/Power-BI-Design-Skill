# Trigger Eval Set · powerbi-design-framework

`trigger-evals.json` contains 20 realistic user queries (10x
`should_trigger: true`, 10x `should_trigger: false`) used to test and
optimize this skill's SKILL.md frontmatter `description` for trigger
accuracy.

## Structure of the Set

- **Positive cases (10):** cover the core trigger scenarios — new page
  scaffold/layout, pulling branding from a website/deck, theme/colors,
  filter panel/navigation, "make charts/report nicer/more consistent",
  bulk restyle ("remove all shadows everywhere"), design review/linting,
  IBCS page layout, dark mode, components/template page.
- **Negative cases (10):** deliberately written as *near-misses* against
  the four neighboring skills, not as obviously unrelated topics: a plain
  DAX question, Deneb/Vega spec debugging (→ `vega-charts`), building a
  ChartKitchen report from data (→ `chartkitchen-report`), inserting a
  single Deneb template into a PBIP (→ `deploy-to-powerbi`), PowerPoint
  slide design, a data modeling question, a performance problem, a
  YouTube channel update (→ `kitchen-update`), website design with no
  Power BI relation, a Power BI licensing question.

Language: predominantly German (some queries in lowercase, colloquial
phrasing, typos — the queries intentionally stay mixed German/English, as
they are written to test real user phrasing rather than textbook
sentences), 3 queries in English. Includes file-name and company context
(e.g. `Sales.pbix`, `Umsatz-Dashboard.pbix`, a Q3 deck) so the queries
read like real chat input rather than textbook sentences.

## How to Use the Set Later

Once a human has reviewed the queries for content, run the optimization
loop from the `skill-creator` skill:

```bash
python3 /root/.claude/skills/synced/skill-creator/scripts/run_loop.py \
  --eval-set /home/user/PowerBI-Kitchen-/.claude/skills/powerbi-design-framework/evals/trigger-evals.json \
  --skill-path /home/user/PowerBI-Kitchen-/.claude/skills/powerbi-design-framework \
  --model <model-id>
```

Useful extra flags: `--holdout 0.4` (train/test split), `--runs-per-query
3` (multiple runs to control for variance), `--results-dir …` (persist
results including an HTML report). See `--help` or the `skill-creator`
SKILL.md for details.

The loop iteratively changes the frontmatter `description`, measures the
trigger rate on positive/negative cases per iteration, and keeps the best
version. Please review any changes to `description` in the SKILL.md diff
afterward, before committing.

## Status

**The loop has not been run yet** (token budget deliberately conserved).
That happens only after a human has reviewed and approved the 20 queries
above for content — in particular whether the negative cases really
should be "no trigger", and whether the positive cases are missing any
important scenarios.
