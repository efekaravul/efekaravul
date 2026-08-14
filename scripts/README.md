# Profile art generators

The profile README is four SVG panels, each of which animates itself. GitHub
strips `<script>` and inline CSS out of README markdown, but it serves SVGs
embedded through `<img>` as `image/svg+xml` with their SMIL animation intact —
so all of the motion is declared inside the SVG files rather than around them.

## Setup

```bash
pip install -r scripts/requirements.txt
```

## Layout

| Script | Output | Notes |
| --- | --- | --- |
| `build_panels.py` | `assets/whoami.svg` | Avatar mosaic beside a neofetch-style identity card. |
| `build_panels.py` | `assets/portfolio.svg` | Featured notebooks with their metrics. Edit `PROJECTS`. |
| `build_panels.py` | `assets/focus.svg` | What the practice consists of. Edit `FOCUS` and `NOW`. |
| `fetch_contributions.py` | `data/contributions.json` | Scrapes the public contribution calendar. No token needed. |
| `render_heatmap_svg.py` | `assets/contrib-heatmap.svg` | Draws the calendar with a diagonal reveal, plus streak and volume stats. |

`panels.py` holds the shared window chrome, palette and animation helpers;
`avatar.py` turns `assets/avatar-src.png` into the mosaic.

Rebuild everything:

```bash
python scripts/build_panels.py && python scripts/fetch_contributions.py && python scripts/render_heatmap_svg.py
```

## Two constraints worth not rediscovering

**Every panel is one whole image at 860px.** GitHub's profile README column is
narrower than 860px on most screens. A single image scales down as a unit, but
two images placed side by side simply wrap onto separate lines once they stop
fitting — which is what happens if a panel is split in two.

**Animations loop rather than freezing.** An SVG's clock starts when the image
loads, so a play-once-and-freeze reveal is over before a reader has scrolled to
it and reads as a static picture. Each animation instead holds hidden until its
turn, reveals, then holds the finished frame for the rest of a 6-second cycle
(`panels.CYCLE`) before repeating.

## Previewing

`STATIC=1` makes every script emit the finished frame with no animation, which
is what you want when checking layout rather than motion:

```bash
STATIC=1 python scripts/build_panels.py
```

`scripts/preview.html` stacks the panels inside a column the width of GitHub's,
so wrapping problems show up locally. Open it in a browser to watch the
animation, then regenerate without `STATIC=1` before committing.

## Why the avatar is rects and not ASCII characters

Character art depends on the reader's monospace font to hold its grid, and every
GitHub reader has a different one, so glyph advances drift and the picture
smears. Rects render identically everywhere. This avatar makes the problem worse
than usual: it is a thin, specular metal ring with almost no broad flat tonal
regions, which is exactly the content an ASCII density ramp reproduces worst.

If you ever swap in a portrait photo — a face has the broad, smooth tonal areas
that character ramps handle well — real ASCII becomes viable, at which point the
shade table in `avatar.py` can be replaced with a density ramp.

## Automation

`.github/workflows/update-profile-art.yml` re-scrapes the calendar and redraws
the heatmap every day at 06:17 UTC, committing with `[skip ci]` so the push does
not retrigger the workflow. The other three panels are static and are not
touched by the schedule.
