"""Scrape the public contribution calendar into data/contributions.json.

GitHub serves the calendar as plain HTML at /users/<name>/contributions with no
authentication, so this needs no token and works from a fork or a scheduled
Action alike. Day counts live in the <tool-tip> elements rather than on the
cells themselves, so the two have to be joined on the cell id.

Usage:
    python scripts/fetch_contributions.py [--user efekaravul]
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "contributions.json"

URL = "https://github.com/users/{user}/contributions"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; profile-art/1.0; +https://github.com/efekaravul)",
    "X-Requested-With": "XMLHttpRequest",
}

# "No contributions on August 10th." / "5 contributions on March 2nd."
COUNT_RE = re.compile(r"^(No|\d+)\s+contributions?", re.IGNORECASE)


def parse_count(tooltip: str) -> int:
    m = COUNT_RE.match(tooltip.strip())
    if not m:
        return 0
    return 0 if m.group(1).lower() == "no" else int(m.group(1))


def fetch(user: str) -> dict:
    resp = requests.get(URL.format(user=user), headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    counts = {
        tip["for"]: parse_count(tip.get_text())
        for tip in soup.find_all("tool-tip")
        if tip.get("for")
    }

    days = []
    for cell in soup.select("td.ContributionCalendar-day"):
        date = cell.get("data-date")
        if not date:
            continue
        days.append(
            {
                "date": date,
                "week": int(cell.get("data-ix", 0)),
                "level": int(cell.get("data-level", 0)),
                "count": counts.get(cell.get("id", ""), 0),
            }
        )

    if not days:
        raise SystemExit("no contribution cells found - GitHub markup may have changed")

    days.sort(key=lambda d: d["date"])
    return {
        "user": user,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "from": days[0]["date"],
        "to": days[-1]["date"],
        "total": sum(d["count"] for d in days),
        "days": days,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default="efekaravul")
    args = ap.parse_args()

    data = fetch(args.user)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    print(
        f"wrote {OUT.relative_to(ROOT)} - {len(data['days'])} days, "
        f"{data['total']} contributions ({data['from']} .. {data['to']})"
    )


if __name__ == "__main__":
    main()
