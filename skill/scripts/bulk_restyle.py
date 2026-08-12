#!/usr/bin/env python3
"""Bulk restyle & design linter for Power BI PBIR reports.

Operates on `*.Report/definition/pages/*/visuals/*/visual.json` and changes
ONLY container formatting (shadow, background, border/corners) under
`visual.visualContainerObjects` — never query/field bindings. Safety model:

  * Default is DRY-RUN: shows planned changes, writes nothing.
  * --apply writes — but first every changed file is backed up to
    design-out/backup-<time>/ (a Git commit beforehand is still recommended).
  * Power BI Desktop must be CLOSED while doing this (otherwise it locks the files).

Modes:
  Restyle:  bulk_restyle.py <report-path> --preset modern-soft [--apply]
            bulk_restyle.py <report-path> --rules rules.json [--apply]
  Strip:    bulk_restyle.py <report-path> --strip dropShadow,border [--apply]
            (removes manual overrides so the THEME takes effect again —
             the most durable bulk change)
  Linter:   bulk_restyle.py <report-path> --check [--zones zones.json]

Presets:
  modern-soft  shadow off, tile background white, subtle outline, radius 8
  ibcs         shadow off, background white, no border, radius 0

rules.json format (overrides/extends the preset; same object order):
  { "set": [ {"object": "dropShadow", "property": "show", "value": false},
             {"object": "border", "property": "radius", "value": 8},
             {"object": "background", "property": "color",
              "value": "#FFFFFF", "kind": "fill"} ] }

zones.json format (for --check; comes from the AGENT BRIEF):
  { "content": [16, 72, 1032, 616], "ignorePages": ["_Design-System"] }

PBIR facts this script relies on (verified):
  * Container formatting lives in `visual.visualContainerObjects`;
    the same properties under `visual.objects` are SILENTLY ignored,
    and `visualContainerObjects` at the root level is an error.
  * Literal encoding: {"expr":{"Literal":{"Value": …}}} with
    Bool "true"/"false" · Double "14D" (e.g. fontSize) · Integer "50L"
    (e.g. pixels, transparency) · String "'…'" (inner ' doubled).
    Where the report itself already contains an example for a property,
    its suffix is reused (replicate rather than guess).
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import shutil
import sys
import time
from pathlib import Path

FILL_PROPERTIES = {"color"}  # properties encoded as Fill { solid: { color } }

# Suffix per property if the report doesn't contain its own example
# (D = Double, L = Integer, "" = none). Source: PBIR examples/schema.
NUMBER_SUFFIX_DEFAULTS = {"fontSize": "D", "transparency": "L", "radius": "L"}
NUMBER_SUFFIX_FALLBACK = "D"

PRESETS = {
    "modern-soft": [
        {"object": "dropShadow", "property": "show", "value": False},
        {"object": "background", "property": "show", "value": True},
        {"object": "background", "property": "color", "value": "#FFFFFF", "kind": "fill"},
        {"object": "background", "property": "transparency", "value": 0},
        {"object": "border", "property": "show", "value": True},
        {"object": "border", "property": "color", "value": "#E5E7EB", "kind": "fill"},
        {"object": "border", "property": "radius", "value": 8},
    ],
    "ibcs": [
        {"object": "dropShadow", "property": "show", "value": False},
        {"object": "background", "property": "show", "value": True},
        {"object": "background", "property": "color", "value": "#FFFFFF", "kind": "fill"},
        {"object": "border", "property": "show", "value": False},
        {"object": "border", "property": "radius", "value": 0},
    ],
}


# ---------- read PBIR ----------

def find_report_dir(root: Path) -> Path:
    if root.name.endswith(".Report") and (root / "definition").is_dir():
        return root
    hits = sorted(p for p in root.glob("*.Report") if (p / "definition").is_dir())
    if len(hits) == 1:
        return hits[0]
    if not hits:
        sys.exit(f"No *.Report/definition found under {root} — PBIP format required.")
    sys.exit("Multiple *.Report folders found — please specify one directly:\n  "
             + "\n  ".join(str(h) for h in hits))


def load_pages(report: Path) -> list[dict]:
    pages = []
    for page_json in sorted(report.glob("definition/pages/*/page.json")):
        try:
            meta = json.loads(page_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            sys.exit(f"Broken JSON in {page_json}: {e}")
        visuals = []
        for vj in sorted(page_json.parent.glob("visuals/*/visual.json")):
            try:
                visuals.append((vj, json.loads(vj.read_text(encoding="utf-8"))))
            except json.JSONDecodeError as e:
                sys.exit(f"Broken JSON in {vj}: {e}")
        pages.append({
            "folder": page_json.parent,
            "name": meta.get("name", page_json.parent.name),
            "displayName": meta.get("displayName", page_json.parent.name),
            "visuals": visuals,
        })
    if not pages:
        sys.exit(f"No pages found under {report}/definition/pages.")
    return pages


def visual_type(v: dict) -> str:
    if "visualGroup" in v:
        return "<group>"
    return (v.get("visual") or {}).get("visualType", "<unknown>")


def container_objects(v: dict, create: bool = False) -> dict | None:
    """`visual.visualContainerObjects` — the only place where
    container formatting takes effect (objects: no effect; root: error)."""
    vis = v.get("visual")
    if not isinstance(vis, dict):
        return None
    objs = vis.get("visualContainerObjects")
    if isinstance(objs, dict):
        return objs
    if create:
        vis["visualContainerObjects"] = {}
        return vis["visualContainerObjects"]
    return None


# ---------- literal encoding ----------

def learn_number_suffixes(pages) -> dict[str, str]:
    """Learn the suffix per property from existing visual.json files ('14D' → D)."""
    learned: dict[str, str] = {}
    rx = re.compile(r'"(\w+)"\s*:\s*\{\s*"expr"\s*:\s*\{\s*"Literal"\s*:\s*'
                    r'\{\s*"Value"\s*:\s*"(-?\d+(?:\.\d+)?)([DLM]?)"')
    for pg in pages:
        for path, _ in pg["visuals"]:
            for prop, _num, suf in rx.findall(path.read_text(encoding="utf-8")):
                learned.setdefault(prop, suf)
    return learned


def encode_literal(prop: str, value, suffixes: dict[str, str]) -> dict:
    if isinstance(value, bool):
        raw = "true" if value else "false"
    elif isinstance(value, (int, float)):
        suf = suffixes.get(prop, NUMBER_SUFFIX_DEFAULTS.get(prop, NUMBER_SUFFIX_FALLBACK))
        raw = f"{value:g}{suf}"
    else:
        raw = "'" + str(value).replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": raw}}}


def encode_value(rule: dict, suffixes: dict[str, str]) -> dict:
    lit = encode_literal(rule["property"], rule["value"], suffixes)
    if rule.get("kind") == "fill" or (rule["property"] in FILL_PROPERTIES
                                      and isinstance(rule["value"], str)):
        return {"solid": {"color": lit}}
    return lit


# ---------- restyle ----------

def apply_rules(v: dict, rules: list[dict], suffixes: dict[str, str]) -> list[str]:
    if "visual" not in v:  # groups have no container formatting
        return []
    objs = container_objects(v, create=bool(rules))
    if objs is None:
        return []
    changes = []
    for rule in rules:
        obj_name, prop = rule["object"], rule["property"]
        entries = objs.setdefault(obj_name, [])
        if not entries:
            entries.append({"properties": {}})
        props = entries[0].setdefault("properties", {})
        new = encode_value(rule, suffixes)
        if props.get(prop) != new:
            props[prop] = new
            changes.append(f"{obj_name}.{prop} = {rule['value']!r}")
    return changes


def strip_objects(v: dict, names: list[str]) -> list[str]:
    objs = container_objects(v)
    if not objs:
        return []
    changes = []
    for n in names:
        if n in objs:
            del objs[n]
            changes.append(f"{n}: override removed (theme takes effect again)")
    return changes


# ---------- linter ----------

LITERAL_NUM_RX = re.compile(r"^-?\d+(?:\.\d+)?")


def literal_value(node) -> str | None:
    try:
        return node["expr"]["Literal"]["Value"]
    except (KeyError, TypeError):
        return None


def literal_number(node) -> float | None:
    raw = literal_value(node)
    if raw is None:
        return None
    m = LITERAL_NUM_RX.match(raw)
    return float(m.group(0)) if m else None


def walk_properties(node):
    """All (property_name, value) pairs under every 'properties' block."""
    if isinstance(node, dict):
        for k, val in node.items():
            if k == "properties" and isinstance(val, dict):
                for pname, pval in val.items():
                    yield pname, pval
            yield from walk_properties(val)
    elif isinstance(node, list):
        for item in node:
            yield from walk_properties(item)


def lint_visual(v: dict, args, zones) -> list[str]:
    issues = []
    pos = v.get("position", {})
    if args.grid:
        off = [f"{k}={pos[k]:g}" for k in ("x", "y", "width", "height")
               if isinstance(pos.get(k), (int, float)) and round(pos[k]) % args.grid]
        if off:
            issues.append(f"not on the {args.grid}-px grid: {', '.join(off)}")
    if zones and "content" in zones:
        cx, cy, cw, ch = zones["content"]
        x, y = pos.get("x", 0), pos.get("y", 0)
        w, h = pos.get("width", 0), pos.get("height", 0)
        if x < cx or y < cy or x + w > cx + cw or y + h > cy + ch:
            issues.append(f"sticks out of the content zone {zones['content']} "
                          f"(x={x:g}, y={y:g}, w={w:g}, h={h:g})")
    if args.require_taborder and "visual" in v and "tabOrder" not in pos:
        issues.append("no tabOrder set (reading order/accessibility)")
    allowed_fonts = ({f.strip().lower() for f in args.fonts.split(",")}
                     if args.fonts else None)
    for pname, pval in walk_properties(v):
        if pname == "fontSize":
            n = literal_number(pval)
            if n is not None and n < args.min_font:
                issues.append(f"fontSize {n:g} pt < minimum {args.min_font:g} pt")
        elif allowed_fonts and pname == "fontFamily":
            raw = literal_value(pval)
            if raw is None:
                continue
            fam = raw.strip("'").split(",")[0].strip().strip("'")
            if fam.lower() not in allowed_fonts:
                issues.append(f"fontFamily '{fam}' not in the allowed list")
    objs = container_objects(v) or {}
    shadow = objs.get("dropShadow") or []
    if shadow:
        raw = literal_value((shadow[0].get("properties") or {}).get("show"))
        if raw != "false":  # dropShadow object without show=false ⇒ shadow active
            issues.append("dropShadow active (spec: no shadows)")
    return issues


# ---------- main ----------

def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("report", help="Path to the *.Report folder or PBIP project folder")
    p.add_argument("--preset", choices=sorted(PRESETS))
    p.add_argument("--rules", help="rules.json with additional/custom set rules")
    p.add_argument("--strip", help="Remove container objects, e.g. 'dropShadow,border'")
    p.add_argument("--check", action="store_true", help="Linter mode (never writes)")
    p.add_argument("--zones", help="zones.json for the content zone check")
    p.add_argument("--pages", help="only these pages (displayName, comma-separated)")
    p.add_argument("--skip-types", default="", help="skip visual types (e.g. 'slicer,image')")
    p.add_argument("--grid", type=int, default=8, help="grid for --check (0 = off)")
    p.add_argument("--min-font", type=float, default=9, help="minimum font size for --check")
    p.add_argument("--fonts", default="", help="allowed fontFamily list for --check")
    p.add_argument("--require-taborder", action="store_true",
                   help="--check: report visuals without tabOrder")
    p.add_argument("--apply", action="store_true", help="actually write the changes")
    args = p.parse_args()

    report = find_report_dir(Path(args.report).resolve())
    pages = load_pages(report)

    zones = None
    ignore_pages: set[str] = set()
    if args.zones:
        zones = json.loads(Path(args.zones).read_text(encoding="utf-8"))
        ignore_pages = set(zones.get("ignorePages", []))
    page_filter = ({s.strip() for s in args.pages.split(",")} if args.pages else None)
    skip_types = {s.strip().lower() for s in args.skip_types.split(",") if s.strip()}

    def selected(pg) -> bool:
        if page_filter and pg["displayName"] not in page_filter and pg["name"] not in page_filter:
            return False
        return pg["displayName"] not in ignore_pages

    # ---- linter ----
    if args.check:
        total = 0
        for pg in pages:
            if not selected(pg):
                continue
            for path, v in pg["visuals"]:
                if visual_type(v).lower() in skip_types:
                    continue
                for issue in lint_visual(v, args, zones):
                    total += 1
                    print(f"[{pg['displayName']}] {path.parent.name} "
                          f"({visual_type(v)}): {issue}")
        print(f"\n{total} violation(s)." if total else "All clean ✓")
        return 1 if total else 0

    # ---- restyle / strip ----
    rules: list[dict] = list(PRESETS.get(args.preset, []))
    if args.rules:
        rules += json.loads(Path(args.rules).read_text(encoding="utf-8")).get("set", [])
    strip_names = [s.strip() for s in args.strip.split(",")] if args.strip else []
    if not rules and not strip_names:
        p.error("Nothing to do: specify --preset, --rules, --strip, or --check.")

    suffixes = learn_number_suffixes(pages)
    planned: list[tuple[Path, dict, list[str]]] = []
    for pg in pages:
        if not selected(pg):
            continue
        for path, v in pg["visuals"]:
            if visual_type(v).lower() in skip_types:
                continue
            work = copy.deepcopy(v)
            changes = strip_objects(work, strip_names) if strip_names else []
            changes += apply_rules(work, rules, suffixes)
            if changes:
                planned.append((path, work, [f"[{pg['displayName']}] {c}" for c in changes]))

    if not planned:
        print("No changes needed — everything already matches the rules.")
        return 0

    for path, _, changes in planned:
        print(f"{path.relative_to(report)}:")
        for c in changes:
            print(f"  {c}")

    if not args.apply:
        print(f"\nDRY-RUN: {len(planned)} file(s) WOULD be changed. "
              "Write with --apply (close Desktop first, Git commit recommended).")
        return 0

    backup = report.parent / "design-out" / f"backup-{time.strftime('%Y%m%d-%H%M%S')}"
    for path, work, _ in planned:
        dest = backup / path.relative_to(report)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        path.write_text(json.dumps(work, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    print(f"\n{len(planned)} file(s) written. Backup: {backup}\n"
          "Now open it in Power BI Desktop and verify; if there are issues, "
          "copy the backup back.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
