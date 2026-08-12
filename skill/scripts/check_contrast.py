#!/usr/bin/env python3
"""WCAG contrast check for the Power BI Design Framework.

Modes:
  Single pair:  check_contrast.py "#1F2937" --bg "#FAFAFB"
  Palette:      check_contrast.py --palette palette.json
                  { "ink": "#1F2937", "bg": "#FAFAFB", ...,
                    "pairs": [["ink","bg"], ...] }
                  Without "pairs", all roles are checked against "bg" and
                  "bg-card" (if present).
  Gray ladder:  check_contrast.py --ladder "#1F2937" --bg "#FAFAFB"

Evaluated against WCAG AA: 4.5:1 (normal text), 3:1 (large text >= 18pt / UI).
On FAIL, the closest matching variant (darkened or lightened) is
automatically suggested. No dependencies.
"""
import argparse
import json
import sys

AA_NORMAL = 4.5
AA_LARGE = 3.0


def parse_hex(c: str) -> tuple[float, float, float]:
    c = c.strip().lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    if len(c) != 6:
        raise ValueError(f"Invalid hex color: #{c}")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore


def to_hex(rgb) -> str:
    return "#{:02X}{:02X}{:02X}".format(*(max(0, min(255, round(v))) for v in rgb))


def rel_luminance(rgb) -> float:
    def channel(v: float) -> float:
        v /= 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b) -> float:
    la, lb = rel_luminance(a), rel_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def scale(rgb, factor: float, toward_white: bool):
    """factor 0..1: 0 = original color, 1 = black or white."""
    if toward_white:
        return tuple(v + (255 - v) * factor for v in rgb)
    return tuple(v * (1 - factor) for v in rgb)


def suggest_fix(fg, bg, target: float):
    """Closest variant of fg that reaches the target against bg."""
    darker_bg = rel_luminance(bg) >= rel_luminance(fg)
    # fg must move away from bg: darker on a light bg, lighter on a dark bg.
    toward_white = not darker_bg
    lo, hi = 0.0, 1.0
    if contrast(scale(fg, 1.0, toward_white), bg) < target:
        return None  # even black/white isn't enough (bg too mid-tone)
    for _ in range(40):  # bisection on the smallest sufficient factor
        mid = (lo + hi) / 2
        if contrast(scale(fg, mid, toward_white), bg) >= target:
            hi = mid
        else:
            lo = mid
    return to_hex(scale(fg, hi, toward_white))


def report_pair(name: str, fg_hex: str, bg_hex: str) -> bool:
    fg, bg = parse_hex(fg_hex), parse_hex(bg_hex)
    ratio = contrast(fg, bg)
    ok_normal = ratio >= AA_NORMAL
    ok_large = ratio >= AA_LARGE
    verdict = "PASS AA" if ok_normal else ("PASS large/UI only (>=3:1)" if ok_large else "FAIL")
    line = f"  {name:<24} {fg_hex.upper():>8} on {bg_hex.upper():<8} → {ratio:4.2f}:1   {verdict}"
    print(line)
    if not ok_normal:
        fix = suggest_fix(fg, bg, AA_NORMAL)
        if fix:
            print(f"  {'':<24} Suggestion for normal text: {fix} "
                  f"({contrast(parse_hex(fix), bg):.2f}:1)")
        else:
            print(f"  {'':<24} No fix possible — background too mid-tone, change BG.")
    return ok_normal


def ladder(ink_hex: str, bg_hex: str, steps: int = 5):
    ink, bg = parse_hex(ink_hex), parse_hex(bg_hex)
    print(f"Gray ladder from {ink_hex.upper()} toward {bg_hex.upper()}:")
    for i in range(steps):
        f = i / (steps - 1) * 0.85  # keep the last step from fully disappearing into the BG
        c = tuple(ink[k] + (bg[k] - ink[k]) * f for k in range(3))
        hx = to_hex(c)
        ratio = contrast(parse_hex(hx), bg)
        use = ("Text" if ratio >= AA_NORMAL
               else "large titles/UI" if ratio >= AA_LARGE
               else "areas/lines only (no text)")
        print(f"  Step {i + 1}: {hx}  ({ratio:4.2f}:1 on BG — {use})")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("fg", nargs="?", help="Foreground hex color, e.g. '#1F2937'")
    p.add_argument("--bg", default="#FFFFFF", help="Background (default: #FFFFFF)")
    p.add_argument("--palette", help="Path to palette.json")
    p.add_argument("--ladder", metavar="INK", help="Generate gray ladder from this color")
    args = p.parse_args()

    if args.ladder:
        ladder(args.ladder, args.bg)
        return 0

    if args.palette:
        with open(args.palette, encoding="utf-8") as f:
            pal = json.load(f)
        roles = {k: v for k, v in pal.items() if k != "pairs" and isinstance(v, str)}
        pairs = pal.get("pairs")
        if not pairs:
            bgs = [b for b in ("bg", "bg-card") if b in roles]
            pairs = [[r, b] for r in roles for b in bgs
                     if r not in ("bg", "bg-card") and r != b]
        print(f"Contrast report ({args.palette}):")
        all_ok = True
        for fg_role, bg_role in pairs:
            ok = report_pair(f"{fg_role} / {bg_role}", roles[fg_role], roles[bg_role])
            all_ok = all_ok and ok
        print("\nOverall:", "all pairs AA-compliant ✓" if all_ok
              else "at least one pair below 4.5:1 — apply the suggestions above.")
        return 0 if all_ok else 1

    if not args.fg:
        p.error("Provide either FG color, --palette, or --ladder.")
    ok = report_pair("fg / bg", args.fg, args.bg)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
