from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from datetime import date


API_KEY = os.environ["SERPAPI_API_KEY"]
ENDPOINT = "https://serpapi.com/search.json"

START_DATE = date(2026, 8, 1)
END_DATE = date(2026, 8, 24)

QUERY = "Bloomberg Surveillance Bloomberg Television"

OUTPUT = Path(
    "data/processed/surveillance/"
    "surveillance_video_inventory_v0_4.json"
)


def search(start: int) -> list[dict]:

    params = {
        "engine": "youtube",
        "search_query": QUERY,
        "api_key": API_KEY,
        "start": start,
    }

    url = ENDPOINT + "?" + urlencode(params)

    req = Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
    )

    with urlopen(req, timeout=60) as r:
        data = json.loads(
            r.read().decode("utf-8")
        )

    return data.get("video_results", [])


videos = {}

print("=" * 100)
print("BLOOMBERG SURVEILLANCE DISCOVERY v0.4")
print("=" * 100)

# 여러 검색 페이지 수집
for start in range(0, 100, 20):

    print(f"SEARCH PAGE START={start}")

    results = search(start)

    print("RESULTS:", len(results))

    if not results:
        break

    for item in results:

        title = item.get("title", "")
        video_id = item.get("video_id", "")

        if not video_id:
            continue

        if "bloomberg surveillance" not in title.lower():
            continue

        # 제목에서 날짜 확인
        import re

        m = re.search(
            r"Bloomberg Surveillance\s+"
            r"(\d{1,2})/(\d{1,2})/(\d{4})",
            title,
            re.IGNORECASE,
        )

        if not m:
            continue

        month, day, year = map(
            int,
            m.groups()
        )

        try:
            video_date = date(
                year,
                month,
                day,
            )
        except ValueError:
            continue

        if not (
            START_DATE
            <= video_date
            <= END_DATE
        ):
            continue

        videos[video_id] = {
            "video_id": video_id,
            "title": title,
            "link": item.get("link"),
            "video_date":
                video_date.isoformat(),
            "published_date":
                item.get("published_date"),
            "length":
                item.get("length"),
            "channel":
                item.get(
                    "channel",
                    {},
                ),
        }


inventory = sorted(
    videos.values(),
    key=lambda x: x["video_date"],
)


OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT.write_text(
    json.dumps(
        {
            "query": QUERY,
            "start_date":
                START_DATE.isoformat(),
            "end_date":
                END_DATE.isoformat(),
            "video_count":
                len(inventory),
            "videos":
                inventory,
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)


print()
print("=" * 100)
print("RESULT")
print("=" * 100)
print("VIDEOS FOUND:", len(inventory))

for video in inventory:
    print(
        video["video_date"],
        "|",
        video["video_id"],
        "|",
        video["title"],
    )

print()
print("OUTPUT:", OUTPUT)
print("=" * 100)

print(
    "DISCOVERY:",
    "PASS" if inventory else "FAIL",
)
