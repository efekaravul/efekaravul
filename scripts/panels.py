"""Shared chrome, palette and animation helpers for the profile SVG panels.

Every panel is drawn at one width and shown at that width in the README, so the
panels can never wrap or drift out of alignment with each other no matter how
narrow the reader's window gets - a single image scales as one unit.

On animation: a play-once-and-freeze reveal is effectively invisible on GitHub,
because the SVG clock starts when the image loads and the whole reveal is over
before a reader has scrolled to it. So every animation here runs on a long loop
instead: it stays hidden until its turn, reveals, then holds the finished state
for the rest of the cycle before starting over.
"""

from __future__ import annotations

PANEL_W = 860.0
TITLEBAR_H = 36.0
PAD_X = 18.0

CYCLE = 6.0         # seconds; the reveal takes ~2.3s and the rest is hold time

BG = "#0d1117"
BORDER = "#30363d"
RULE = "#21262d"
INK = "#c9d1d9"
DIM = "#8b949e"
FAINT = "#6e7681"
ACCENT = "#7ee787"  # prompt green
KEY = "#79c0ff"     # label blue
WARM = "#ffa657"

MONO = (
    "font-family:ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,"
    "'DejaVu Sans Mono',monospace"
)


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def open_svg(width: float, height: float, label: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" '
        f'width="{width:.0f}" height="{height:.0f}" role="img" aria-label="{esc(label)}">',
        f"<style>.mono{{{MONO}}}</style>",
        f'<rect x="0.5" y="0.5" width="{width - 1:.0f}" height="{height - 1:.0f}" '
        f'rx="10" fill="{BG}" stroke="{BORDER}"/>',
    ]


def titlebar(width: float, command: str) -> str:
    """Window chrome with a shell prompt, shared by every panel."""
    dots = "".join(
        f'<circle cx="{x}" cy="18" r="4.5" fill="{c}"/>'
        for x, c in ((20, "#ff5f56"), (36, "#ffbd2e"), (52, "#27c93f"))
    )
    return (
        f"<g>{dots}"
        f'<line x1="0" y1="{TITLEBAR_H:.0f}" x2="{width:.0f}" y2="{TITLEBAR_H:.0f}" stroke="{BORDER}"/>'
        f'<text class="mono" x="70" y="22" font-size="11" fill="{ACCENT}">efe@github'
        f'<tspan fill="{INK}">:</tspan><tspan fill="{KEY}">~</tspan>'
        f'<tspan fill="{INK}">$ {esc(command)}</tspan></text></g>'
    )


def _keytimes(begin: float, dur: float) -> str:
    """Fractions of the cycle at which the reveal starts and ends."""
    t1 = min(max(begin, 0.01), CYCLE - 0.2) / CYCLE
    t2 = min(begin + dur, CYCLE - 0.05) / CYCLE
    return f"0;{t1:.4f};{max(t2, t1 + 0.001):.4f};1"


def loop(attr: str, hidden: str, shown: str, begin: float, dur: float,
         transform: bool = False) -> str:
    """One looping animation: hold hidden, reveal, hold shown until the cycle ends."""
    tag = "animateTransform" if transform else "animate"
    kind = ' type="translate"' if transform else ""
    return (
        f'<{tag} attributeName="{attr}"{kind} '
        f'values="{hidden};{hidden};{shown};{shown}" keyTimes="{_keytimes(begin, dur)}" '
        f'dur="{CYCLE}s" repeatCount="indefinite"/>'
    )


def reveal(index: int, static: bool, step: float = 0.075, dur: float = 0.45,
           dx: float = -10.0) -> tuple[str, str]:
    """Attributes and animation elements for one staggered row reveal."""
    if static:
        return ' opacity="1"', ""
    begin = index * step
    return ' opacity="0"', (
        loop("opacity", "0", "1", begin, dur)
        + loop("transform", f"{dx:.0f} 0", "0 0", begin, dur, transform=True)
    )
