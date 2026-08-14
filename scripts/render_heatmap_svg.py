"""Render data/contributions.json as a self-animating contribution heatmap SVG.

The cells reveal on a diagonal sweep: the delay for each square is driven by
(week + weekday), so the wave travels from the top-left corner to the bottom
right, then freezes. Streak and volume stats are computed here rather than
scraped, so they always agree with the grid that is drawn.

Usage:
    python scripts/render_heatmap_svg.py
"""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "contributions.json"
OUT = ROOT / "assets" / "contrib-heatmap.svg"

W = 860.0
TITLEBAR_H = 36.0
PAD_X = 18.0
GUTTER = 30.0          # room for the Mon/Wed/Fri labels
CELL = 12.0
GAP = 3.0
PITCH = CELL + GAP
WEEKS = 53
GRID_X = PAD_X + GUTTER
GRID_Y = 68.0
GRID_H = 7 * PITCH - GAP
H = 240.0

BG = "#0d1117"
BORDER = "#30363d"
INK = "#c9d1d9"
DIM = "#8b949e"
ACCENT = "#7ee787"
KEY = "#79c0ff"
EMPTY = "#161b22"
EMPTY_STROKE = "#1f242c"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

SWEEP = 0.022          # seconds added per diagonal step
CELL_DUR = 0.40


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def weekday_row(iso: str) -> int:
    """GitHub's calendar rows run Sunday (0) through Saturday (6)."""
    return date.fromisoformat(iso).isoweekday() % 7


def streaks(days: list[dict]) -> tuple[int, int]:
    """Return (current, longest) streak of consecutive days with contributions.

    The current streak is allowed to end yesterday as well as today, because a
    day that has not been worked yet should not read as a broken streak.
    """
    longest = run = 0
    for day in days:
        run = run + 1 if day["count"] > 0 else 0
        longest = max(longest, run)

    # The calendar runs a few days past today, so drop those before walking
    # backwards from the most recent real day.
    today = date.today()
    past = [d for d in days if date.fromisoformat(d["date"]) <= today]

    current = 0
    for i, day in enumerate(reversed(past)):
        if day["count"] > 0:
            current += 1
        elif i == 0:
            continue  # today is not over yet, so an empty today is not a break
        else:
            break
    return current, longest


def titlebar(command: str) -> str:
    dots = "".join(
        f'<circle cx="{x}" cy="18" r="4.5" fill="{c}"/>'
        for x, c in ((20, "#ff5f56"), (36, "#ffbd2e"), (52, "#27c93f"))
    )
    return (
        f"<g>{dots}"
        f'<line x1="0" y1="36" x2="{W:.0f}" y2="36" stroke="{BORDER}"/>'
        f'<text class="mono" x="70" y="22" font-size="11" fill="{ACCENT}">efe@github'
        f'<tspan fill="{INK}">:</tspan><tspan fill="{KEY}">~</tspan>'
        f'<tspan fill="{INK}">$ {esc(command)}</tspan></text></g>'
    )


def month_labels(days: list[dict]) -> str:
    """One label per month, placed above the first week that month appears in."""
    seen: dict[int, int] = {}
    for day in days:
        d = date.fromisoformat(day["date"])
        seen.setdefault(d.month, day["week"])

    out = []
    for month, week in sorted(seen.items(), key=lambda kv: kv[1]):
        x = GRID_X + week * PITCH
        if x > GRID_X + WEEKS * PITCH - 24:
            continue
        out.append(
            f'<text class="mono" x="{x:.1f}" y="60" font-size="10" fill="{DIM}">{MONTHS[month - 1]}</text>'
        )
    return "".join(out)


