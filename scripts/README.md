# Profile art generators

The profile README is three SVG panels, each of which animates itself. GitHub
strips `<script>` and inline CSS out of README markdown, but it renders SVGs
embedded through `<img>` with their SMIL animation intact — so all of the motion
is declared inside the SVG files rather than around them.

## Setup

```bash
pip install -r scripts/requirements.txt
```

## The three panels

| Script | Output | Notes |
| --- | --- | --- |
| `make_avatar_svg.py` | `assets/avatar-mosaic.svg` | Quantises `assets/avatar-src.png` into a mosaic; rows wipe in left to right. |
| `make_info_card.py` | `assets/info-card.svg` | Hand-authored neofetch-style panel; rows fade and slide in. Edit `ROWS` to change the content. |
| `fetch_contributions.py` | `data/contributions.json` | Scrapes the public contribution calendar. No token needed. |
| `render_heatmap_svg.py` | `assets/contrib-heatmap.svg` | Draws the calendar with a diagonal reveal, plus streak and volume stats. |

Rebuild everything:

```bash
python scripts/make_avatar_svg.py && python scripts/make_info_card.py && python scripts/fetch_contributions.py && python scripts/render_heatmap_svg.py
```

## Previewing

`STATIC=1` makes every script emit the finished frame with no animation, which
is what you want when you are checking layout rather than motion:

```bash
STATIC=1 python scripts/make_avatar_svg.py
```

`scripts/preview.html` puts the three panels together at their README sizes.
Open it in a browser to watch the animation, then regenerate without `STATIC=1`
before committing.

## Why the avatar is rects and not ASCII characters

Character art depends on the viewer's monospace font to hold its grid, and every
GitHub reader has a different one, so glyph advances drift and the picture
smears. Rects render identically everywhere. This avatar makes the problem worse
than usual: it is a thin, specular metal ring with almost no large flat tonal
regions, which is exactly the content an ASCII density ramp reproduces worst.

If you ever swap in a portrait photo — a face has the broad, smooth tonal areas
that character ramps handle well — real ASCII becomes viable, at which point the
ramp in `make_avatar_svg.py` can replace the shade table.

## Automation

`.github/workflows/update-profile-art.yml` re-scrapes the calendar and redraws
the heatmap every day at 06:17 UTC, committing with `[skip ci]` so the push does
not retrigger the workflow. The avatar and info card are static and are not
touched by the schedule.
