# Branding Extraction — Deriving Colors & Fonts from a Source

Goal: derive a solid palette from what the user already has (a deck, a
website, a logo) — instead of asking them for hex values. That's the
"native entry point": providing a source is enough.

The result of the extraction is always the same set of **color roles**:

| Role          | Purpose                                 | Origin                            |
| ------------- | ---------------------------------------- | ---------------------------------- |
| `ink`         | text, titles                            | darkest brand/text color           |
| `accent`      | interaction, active nav, emphasis       | primary/brand color                |
| `bg`          | page background (lightly tinted)        | derived: near-white with a tint toward ink/accent |
| `bg-card`     | tile background                         | usually pure white                 |
| `gray-ladder` | secondary text, lines, panel surfaces   | stepped from `ink` (not plain gray) |
| `dataColors`  | series colors (6–8)                     | accent-compatible, colorblind-safe |

## Source: company presentation (`.pptx`)

The Office theme is embedded as XML in the package — no need to guess from
a screenshot:

```bash
unzip -p praesi.pptx ppt/theme/theme1.xml | grep -o 'srgbClr val="[0-9A-Fa-f]\{6\}"' | sort | uniq -c | sort -rn
```

Interpreting the theme slots in `theme1.xml` (`<a:clrScheme>`):
`dk1`/`dk2` → ink candidates, `accent1` → accent candidate, `accent2–6` →
data-color candidates, `lt1`/`lt2` → backgrounds. It's also worth checking
the slide master (logo is often embedded there:
`unzip -l praesi.pptx | grep media`). For `.pdf` presentations: render pages
as images and extract dominant colors the same way as for a logo (below).

## Source: website (URL)

1. Fetch HTML + CSS (WebFetch or `curl`), search for color definitions: CSS
   variables (`--primary`, `--brand`, the `:root` block), the
   `theme-color` meta tag, most frequent hex values in stylesheets.
2. Count frequency; nav/button colors are usually the brand color.
3. Extract the logo URL from the `<img>`/SVG in the header — an SVG contains
   hex values directly in its markup.
4. Ambiguities (e.g., three blue candidates) → present as an open decision
   with the hex values and where they were found ("nav background vs.
   button vs. link").

## Source: logo file (image)

Dominant colors via pixel statistics (Python + Pillow, inline if needed):

```python
from PIL import Image
from collections import Counter
img = Image.open("logo.png").convert("RGBA").resize((64, 64))
px = [p[:3] for p in img.getdata() if p[3] > 128]          # drop transparent
common = Counter(px).most_common(12)                        # then filter near-white/near-black
```

Treat clusters near white (#F0+) and near black as BG/ink hints; the
strongest remaining color is the accent candidate.

## No source → neutral modern palette

Offer a default (works, AA-checked, understated):
`ink #1F2937` · `accent #2563EB` · `bg #FAFAFB` · `bg-card #FFFFFF` ·
secondary gray `#6B7280`. The user can swap any role later — the role
structure stays.

## Derivation rules (source → roles)

1. **Accent:** the one brand color. If the brand has several: the one with
   the strongest interaction association (button/link color on the
   website).
2. **Ink:** the darkest text color in the source; if only "black" exists,
   tint it slightly toward the accent (e.g., a very dark blue instead of
   #000) — reads more modern and stays AA-compliant.
3. **Gray ladder:** lighten `ink` in 4–5 steps toward `bg`
   (`check_contrast.py --ladder` generates them). Plain grays next to a
   tinted ink look muddy.
4. **bg:** near-white with a minimal tint of the brand (1–3% saturation).
5. **dataColors:** use the accent as the first series only if it stays away
   from red/green semantics; otherwise a coordinated, distinguishable
   palette. For IBCS reports, use the IBCS semantics instead (see
   design-rules.md §6).

## Required: contrast validation

Every derived combination goes through the script:

```bash
python scripts/check_contrast.py "#1F2937" --bg "#FAFAFB"        # single pair
python scripts/check_contrast.py --palette design-out/palette.json  # all role pairs
python scripts/check_contrast.py --ladder "#1F2937" --bg "#FAFAFB"  # generate gray ladder
```

The script reports PASS/FAIL against AA (4.5:1 text, 3:1 large/UI) and, on
FAIL, automatically suggests the nearest viable variant (darkened/
lightened). **Corporate color fails AA?** → use the adjusted variant,
reserve the original for large areas/logos, and document the deviation in
the DESIGN-SPEC ("brand blue #4F8FE0 → text variant #2B6CB8, 4.6:1").

`palette.json` format for palette mode:

```json
{ "ink": "#1F2937", "accent": "#2563EB", "bg": "#FAFAFB", "bg-card": "#FFFFFF",
  "pairs": [["ink","bg"], ["ink","bg-card"], ["accent","bg"]] }
```
