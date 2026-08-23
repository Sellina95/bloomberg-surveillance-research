from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path


INPUT = Path(
    "data/processed/surveillance/"
    "surveillance_video_inventory_v0_3.json"
)

OUTPUT = Path(
    "data/processed/surveillance/"
    "surveillance_video_inventory_august_2026.json"
)

START = date(2026, 8, 1)
END = date(2026, 8, 24)

DATE_PATTERN = re.compile(
    r"Bloomberg Surveillance\s+"
    r"(\d{1,2})/(\d{1,2})/(\d{4})",
    re.IGNORECASE,
)


data = json.loads(
    INPUT.read_text(
        encoding="utf-8"
    )
)

selected = []
excluded = []
unparseable = []


for video in data["videos"]:

    title = video["title"]

    match = DATE_PATTERN.search(title)

    if not match:
        unparseable.append(video)
        continue

    month, day, year = map(
        int,
        match.groups()
    )

    video_date = date(
        year,
        month,
        day,
    )

    video["video_date"] = (
        video_date.isoformat()
    )

    if START <= video_date <= END:

        selected.append(video)

    else:

        excluded.append(video)


selected.sort(
    key=lambda x: x["video_date"]
)

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT.write_text(
    json.dumps(
        {
            "start_date":
                START.isoformat(),
            "end_date":
                END.isoformat(),
            "selected_count":
                len(selected),
            "excluded_count":
                len(excluded),
            "unparseable_count":
                len(unparseable),
            "videos":
                selected,
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)


print("=" * 100)
print("SURVEILLANCE INVENTORY DATE FILTER")
print("=" * 100)
print(
    "RANGE:",
    START,
    "->",
    END,
)
print(
    "SELECTED:",
    len(selected)
)
print(
    "EXCLUDED:",
    len(excluded)
)
print(
    "UNPARSEABLE:",
    len(unparseable)
)

print()
print("SELECTED VIDEOS")

for video in selected:
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

if selected:
    print("DATE FILTER: PASS")
else:
    print("DATE FILTER: FAIL")
