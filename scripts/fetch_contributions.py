"""Collect the public contribution calendar into data/contributions.json.

Two sources, in order of preference:

1. The GraphQL API (`contributionsCollection`). This is the same data the
   profile page renders and it reflects repository deletions and rewritten
   authorship immediately. It needs a token, which the workflow supplies from
   the run's own GITHUB_TOKEN.
2. The public HTML calendar at /users/<name>/contributions. No token needed, so
   this still works from a fork or a local run, but GitHub serves it from a
   cache that can lag the real numbers by a day or more.

Usage:
    python scripts/fetch_contributions.py [--user efekaravul]
"""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "contributions.json"

URL = "https://github.com/users/{user}/contributions"
GRAPHQL_URL = "https://api.github.com/graphql"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; profile-art/1.0; +https://github.com/efekaravul)",
    "X-Requested-With": "XMLHttpRequest",
}

# "No contributions on August 10th." / "5 contributions on March 2nd."
COUNT_RE = re.compile(r"^(No|\d+)\s+contributions?", re.IGNORECASE)

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        weeks {
          contributionDays { date contributionCount contributionLevel }
        }
      }
    }
  }
}
"""

LEVELS = {
    "NONE": 0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE": 4,
}


def parse_count(tooltip: str) -> int:
    m = COUNT_RE.match(tooltip.strip())
    if not m:
        return 0
    return 0 if m.group(1).lower() == "no" else int(m.group(1))


def summarise(user: str, days: list[dict]) -> dict:
    days.sort(key=lambda d: d["date"])
    return {
        "user": user,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "from": days[0]["date"],
        "to": days[-1]["date"],
        "total": sum(d["count"] for d in days),
        "days": days,
    }


def fetch_graphql(user: str, token: str) -> dict:
    now = datetime.now(timezone.utc)
    resp = requests.post(
        GRAPHQL_URL,
        json={
            "query": QUERY,
            "variables": {
                "login": user,
                # The API caps the window at one year; a day of slack keeps the
                # request valid whichever side of midnight UTC it lands on.
                "from": (now - timedelta(days=364)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "to": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        },
        headers={"Authorization": f"bearer {token}", "User-Agent": HEADERS["User-Agent"]},
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("errors"):
        raise RuntimeError(payload["errors"][0].get("message", "graphql error"))

    weeks = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = [
        {
            "date": day["date"],
            "week": ix,
            "level": LEVELS.get(day["contributionLevel"], 0),
            "count": day["contributionCount"],
        }
        for ix, week in enumerate(weeks)
        for day in week["contributionDays"]
    ]
    if not days:
        raise RuntimeError("graphql returned an empty calendar")
    return summarise(user, days)


def fetch_html(user: str) -> dict:
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
    return summarise(user, days)


def fetch(user: str) -> dict:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        try:
            data = fetch_graphql(user, token)
            print("source: graphql")
            return data
        except Exception as exc:  # fall back rather than leave the README stale
            print(f"graphql failed ({exc}); falling back to the HTML calendar")
    else:
        print("no GITHUB_TOKEN in the environment; using the HTML calendar")
    data = fetch_html(user)
    print("source: html")
    return data


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
