from __future__ import annotations

import json
import os
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_KEY = os.environ["SERPAPI_API_KEY"]
ENDPOINT = "https://serpapi.com/search.json"

CHANNEL_HANDLE = "@markets"

START_DATE = date(2026, 8, 1)
END_DATE = date(2026, 8, 24)

OUTPUT = Path(
    "data/processed/surveillance/"
    "surveillance_channel_inventory_v0_1.json"
)


def fetch_channel_videos() -> list[dict]:

    params = {
        "engine": "youtube",
        "channel": CHANNEL_HANDLE,
        "api_key": API_KEY,
    }

    url = (
        ENDPOINT
        + "?"
        + urlencode(params)
    )

    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
    )

    with urlopen(
        request,
        timeout=60,
    ) as response:

        data = json.loads(
            response.read().decode("utf-8")
        )

    return data.get(
        "video_results",
        []
    )


DATE_PATTERN = re.compile(
    r"Bloomberg Surveillance\s+"
    r"(\d{1,2})/(\d{1,2})/(\d{4})",
    re.IGNORECASE,
)


print("=" * 100)
print("BLOOMBERG CHANNEL DISCOVERY v0.1")
print("=" * 100)
print("CHANNEL:", CHANNEL_HANDLE)
print(
    "RANGE:",
    START_DATE,
    "->",
    END_DATE,
)
print("=" * 100)


videos = fetch_channel_videos()

print(
    "CHANNEL RESULTS:",
    len(videos)
)


selected = {}

for item in videos:

    title = item.get(
        "title",
        ""
    )

    video_id = item.get(
        "video_id",
        ""
    )

    if not video_id:
        continue

    match = DATE_PATTERN.search(
        title
    )

    if not match:
        continue

    month, day, year = map(
        int,
        match.groups()
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

    selected[video_id] = {
        "video_id":
            video_id,
        "title":
            title,
        "link":
            item.get("link"),
        "video_date":
            video_date.isoformat(),
        "published_date":
            item.get(
                "published_date"
            ),
        "length":
            item.get(
                "length"
            ),
        "channel":
            item.get(
                "channel",
                {}
            ),
    }


inventory = sorted(
    selected.values(),
    key=lambda x:
        x["video_date"],
)


OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT.write_text(
    json.dumps(
        {
            "schema_version":
                "surveillance_channel_inventory_v0_1",
            "channel":
                CHANNEL_HANDLE,
            "start_date":
                START_DATE.isoformat(),
            "end_date":
                END_DATE.isoformat(),
            "channel_results":
                len(videos),
            "selected_count":
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
print(
    "CHANNEL RESULTS:",
    len(videos)
)
print(
    "SELECTED:",
    len(inventory)
)

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

if inventory:
    print("CHANNEL DISCOVERY: PASS")
else:
    print("CHANNEL DISCOVERY: FAIL")
