#!/usr/bin/env python3
"""Wireframe renderer for Power BI PBIR reports — visual feedback loop.

Draws an SVG wireframe per report page from the raw position data in
`*.Report/definition/pages/*/visuals/*/visual.json` — without Power BI
Desktop, without a screenshot, without a network. This lets an agent (or a
human) *see* what they built: grid alignment, overlaps, empty corners,
reading order.

The script is strictly read-only — it only writes to --out.

Usage:
  render_wireframe.py <report-path> [--out DIR] [--zones zones.json]
                      [--pages "Overview,Detail"] [--html]

  <report-path>  *.Report folder or PBIP project folder (like bulk_restyle.py)
  --out          target folder, default: <project>/design-out/wireframes/
  --zones        zones.json from the AGENT BRIEF (see below)
  --pages        only these pages (displayName or name, comma-separated)
  --html         additionally an index.html with all SVGs inline, stacked

zones.json format (identical to `bulk_restyle.py --check`):
  { "content": [16, 72, 1032, 616], "ignorePages": ["_Design-System"] }

  `content` is drawn as a semi-transparent overlay with a dashed border;
  any visual sticking out of the zone gets a red border. Pages from
  `ignorePages` are still rendered (you still want to see the component
  page), but without the zone overlay and without violations.

Color coding (legend is on the right of the SVG):
  Chrome        shape, basicShape, textbox, actionButton, image
  Slicer        slicer, advancedSlicerVisual
  Data visual   everything else (cards, charts, tables, custom visuals)
  Group         visualGroup — dashed border only, no fill

Grid: Power BI snaps to an 8 px grid, but drawing 8-px lines on a
1280-px page would be a gray carpet (160 lines) and would visually drown
out the visuals. So only the **major lines every 80 px** (= every 10th
grid line) are drawn — enough for orientation and eyeballing column
widths. The exact 8-px check is done by `bulk_restyle.py --check`.

PBIR facts this script relies on (verified):
  * `page.json`: `name`, `displayName`, `width`, `height` (fallback 1280x720).
  * `visual.json` root: `position` with `x`, `y`, `z`, `width`, `height`,
    optional `tabOrder`; visual type under `visual.visualType`.
  * Groups carry a `visualGroup` block instead of `visual`.
  * `z` is the layer: small = back. Drawing accordingly goes from back to
    front, so the SVG stacking matches the Desktop view.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ---------- rendering constants ----------

PAGE_FALLBACK = (1280.0, 720.0)
GRID_MAJOR = 80          # drawn major lines (every 10th 8-px grid line)
GRID_BASE = 8            # Power BI base grid (documented only, not drawn)

MARGIN = 24              # margin around the canvas
HEADER_H = 44            # header row with page name
FOOTER_H = 26            # footer row with notes
LEGEND_W = 208           # legend column on the right

CHROME_TYPES = {"shape", "basicshape", "textbox", "actionbutton", "image"}
SLICER_TYPES = {"slicer", "advancedslicervisual"}

CATEGORIES = {
    # key: internal category → (label, fill, border)
    "chrome": ("Chrome", "#EFEEE8", "#B3AFA4"),
    "slicer": ("Slicer", "#E9EFF6", "#7C9DBD"),
    "data": ("Data visual", "#E6EDE9", "#6E9184"),
    "group": ("Group", "none", "#9A958A"),
}
VIOLATION_STROKE = "#C2412D"   # red border: sticks out of the content zone
ZONE_STROKE = "#C25A2D"        # accent color of the design system
INK = "#0F1E2E"
INK_SOFT = "#475569"
CANVAS_BG = "#FFFFFF"
SHEET_BG = "#FAFAF7"
GRID_COLOR = "#DDDBD3"


# ---------- read PBIR (identical to bulk_restyle.py) ----------

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
            "width": _num(meta.get("width"), PAGE_FALLBACK[0]),
            "height": _num(meta.get("height"), PAGE_FALLBACK[1]),
            "visuals": visuals,
        })
    if not pages:
        sys.exit(f"No pages found under {report}/definition/pages.")
    return pages


def visual_type(v: dict) -> str:
    if "visualGroup" in v:
        return "<group>"
    return (v.get("visual") or {}).get("visualType", "<unknown>")


def category(v: dict) -> str:
    if "visualGroup" in v:
        return "group"
    t = visual_type(v).lower()
    if t in CHROME_TYPES:
        return "chrome"
    if t in SLICER_TYPES:
        return "slicer"
    return "data"


def _num(value, default: float) -> float:
    return float(value) if isinstance(value, (int, float)) else default


# ---------- helpers ----------

def esc(text: str) -> str:
    """XML escaping for labels (titles come unfiltered from the report)."""
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;"))


def slugify(text: str) -> str:
    """Filename from displayName — keep umlauts, strip everything risky."""
    s = re.sub(r"[^\w.\- ]+", "", str(text), flags=re.UNICODE).strip()
    s = re.sub(r"[\s_]+", "-", s).strip("-.")
    return s or "page"


def fit(text: str, box_w: float, font_size: float, pad: float = 8.0) -> str:
    """Truncate label to the tile width (rough width estimate)."""
    usable = box_w - 2 * pad
    if usable <= 6:
        return ""
    max_chars = int(usable / (font_size * 0.55))
    if max_chars <= 1:
        return ""
    if len(text) <= max_chars:
        return text
    return text[: max(1, max_chars - 1)] + "…"


def fmt(value: float) -> str:
    return f"{value:g}"


def violates(pos: dict, zone: list) -> bool:
    cx, cy, cw, ch = (float(v) for v in zone)
    x, y = _num(pos.get("x"), 0.0), _num(pos.get("y"), 0.0)
    w, h = _num(pos.get("width"), 0.0), _num(pos.get("height"), 0.0)
    return x < cx or y < cy or x + w > cx + cw or y + h > cy + ch


# ---------- build SVG ----------

def build_svg(page: dict, zone: list | None) -> tuple[str, int]:
    """A complete <svg> element for one page. Returns (SVG, violations)."""
    pw, ph = page["width"], page["height"]
    ox, oy = MARGIN, MARGIN + HEADER_H          # origin of the report canvas
    total_w = MARGIN * 2 + pw + LEGEND_W
    total_h = MARGIN * 2 + HEADER_H + ph + FOOTER_H

    out: list[str] = []
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{fmt(total_w)}" '
        f'height="{fmt(total_h)}" viewBox="0 0 {fmt(total_w)} {fmt(total_h)}" '
        f'font-family="Segoe UI, Helvetica, Arial, sans-serif">'
    )
    out.append(f'<rect width="{fmt(total_w)}" height="{fmt(total_h)}" fill="{CANVAS_BG}"/>')

    # header row
    out.append(f'<text x="{fmt(MARGIN)}" y="{fmt(MARGIN + 18)}" font-size="17" '
               f'font-weight="600" fill="{INK}">{esc(page["displayName"])}</text>')
    out.append(f'<text x="{fmt(MARGIN)}" y="{fmt(MARGIN + 34)}" font-size="11" '
               f'fill="{INK_SOFT}">{esc(page["name"])} · {fmt(pw)}×{fmt(ph)} px · '
               f'{len(page["visuals"])} visual(s)</text>')

    # report canvas
    out.append(f'<rect x="{fmt(ox)}" y="{fmt(oy)}" width="{fmt(pw)}" height="{fmt(ph)}" '
               f'fill="{SHEET_BG}" stroke="{INK_SOFT}" stroke-width="1"/>')

    # grid lines (only major lines every GRID_MAJOR px — 8 px would be a carpet)
    lines = []
    gx = GRID_MAJOR
    while gx < pw:
        lines.append(f'M{fmt(ox + gx)} {fmt(oy)}V{fmt(oy + ph)}')
        gx += GRID_MAJOR
    gy = GRID_MAJOR
    while gy < ph:
        lines.append(f'M{fmt(ox)} {fmt(oy + gy)}H{fmt(ox + pw)}')
        gy += GRID_MAJOR
    if lines:
        out.append(f'<path d="{"".join(lines)}" stroke="{GRID_COLOR}" '
                   f'stroke-width="1" fill="none"/>')

    # content zone
    if zone:
        zx, zy, zw, zh = (float(v) for v in zone)
        out.append(f'<rect x="{fmt(ox + zx)}" y="{fmt(oy + zy)}" width="{fmt(zw)}" '
                   f'height="{fmt(zh)}" fill="{ZONE_STROKE}" fill-opacity="0.06" '
                   f'stroke="{ZONE_STROKE}" stroke-width="1.5" stroke-dasharray="8 5"/>')
        out.append(f'<text x="{fmt(ox + zx + 5)}" y="{fmt(oy + zy + 13)}" font-size="10" '
                   f'fill="{ZONE_STROKE}">Content zone {fmt(zx)},{fmt(zy)} '
                   f'{fmt(zw)}×{fmt(zh)}</text>')

    # visuals: draw from back (small z) to front
    ordered = sorted(
        page["visuals"],
        key=lambda item: (_num((item[1].get("position") or {}).get("z"), 0.0),
                          item[0].parent.name),
    )

    violations = 0
    counts = {key: 0 for key in CATEGORIES}
    for path, v in ordered:
        pos = v.get("position") or {}
        x = ox + _num(pos.get("x"), 0.0)
        y = oy + _num(pos.get("y"), 0.0)
        w = max(_num(pos.get("width"), 0.0), 2.0)
        h = max(_num(pos.get("height"), 0.0), 2.0)
        cat = category(v)
        counts[cat] += 1
        _, fill, stroke = CATEGORIES[cat]
        bad = bool(zone) and violates(pos, zone)
        if bad:
            violations += 1
        dash = ' stroke-dasharray="7 4"' if cat == "group" else ""
        out.append(
            f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" '
            f'fill="{fill}" stroke="{VIOLATION_STROKE if bad else stroke}" '
            f'stroke-width="{2 if bad else 1}"{dash}/>'
        )

        # label: visualType + folder name, truncated when space is tight
        label = f"{visual_type(v)} · {path.parent.name}"
        text = fit(label, w, 11)
        if text and h >= 18:
            out.append(f'<text x="{fmt(x + 8)}" y="{fmt(y + 16)}" font-size="11" '
                       f'fill="{INK}">{esc(text)}</text>')
        size = fit(f"{fmt(_num(pos.get('width'), 0.0))}×{fmt(_num(pos.get('height'), 0.0))}",
                   w, 9)
        if size and h >= 32:
            out.append(f'<text x="{fmt(x + 8)}" y="{fmt(y + 28)}" font-size="9" '
                       f'fill="{INK_SOFT}">{esc(size)}</text>')

        # tabOrder as a number badge in the top-right corner
        tab = pos.get("tabOrder")
        if isinstance(tab, (int, float)) and w >= 30 and h >= 22:
            bx, by = x + w - 22, y + 4
            out.append(f'<rect x="{fmt(bx)}" y="{fmt(by)}" width="18" height="14" rx="3" '
                       f'fill="{INK}" fill-opacity="0.75"/>')
            out.append(f'<text x="{fmt(bx + 9)}" y="{fmt(by + 10.5)}" font-size="9" '
                       f'text-anchor="middle" fill="#FFFFFF">{esc(fmt(float(tab)))}</text>')

    # legend
    lx = ox + pw + 16
    ly = oy + 4
    out.append(f'<text x="{fmt(lx)}" y="{fmt(ly + 10)}" font-size="11" '
               f'font-weight="600" fill="{INK}">Legend</text>')
    ly += 24
    for key, (label, fill, stroke) in CATEGORIES.items():
        dash = ' stroke-dasharray="5 3"' if key == "group" else ""
        out.append(f'<rect x="{fmt(lx)}" y="{fmt(ly - 9)}" width="16" height="12" '
                   f'fill="{fill}" stroke="{stroke}"{dash}/>')
        out.append(f'<text x="{fmt(lx + 24)}" y="{fmt(ly)}" font-size="10" '
                   f'fill="{INK_SOFT}">{esc(label)} ({counts[key]})</text>')
        ly += 20
    if zone:
        ly += 4
        out.append(f'<rect x="{fmt(lx)}" y="{fmt(ly - 9)}" width="16" height="12" '
                   f'fill="{ZONE_STROKE}" fill-opacity="0.06" stroke="{ZONE_STROKE}" '
                   f'stroke-dasharray="5 3"/>')
        out.append(f'<text x="{fmt(lx + 24)}" y="{fmt(ly)}" font-size="10" '
                   f'fill="{INK_SOFT}">Content zone</text>')
        ly += 20
        out.append(f'<rect x="{fmt(lx)}" y="{fmt(ly - 9)}" width="16" height="12" '
                   f'fill="none" stroke="{VIOLATION_STROKE}" stroke-width="2"/>')
        out.append(f'<text x="{fmt(lx + 24)}" y="{fmt(ly)}" font-size="10" '
                   f'fill="{INK_SOFT}">outside ({violations})</text>')
        ly += 20
    ly += 4
    out.append(f'<rect x="{fmt(lx)}" y="{fmt(ly - 9)}" width="16" height="12" rx="3" '
               f'fill="{INK}" fill-opacity="0.75"/>')
    out.append(f'<text x="{fmt(lx + 24)}" y="{fmt(ly)}" font-size="10" '
               f'fill="{INK_SOFT}">tabOrder</text>')

    # footer
    out.append(f'<text x="{fmt(MARGIN)}" y="{fmt(total_h - MARGIN + 6)}" font-size="10" '
               f'fill="{INK_SOFT}">Grid lines every {GRID_MAJOR} px '
               f'(Power BI base grid {GRID_BASE} px — exact check: '
               f'bulk_restyle.py --check) · draw order by z (back → front)'
               f'</text>')
    out.append("</svg>")
    return "\n".join(out), violations


def build_html(entries: list[tuple[str, str]]) -> str:
    """index.html with all SVGs inline — self-contained, no external CSS/JS."""
    parts = [
        "<!doctype html>",
        '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>PBIR-Wireframes</title>",
        "<style>",
        "body{margin:0;padding:24px;background:#FAFAF7;color:#0F1E2E;",
        "font-family:Segoe UI,Helvetica,Arial,sans-serif}",
        "h1{font-size:20px;margin:0 0 4px}",
        "p.meta{margin:0 0 24px;color:#475569;font-size:13px}",
        "section{margin:0 0 32px}",
        "h2{font-size:15px;margin:0 0 8px;font-weight:600}",
        "figure{margin:0;overflow-x:auto;background:#FFF;border:1px solid #E5E7EB;",
        "border-radius:8px;padding:8px}",
        "svg{display:block;max-width:100%;height:auto}",
        "</style></head><body>",
        "<h1>PBIR-Wireframes</h1>",
        f'<p class="meta">{len(entries)} page(s) · rendered from the '
        "position data in visual.json — not a live view from Power BI.</p>",
    ]
    for title, svg in entries:
        parts.append("<section>")
        parts.append(f"<h2>{esc(title)}</h2>")
        parts.append(f"<figure>{svg}</figure>")
        parts.append("</section>")
    parts.append("</body></html>")
    return "\n".join(parts)


# ---------- main ----------

def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("report", help="Path to the *.Report folder or PBIP project folder")
    p.add_argument("--out", help="Target folder (default: <project>/design-out/wireframes)")
    p.add_argument("--zones", help="zones.json with content zone and ignorePages")
    p.add_argument("--pages", help="only these pages (displayName/name, comma-separated)")
    p.add_argument("--html", action="store_true",
                   help="additionally an index.html with all SVGs inline")
    args = p.parse_args()

    report = find_report_dir(Path(args.report).resolve())
    pages = load_pages(report)

    zone = None
    ignore_pages: set[str] = set()
    if args.zones:
        zones_path = Path(args.zones)
        if not zones_path.is_file():
            sys.exit(f"zones.json not found: {zones_path}")
        try:
            cfg = json.loads(zones_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            sys.exit(f"Broken JSON in {zones_path}: {e}")
        zone = cfg.get("content")
        if zone is not None and (not isinstance(zone, list) or len(zone) != 4):
            sys.exit('zones.json: "content" must be [x, y, w, h].')
        ignore_pages = set(cfg.get("ignorePages", []))

    page_filter = ({s.strip() for s in args.pages.split(",") if s.strip()}
                   if args.pages else None)

    out_dir = Path(args.out) if args.out else report.parent / "design-out" / "wireframes"
    out_dir.mkdir(parents=True, exist_ok=True)

    selected = [pg for pg in pages if not page_filter
                or pg["displayName"] in page_filter or pg["name"] in page_filter]
    if not selected:
        sys.exit(f"No page matches --pages {args.pages!r}. Available: "
                 + ", ".join(pg["displayName"] for pg in pages))

    entries: list[tuple[str, str]] = []
    used: set[str] = set()
    total_violations = 0
    for pg in selected:
        # ignorePages: render yes, zone overlay/violations no
        page_zone = None if pg["displayName"] in ignore_pages else zone
        svg, violations = build_svg(pg, page_zone)
        total_violations += violations

        stem = slugify(pg["displayName"])
        candidate, n = stem, 2
        while candidate in used:                    # disambiguate identical displayNames
            candidate, n = f"{stem}-{n}", n + 1
        used.add(candidate)

        target = out_dir / f"{candidate}.svg"
        target.write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + svg + "\n",
                          encoding="utf-8")
        note = "" if page_zone else (" (ignorePages: no zone check)"
                                     if pg["displayName"] in ignore_pages else "")
        flag = f" · {violations} outside the zone" if violations else ""
        print(f"{target}  ← {pg['displayName']} "
              f"({len(pg['visuals'])} visual(s){flag}){note}")
        entries.append((pg["displayName"], svg))

    if args.html:
        index = out_dir / "index.html"
        index.write_text(build_html(entries) + "\n", encoding="utf-8")
        print(f"{index}  ← overview with {len(entries)} page(s)")

    print(f"\n{len(entries)} wireframe(s) in {out_dir}")
    if zone:
        print(f"{total_violations} visual(s) stick out of the content zone "
              f"(outlined in red)." if total_violations
              else "All visuals within the content zone ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
