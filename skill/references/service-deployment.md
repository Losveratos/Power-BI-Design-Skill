# Service Deployment — Future Extension (Not in v1)

> **Status:** Documented future extension, **deliberately not implemented**.
> No script here talks to the Fabric REST API or calls
> `semantic-link-labs` — consistent with the "future extension" note. The
> equivalent guidance lives in the `chartkitchen-report` skill of the
> Daten-WG PowerBI-Kitchen repo (https://github.com/Losveratos/PowerBI-Kitchen-):
> harden the file-based path (`pbir-integration.md`) against real PBIPs
> first, then extend here.

## 1 · When Service Instead of File-Based Path

The file-based path assumes Desktop plus one report at a time. Service
level becomes relevant once: **many reports at once** need to be deployed
(theme rollout across 20+ reports), **no Desktop is in the loop** (CI
runner, Fabric notebook), a **CI/CD pipeline** should auto-deploy theme
changes after merge, or reports are **already in the workspace** (no
longer local). Otherwise: stay with the file-based path — simpler, no
auth setup.

## 2 · The Three Paths

### A. Fabric REST Items API (`getDefinition` / `updateDefinition`)

**Use case:** programmatic deployment of a report definition from a
pipeline.

**Verified:** the generic Items API `POST /v1/workspaces/{wsId}/items/{itemId}/getDefinition`
resp. `.../updateDefinition`; for reports there's additionally a
type-specific variant (`.../reports/{reportId}/...`) with the same
payload envelope. Payload: `definition.parts[]` with `path`, `payload`
(Base64), and `payloadType: "InlineBase64"` — the same file map as in
`pbir-integration.md` (`report.json`, `pages.json`, `page.json`,
`visual.json`), just Base64-encoded instead of files on disk.
`updateDefinition` **replaces the entire definition** — all parts
(changed and unchanged) must be included, or parts get lost; no partial
update. `.platform` metadata only with `?updateMetadata=true`.
**Important limitation:** if the report references its semantic model via
`byPath` (the default for Git exports in the same workspace), the REST
API rejects that — for API deployment it must be rewritten to
`byConnection` (connection string with model ID). Confirmed via open
issues in the `microsoft/fabric-cicd` repo (#637, #436).

**UNVERIFIED:** exact API version/LRO polling behavior; whether custom
visuals (ChartKitchen) pass through unchanged — `learn.microsoft.com` is
blocked by the proxy, the facts above come from search-result snippets of
those pages plus independent confirmation via
`raw.githubusercontent.com/microsoft/skills-for-fabric/main/common/ITEM-DEFINITIONS-CORE.md`.
Verify against a test workspace before production use.

### B. `semantic-link-labs` (Python, Fabric Notebook)

**Use case:** deployment from a Fabric notebook, runs with notebook
identity, no separate auth setup.

**Verified** (from README + wiki code examples on
raw.githubusercontent.com/microsoft/semantic-link-labs): installation via
`%pip install semantic-link-labs`. Module `sempy_labs.report`
(`from sempy_labs import report as rep`) offers, among others:

- `connect_report(report=…, workspace=…, readonly=False)` as a
  context manager → `ReportWrapper`. On it, **`rpt.set_theme(theme_file_path=…)`**
  — the direct service-side counterpart to the Desktop theme import: the
  `theme.json` produced here could be applied unchanged with it.
- `rpt.migrate_report_level_measures(...)` — moves report-level measures
  into the model.
- `rep.report_rebind(report=…, dataset=…, report_workspace=…, dataset_workspace=…)`.
- `rep.save_report_as_pbip(report=…, workspace=…, …)` — service → PBIP
  round trip.
- `rep.run_report_bpa(report=…, workspace=…)` — Best Practice Analyzer.

**UNVERIFIED:** `create_report_from_reportjson` /
`update_report_from_reportjson` are listed in the package docs as part of
the module, but the signature and whether individual `visual.json` files
(rather than just `report.json`) can also be written with them was not
inspectable (readthedocs.io is blocked).

### C. Deployment Pipelines / Git Integration

**Use case:** a durable Dev → Test → Prod flow instead of ad-hoc
scripting: PBIP in Git, workspace bound to a branch, Deployment Pipelines
promote between stages.

**Verified:** Git integration binds a Fabric workspace to a branch (Azure
DevOps, and since 2025 also GitHub); commits in the workspace ↔ repo stay
in sync. Only with Fabric workspaces, not classic Premium workspaces.
Common architecture: Git integration keeps Dev in sync with `main`,
Deployment Pipelines take over Test/Prod. A separate Microsoft package,
`microsoft/fabric-cicd` (`pip install fabric-cicd`), deploys PBIP folders
directly via the REST API — an alternative to native Git binding. **When
report and model live in the same workspace, Git integration exports the
model reference as `byPath` by default** — exactly the form that path A
rejects; not a problem here, because workspace sync takes over instead of
a raw `updateDefinition` call.

**UNVERIFIED:** whether Deployment Pipelines pass through PBIR including
custom visuals 1:1; the level of detail behind the "only partially
supported" claim for Direct Lake models from secondary sources
(powerbiconsulting.com, draftbi.com) — not verified against the original
source (learn.microsoft.com, blocked).

## 3 · How the Skill's Artifacts Would Flow In

The existing scripts wouldn't change — only the last step (opening
Desktop) would be replaced by an upload:

1. `theme.json` remains the source of truth for colors/typography/defaults,
   regardless of the target path.
2. `scripts/bulk_restyle.py` already works **purely file-based** against
   PBIR `visual.json` files — no GUI access in the script, so
   pipeline-ready without rewriting: provide the definition via
   `getDefinition` (A) or Git checkout (C) as a PBIP folder → decode
   Base64 → run `bulk_restyle.py --preset … --apply` unchanged → re-encode
   the result as Base64 and upload via `updateDefinition` (A) or commit +
   sync (C).
3. For pure theme rollouts with no structural change, path B is the most
   direct route: `theme.json` unchanged into `set_theme(theme_file_path=…)`,
   no Base64 detour.
4. The linter (`bulk_restyle.py --check`) remains the quality gate before
   every upload/commit — as a pipeline step instead of a manual call.

## 4 · Guardrails

- **Never deploy directly into a production workspace.** Dev/copy first,
  verify there (report opens, visuals load, bindings intact), only then
  promote via Deployment Pipeline to Test/Prod.
- Same backup discipline as the file-based path: before every
  `updateDefinition`, pull the current definition via `getDefinition` and
  store it as a backup (equivalent to risk-ladder step 4 in
  `pbir-integration.md`).
- `updateDefinition` replaces the entire definition — always use the full
  set of parts from `getDefinition` as the base, only patch the affected
  ones.
- Check the `byPath` vs. `byConnection` trap (path A) before the first
  production run, not only after it fails.
- Auth/credentials don't belong in this skill directory — a separate
  setup managed by the respective team.
- When API/package behavior is unclear, don't guess — verify against a
  test workspace before building it into a pipeline.

## 5 · Status

Documentation of a possible future extension, **no working code**. In v1
(as in `chartkitchen-report` and `deploy-to-powerbi`) deliberately not
implemented — the file-based path is hardened against real PBIPs first.
Entry point when needed: path B (`semantic-link-labs`, lowest barrier,
runs in the notebook with no separate auth setup), only then path A or C.
