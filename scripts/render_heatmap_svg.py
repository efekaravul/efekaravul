"""Render data/contributions.json as a self-animating contribution heatmap SVG.

The cells reveal on a diagonal sweep: each square's delay is driven by
(week + weekday), so the wave travels from the top-left corner to the bottom
right, holds, then loops. Streak and volume stats are computed here rather than
scraped, so they always agree with the grid that is drawn.

Usage:
    python scripts/render_heatmap_svg.py
    STATIC=1 python scripts/render_heatmap_svg.py
"""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

import panels as P

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "contributions.json"
OUT = ROOT / "assets" / "contrib-heatmap.svg"

W = P.PANEL_W
GUTTER = 30.0          # room for the Mon/Wed/Fri labels
CELL = 12.0
GAP = 3.0
PITCH = CELL + GAP
WEEKS = 53
GRID_X = P.PAD_X + GUTTER
GRID_Y = 68.0
GRID_H = 7 * PITCH - GAP
H = 240.0

EMPTY_STROKE = "#1f242c"
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

SWEEP = 0.022          # seconds added per diagonal step
CELL_DUR = 0.40


def weekday_row(iso: str) -> int:
    """GitHub's calendar rows run Sunday (0) through Saturday (6)."""
    return date.fromisoformat(iso).isoweekday() % 7


def streaks(days: list[dict]) -> tuple[int, int]:
    """Return (current, longest) streak of consecutive days with contributions."""
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


def month_labels(days: list[dict]) -> str:
    """One label per month, above the first week that month appears in."""
    seen: dict[int, int] = {}
    for day in days:
        seen.setdefault(date.fromisoformat(day["date"]).month, day["week"])

    out = []
    for month, week in sorted(seen.items(), key=lambda kv: kv[1]):
        x = GRID_X + week * PITCH
        if x > GRID_X + WEEKS * PITCH - 24:
            continue
        out.append(
            f'<text class="mono" x="{x:.1f}" y="60" font-size="10" fill="{P.DIM}">'
            f"{MONTHS[month - 1]}</text>"
        )
    return "".join(out)


def build_svg(data: dict, static: bool = False) -> str:
    days = data["days"]
    counts = [d["count"] for d in days]
    active = sum(1 for c in counts if c > 0)
    best = max(counts) if counts else 0
    current, longest = streaks(days)

    out = P.open_svg(
        W, H,
        f"GitHub contribution heatmap: {data['total']} contributions "
        f"from {data['from']} to {data['to']}",
    )
    out.append(P.titlebar(W, "./contributions.sh --year"))
    out.append(month_labels(days))

    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        y = GRID_Y + row * PITCH + CELL - 2
        out.append(
            f'<text class="mono" x="{P.PAD_X:.1f}" y="{y:.1f}" font-size="9" '
            f'fill="{P.DIM}">{label}</text>'
        )

    for day in days:
        row = weekday_row(day["date"])
        x = GRID_X + day["week"] * PITCH
        y = GRID_Y + row * PITCH
        level = day["level"]
        fill = PALETTE[min(level, len(PALETTE) - 1)]
        stroke = f' stroke="{EMPTY_STROKE}"' if level == 0 else ""

        if static:
            opacity, anim = "", ""
        else:
            begin = (day["week"] + row) * SWEEP
            opacity = ' opacity="0"'
            anim = (
                P.loop("opacity", "0", "1", begin, CELL_DUR)
                + P.loop("transform", "0 -9", "0 0", begin, CELL_DUR, transform=True)
            )
        out.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{CELL}" height="{CELL}" rx="2.5" '
            f'fill="{fill}"{stroke}{opacity}>{anim}'
            f"<title>{day['count']} on {day['date']}</title></rect>"
        )

    # Legend, bottom right.
    legend_y = GRID_Y + GRID_H + 22
    legend_x = W - P.PAD_X - 5 * PITCH - 74
    out.append(
        f'<text class="mono" x="{legend_x:.1f}" y="{legend_y + 10:.1f}" font-size="10" '
        f'fill="{P.DIM}">Less</text>'
    )
    for i, colour in enumerate(PALETTE):
        stroke = f' stroke="{EMPTY_STROKE}"' if i == 0 else ""
        out.append(
            f'<rect x="{legend_x + 32 + i * PITCH:.1f}" y="{legend_y:.1f}" '
            f'width="{CELL}" height="{CELL}" rx="2.5" fill="{colour}"{stroke}/>'
        )
    out.append(
        f'<text class="mono" x="{legend_x + 32 + 5 * PITCH + 4:.1f}" '
        f'y="{legend_y + 10:.1f}" font-size="10" fill="{P.DIM}">More</text>'
    )

    # Stats, bottom left.
    stats = [
        ("total", str(data["total"])),
        ("active days", str(active)),
        ("current streak", str(current)),
        ("longest streak", str(longest)),
        ("best day", str(best)),
    ]
    x = P.PAD_X
    for label, value in stats:
        out.append(
            f'<text class="mono" x="{x:.1f}" y="{legend_y + 10:.1f}" font-size="10.5">'
            f'<tspan fill="{P.DIM}">{label} </tspan>'
            f'<tspan fill="{P.ACCENT}" font-weight="700">{value}</tspan></text>'
        )
        # Monospace advance is about 0.6em, so the drawn width is predictable
        # and the next stat can be placed without measuring the rendered text.
        x += (len(label) + 1 + len(value)) * 6.3 + 22

    out.append(
        f'<text class="mono" x="{P.PAD_X:.1f}" y="{H - 14:.1f}" font-size="9.5" '
        f'fill="{P.DIM}">{data["from"]} .. {data["to"]} — refreshed daily by '
        f"GitHub Actions</text>"
    )
    out.append("</svg>")
    return "".join(out)


def main() -> None:
    static = os.environ.get("STATIC") == "1"
    data = json.loads(SRC.read_text(encoding="utf-8"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build_svg(data, static), encoding="utf-8")
    print(f"wrote assets/contrib-heatmap.svg  ({OUT.stat().st_size // 1024} KB)"
          f"{' (static)' if static else ''}")


if __name__ == "__main__":
    main()
