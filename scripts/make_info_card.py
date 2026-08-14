"""Render the neofetch-style info panel as a self-animating SVG.

Each row fades in and slides right, staggered top to bottom, then freezes.
Set STATIC=1 to emit the finished state with no animation, which is handy when
you want a still preview of the layout.

Usage:
    python scripts/make_info_card.py
    STATIC=1 python scripts/make_info_card.py
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "info-card.svg"

W = 490.0
# The avatar panel is 402x426 shown at width 370, so it lands ~392 tall. Matching
# that here keeps the two panels level when the README sets them side by side.
H = 392.0

BG = "#0d1117"
BORDER = "#30363d"
INK = "#c9d1d9"
DIM = "#8b949e"
KEY = "#79c0ff"
ACCENT = "#7ee787"
RULE = "#21262d"

TITLE = "efe.karavul"
SUBTITLE = "aspiring data engineer"

ROWS: list[tuple[str, str]] = [
    ("Role", "Data Engineering & Machine Learning"),
    ("Focus", "End-to-end pipelines - predictive models"),
    ("Language", "Python 3.12"),
    ("Core", "pandas - NumPy - scikit-learn"),
    ("Viz", "Matplotlib - Seaborn - Plotly"),
    ("Env", "PyCharm - Jupyter - Git"),
    ("Learning", "SVM kernels - Naive Bayes - encoding"),
    ("Method", "Leakage-safe prep, honest evaluation"),
    ("Portfolio", "Applied-Data-Engineering-And-ML"),
    ("Kaggle", "kaggle.com/efekaravul"),
    ("Docs", "Bilingual TR / EN on every notebook"),
    ("Contact", "efekaravul@gmail.com"),
]

# The neofetch colour strip along the bottom.
SWATCHES = [
    "#ff7b72", "#ffa657", "#e3b341", "#7ee787",
    "#79c0ff", "#d2a8ff", "#f0883e", "#8b949e",
]

PAD_X = 22.0
TITLEBAR_H = 36.0
KEY_X = PAD_X
VAL_X = PAD_X + 92.0
ROW_STEP = 20.5
ROW_START = 112.0
FONT = 11.5

STEP_DELAY = 0.085
FADE_DUR = 0.45


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def reveal(index: int, static: bool) -> tuple[str, str]:
    """Return (opening <g> attributes, inner animation elements) for one row."""
    if static:
        return ' opacity="1"', ""
    begin = f"{index * STEP_DELAY:.2f}s"
    anim = (
        f'<animate attributeName="opacity" from="0" to="1" begin="{begin}" '
        f'dur="{FADE_DUR}s" fill="freeze"/>'
        f'<animateTransform attributeName="transform" type="translate" '
        f'from="-10 0" to="0 0" begin="{begin}" dur="{FADE_DUR}s" fill="freeze"/>'
    )
    return ' opacity="0"', anim


def titlebar(width: float, command: str) -> str:
    dots = "".join(
        f'<circle cx="{x}" cy="18" r="4.5" fill="{c}"/>'
        for x, c in ((20, "#ff5f56"), (36, "#ffbd2e"), (52, "#27c93f"))
    )
    return (
        f"<g>{dots}"
        f'<line x1="0" y1="36" x2="{width:.0f}" y2="36" stroke="{BORDER}"/>'
        f'<text class="mono" x="70" y="22" font-size="11" fill="{ACCENT}">efe@github'
        f'<tspan fill="{INK}">:</tspan><tspan fill="{KEY}">~</tspan>'
        f'<tspan fill="{INK}">$ {esc(command)}</tspan></text></g>'
    )


def build_svg(static: bool) -> str:
    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
        f'width="{W:.0f}" height="{H:.0f}" role="img" '
        f'aria-label="Profile summary card for Efe Karavul">'
    )
    parts.append(
        "<style>"
        ".mono{font-family:ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,"
        "'DejaVu Sans Mono',monospace}"
        "</style>"
    )
    parts.append(
        f'<rect x="0.5" y="0.5" width="{W - 1:.0f}" height="{H - 1:.0f}" '
        f'rx="10" fill="{BG}" stroke="{BORDER}"/>'
    )
    parts.append(titlebar(W, "neofetch"))

    parts.append('<g class="mono">')

    # Title block.
    attrs, anim = reveal(0, static)
    parts.append(
        f"<g{attrs}>{anim}"
        f'<text x="{PAD_X}" y="72" font-size="17" font-weight="700" fill="{ACCENT}">{TITLE}</text>'
        f'<text x="{PAD_X}" y="90" font-size="11" fill="{DIM}">{SUBTITLE}</text>'
        f"</g>"
    )

    attrs, anim = reveal(1, static)
    parts.append(
        f"<g{attrs}>{anim}"
        f'<line x1="{PAD_X}" y1="100" x2="{W - PAD_X}" y2="100" stroke="{RULE}"/>'
        f"</g>"
    )

    for i, (key, value) in enumerate(ROWS):
        y = ROW_START + i * ROW_STEP
        attrs, anim = reveal(i + 2, static)
        parts.append(
            f"<g{attrs}>{anim}"
            f'<text x="{KEY_X}" y="{y:.1f}" font-size="{FONT}" fill="{KEY}">{esc(key)}</text>'
            f'<text x="{VAL_X}" y="{y:.1f}" font-size="{FONT}" fill="{INK}">{esc(value)}</text>'
            f"</g>"
        )

    # Colour strip.
    strip_y = ROW_START + len(ROWS) * ROW_STEP + 14
    attrs, anim = reveal(len(ROWS) + 2, static)
    swatches = "".join(
        f'<rect x="{PAD_X + i * 26:.1f}" y="{strip_y:.1f}" width="22" height="11" rx="2" fill="{c}"/>'
        for i, c in enumerate(SWATCHES)
    )
    parts.append(f"<g{attrs}>{anim}{swatches}</g>")

    parts.append("</g></svg>")
    return "".join(parts)


def main() -> None:
    static = os.environ.get("STATIC") == "1"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build_svg(static), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}{' (static)' if static else ''}")


if __name__ == "__main__":
    main()