def build_svg(data: dict, static: bool = False) -> str:
    days = data["days"]
    counts = [d["count"] for d in days]
    active = sum(1 for c in counts if c > 0)
    best = max(counts) if counts else 0
    current, longest = streaks(days)

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
        f'width="{W:.0f}" height="{H:.0f}" role="img" '
        f'aria-label="GitHub contribution heatmap: {data["total"]} contributions '
        f'from {data["from"]} to {data["to"]}">'
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
    parts.append(titlebar("./contributions.sh --year"))
    parts.append(month_labels(days))

    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        y = GRID_Y + row * PITCH + CELL - 2
        parts.append(
            f'<text class="mono" x="{PAD_X:.1f}" y="{y:.1f}" font-size="9" fill="{DIM}">{label}</text>'
        )

    for day in days:
        row = weekday_row(day["date"])
        x = GRID_X + day["week"] * PITCH
        y = GRID_Y + row * PITCH
        level = day["level"]
        fill = PALETTE[min(level, len(PALETTE) - 1)]
        stroke = f' stroke="{EMPTY_STROKE}"' if level == 0 else ""
        if static:
            anim = ""
            opacity = ""
        else:
            begin = f"{(day['week'] + row) * SWEEP:.2f}s"
            opacity = ' opacity="0"'
            anim = (
                f'<animate attributeName="opacity" from="0" to="1" begin="{begin}" '
                f'dur="{CELL_DUR}s" fill="freeze"/>'
                f'<animateTransform attributeName="transform" type="translate" '
                f'from="0 -9" to="0 0" begin="{begin}" dur="{CELL_DUR}s" fill="freeze"/>'
            )
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{CELL}" height="{CELL}" rx="2.5" '
            f'fill="{fill}"{stroke}{opacity}>{anim}'
            f"<title>{day['count']} on {day['date']}</title></rect>"
        )

    # Legend, bottom right.
    legend_y = GRID_Y + GRID_H + 22
    legend_x = W - PAD_X - 5 * PITCH - 74
    parts.append(
        f'<text class="mono" x="{legend_x:.1f}" y="{legend_y + 10:.1f}" font-size="10" fill="{DIM}">Less</text>'
    )
    for i, colour in enumerate(PALETTE):
        stroke = f' stroke="{EMPTY_STROKE}"' if i == 0 else ""
        parts.append(
            f'<rect x="{legend_x + 32 + i * PITCH:.1f}" y="{legend_y:.1f}" '
            f'width="{CELL}" height="{CELL}" rx="2.5" fill="{colour}"{stroke}/>'
        )
    parts.append(
        f'<text class="mono" x="{legend_x + 32 + 5 * PITCH + 4:.1f}" y="{legend_y + 10:.1f}" '
        f'font-size="10" fill="{DIM}">More</text>'
    )

    # Stats, bottom left.
    stats = [
        ("total", f"{data['total']}"),
        ("active days", f"{active}"),
        ("current streak", f"{current}"),
        ("longest streak", f"{longest}"),
        ("best day", f"{best}"),
    ]
    x = PAD_X
    for label, value in stats:
        parts.append(
            f'<text class="mono" x="{x:.1f}" y="{legend_y + 10:.1f}" font-size="10.5">'
            f'<tspan fill="{DIM}">{label} </tspan>'
            f'<tspan fill="{ACCENT}" font-weight="700">{value}</tspan></text>'
        )
        # Monospace advance is about 0.6em, so the drawn width is predictable
        # and the next stat can be placed without measuring the rendered text.
        x += (len(label) + 1 + len(value)) * 6.3 + 22

    parts.append(
        f'<text class="mono" x="{PAD_X:.1f}" y="{H - 14:.1f}" font-size="9.5" fill="{DIM}">'
        f'{data["from"]} .. {data["to"]}  -  refreshed daily by GitHub Actions</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


def main() -> None:
    static = os.environ.get("STATIC") == "1"
    data = json.loads(SRC.read_text(encoding="utf-8"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build_svg(data, static), encoding="utf-8")
    print(
        f"wrote {OUT.relative_to(ROOT)}  ({OUT.stat().st_size // 1024} KB)"
        f"{' (static)' if static else ''}"
    )


if __name__ == "__main__":
    main()
