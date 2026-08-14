"""Quantise the avatar image into a terminal-style mosaic.

The cells are <rect> elements rather than ASCII characters on purpose. Character
art depends on the reader's monospace font to hold its grid, and every GitHub
reader has a different one, so glyph advances drift and the picture smears.
Rects render identically everywhere. This avatar makes it worse than usual: a
thin, specular metal ring has almost no broad flat tonal regions, which is
exactly the content an ASCII density ramp reproduces worst.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

import panels as P

SRC = Path(__file__).resolve().parents[1] / "assets" / "avatar-src.png"

# Contrast window. The floor sits above 0 so noise in the black backdrop stays
# empty, and the ceiling well below 255 so the specular highlights do not
# swallow the whole top of the ramp.
LEVEL_LO = 10.0
LEVEL_HI = 155.0
GAMMA = 0.78

# Index 0 is never drawn, so the panel background shows through as empty space.
SHADES = ["#0d1117", "#2d3540", "#586675", "#8b98a6", "#c2ccd6", "#eef3f8"]

ROW_DELAY = 0.022
ROW_DUR = 0.40


def autocrop(img: Image.Image, threshold: int = 12, margin: int = 4) -> Image.Image:
    """Trim the dead black border so the subject fills the mosaic."""
    a = np.asarray(img, dtype=np.uint8)
    ys, xs = np.where(a > threshold)
    if ys.size == 0:
        return img
    top, bottom = max(0, ys.min() - margin), min(a.shape[0], ys.max() + 1 + margin)
    left, right = max(0, xs.min() - margin), min(a.shape[1], xs.max() + 1 + margin)
    return img.crop((left, top, right, bottom))


def quantise(cols: int, src: Path = SRC) -> np.ndarray:
    """Downsample to a square-celled grid of shade indices."""
    img = autocrop(Image.open(src).convert("L"))
    w, h = img.size
    rows = max(1, round(cols * h / w))
    a = np.asarray(img.resize((cols, rows), Image.LANCZOS), dtype=np.float32)
    a = np.clip((a - LEVEL_LO) / (LEVEL_HI - LEVEL_LO), 0.0, 1.0) ** GAMMA
    return np.clip((a * (len(SHADES) - 1)).round().astype(int), 0, len(SHADES) - 1)


def _runs(row: np.ndarray) -> list[tuple[int, int, int]]:
    """Collapse a row into (start, length, level) runs so one rect covers many cells.

    A per-cell rect would put thousands of elements in the file; merging equal
    neighbours cuts that several times over without changing a pixel.
    """
    out: list[tuple[int, int, int]] = []
    start = 0
    for i in range(1, len(row) + 1):
        if i == len(row) or row[i] != row[start]:
            if row[start] != 0:
                out.append((start, i - start, int(row[start])))
            start = i
    return out


def render(grid: np.ndarray, x0: float, y0: float, width: float,
           prefix: str, static: bool) -> tuple[str, str, float]:
    """Return (clipPath defs, drawn rows, mosaic height).

    Each row is clipped by a rect that wipes from zero width to full, so the
    picture types itself in from the top down like a terminal drawing it.
    """
    rows, cols = grid.shape
    cell = width / cols
    defs: list[str] = []
    body: list[str] = []

    for r in range(rows):
        segments = _runs(grid[r])
        if not segments:
            continue
        y = y0 + r * cell
        clip_id = f"{prefix}{r}"

        if static:
            defs.append(
                f'<clipPath id="{clip_id}"><rect x="{x0:.1f}" y="{y:.1f}" '
                f'width="{width:.1f}" height="{cell:.1f}"/></clipPath>'
            )
        else:
            defs.append(
                f'<clipPath id="{clip_id}"><rect x="{x0:.1f}" y="{y:.1f}" '
                f'width="0" height="{cell:.1f}">'
                + P.loop("width", "0", f"{width:.1f}", r * ROW_DELAY, ROW_DUR)
                + "</rect></clipPath>"
            )

        # Group the row's runs by shade so `fill` is written once per level
        # instead of once per rect - worth about a fifth of the file size.
        by_level: dict[int, list[tuple[int, int]]] = {}
        for start, length, level in segments:
            by_level.setdefault(level, []).append((start, length))

        groups = "".join(
            f'<g fill="{SHADES[level]}">'
            + "".join(
                f'<rect x="{x0 + s * cell:.1f}" y="{y:.1f}" '
                f'width="{n * cell:.1f}" height="{cell:.1f}"/>'
                for s, n in spans
            )
            + "</g>"
            for level, spans in sorted(by_level.items())
        )
        body.append(f'<g clip-path="url(#{clip_id})">{groups}</g>')

    return "".join(defs), "".join(body), rows * cell
