"""Turn the avatar into a self-animating terminal-style mosaic SVG.

GitHub strips <script> and inline CSS from README markdown but renders SVGs
embedded through <img> with their SMIL animation intact, so the whole reveal
has to live inside the SVG: one <clipPath> per row with an animated rect that
wipes left to right, staggered by row and frozen at the end.

The cells are <rect> elements rather than ASCII characters on purpose. Character
art depends on the viewer's monospace font for its grid, and every GitHub reader
has a different one, so glyph advances drift and the picture smears. Rects are
identical everywhere. This avatar in particular - a thin, specular metal ring -
carries almost no large flat tonal regions, which is exactly the content ASCII
ramps reproduce worst.

Usage:
    python scripts/make_avatar_svg.py [--cols 84] [--out assets/avatar-mosaic.svg]
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "avatar-src.png"
OUT = ROOT / "assets" / "avatar-mosaic.svg"

COLS = 84
PANEL_W = 369.6      # drawing width in user units; the README shows it at 370px
PAD_X = 16.0
TITLEBAR_H = 36.0
PAD_BOTTOM = 16.0

# Contrast window. The floor sits above 0 so sensor noise in the black backdrop
# stays empty, and the ceiling well below 255 so the specular highlights do not
# swallow the whole top of the ramp.
LEVEL_LO = 10.0
LEVEL_HI = 155.0
GAMMA = 0.78

# Index 0 is never drawn, so the panel background shows through as empty space.
SHADES = ["#0d1117", "#2d3540", "#586675", "#8b98a6", "#c2ccd6", "#eef3f8"]

BG = "#0d1117"
BORDER = "#30363d"
INK = "#c9d1d9"
PROMPT_USER = "#7ee787"
PROMPT_PATH = "#79c0ff"

ROW_DELAY = 0.028    # seconds between consecutive rows starting to draw
ROW_DUR = 0.40       # seconds for one row to wipe in


def autocrop(img: Image.Image, threshold: int = 12, margin: int = 4) -> Image.Image:
    """Trim the dead black border so the subject fills the mosaic."""
    a = np.asarray(img, dtype=np.uint8)
    ys, xs = np.where(a > threshold)
    if ys.size == 0:
        return img
    top, bottom = max(0, ys.min() - margin), min(a.shape[0], ys.max() + 1 + margin)
    left, right = max(0, xs.min() - margin), min(a.shape[1], xs.max() + 1 + margin)
    return img.crop((left, top, right, bottom))


def quantise(path: Path, cols: int) -> np.ndarray:
    """Downsample to a square-celled grid of shade indices."""
    img = autocrop(Image.open(path).convert("L"))
    w, h = img.size
    rows = max(1, round(cols * h / w))
    a = np.asarray(img.resize((cols, rows), Image.LANCZOS), dtype=np.float32)
    a = np.clip((a - LEVEL_LO) / (LEVEL_HI - LEVEL_LO), 0.0, 1.0) ** GAMMA
    return np.clip((a * (len(SHADES) - 1)).round().astype(int), 0, len(SHADES) - 1)


def runs(row: np.ndarray) -> list[tuple[int, int, int]]:
    """Collapse a row into (start, length, level) runs so one rect covers many cells.

    A per-cell rect would put roughly 4,000 elements in the file; merging equal
    neighbours cuts that by several times without changing a pixel.
    """
    out: list[tuple[int, int, int]] = []
    start = 0
    for i in range(1, len(row) + 1):
        if i == len(row) or row[i] != row[start]:
            if row[start] != 0:
                out.append((start, i - start, int(row[start])))
            start = i
    return out


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def titlebar(width: float, command: str) -> str:
    """Shared window chrome so all three panels read as one set."""
    dots = "".join(
        f'<circle cx="{x}" cy="18" r="4.5" fill="{c}"/>'
        for x, c in ((20, "#ff5f56"), (36, "#ffbd2e"), (52, "#27c93f"))
    )
    return (
        f"<g>{dots}"
        f'<line x1="0" y1="36" x2="{width:.0f}" y2="36" stroke="{BORDER}"/>'
        f'<text class="mono" x="70" y="22" font-size="11" fill="{PROMPT_USER}">efe@github'
        f'<tspan fill="{INK}">:</tspan><tspan fill="{PROMPT_PATH}">~</tspan>'
        f'<tspan fill="{INK}">$ {esc(command)}</tspan></text></g>'
    )


def build_svg(grid: np.ndarray, static: bool = False) -> str:
    rows, cols = grid.shape
    cell = PANEL_W / cols
    width = PANEL_W + 2 * PAD_X
    height = TITLEBAR_H + rows * cell + PAD_BOTTOM

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" '
        f'width="{width:.0f}" height="{height:.0f}" role="img" '
        f'aria-label="Mosaic rendering of Efe Karavul\'s avatar">'
    )
    parts.append(
        "<style>"
        ".mono{font-family:ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,"
        "'DejaVu Sans Mono',monospace}"
        "</style>"
    )

    # One clip rect per row, each wiping from zero width to full and freezing.
    parts.append("<defs>")
    for r in range(rows):
        y = TITLEBAR_H + r * cell
        if static:
            body = f'<rect x="{PAD_X:.1f}" y="{y:.1f}" width="{PANEL_W:.1f}" height="{cell:.1f}"/>'
        else:
            body = (
                f'<rect x="{PAD_X:.1f}" y="{y:.1f}" width="0" height="{cell:.1f}">'
                f'<animate attributeName="width" from="0" to="{PANEL_W:.1f}" '
                f'begin="{r * ROW_DELAY:.2f}s" dur="{ROW_DUR}s" fill="freeze"/></rect>'
            )
        parts.append(f'<clipPath id="r{r}">{body}</clipPath>')
    parts.append("</defs>")

    parts.append(
        f'<rect x="0.5" y="0.5" width="{width - 1:.0f}" height="{height - 1:.0f}" '
        f'rx="10" fill="{BG}" stroke="{BORDER}"/>'
    )
    parts.append(titlebar(width, "./avatar.sh --render"))

    for r in range(rows):
        segments = runs(grid[r])
        if not segments:
            continue
        y = TITLEBAR_H + r * cell
        # Group the row's runs by shade so `fill` is written once per level
        # instead of once per rect - worth about 20% of the file.
        by_level: dict[int, list[tuple[int, int]]] = {}
        for start, length, level in segments:
            by_level.setdefault(level, []).append((start, length))

        groups = "".join(
            f'<g fill="{SHADES[level]}">'
            + "".join(
                f'<rect x="{PAD_X + start * cell:.1f}" y="{y:.1f}" '
                f'width="{length * cell:.1f}" height="{cell:.1f}"/>'
                for start, length in spans
            )
            + "</g>"
            for level, spans in sorted(by_level.items())
        )
        parts.append(f'<g clip-path="url(#r{r})">{groups}</g>')

    parts.append("</svg>")
    return "".join(parts)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cols", type=int, default=COLS, help="cells per row")
    ap.add_argument("--out", type=Path, default=OUT, help="destination .svg")
    args = ap.parse_args()

    static = os.environ.get("STATIC") == "1"
    grid = quantise(SRC, args.cols)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(build_svg(grid, static), encoding="utf-8")
    rows, cols = grid.shape
    print(
        f"wrote {args.out}  ({cols}x{rows} cells, "
        f"{args.out.stat().st_size // 1024} KB){' (static)' if static else ''}"
    )


if __name__ == "__main__":
    main()
