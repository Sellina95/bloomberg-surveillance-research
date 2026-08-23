from __future__ import annotations

import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path


CHANNEL_ID = "UCIALMKvObZNtJ6AmdCLP7Lg"

START_DATE = date(2026, 8, 1)
END_DATE = date(2026, 8, 24)

FEED_URL = (
    "https://www.youtube.com/feeds/videos.xml"
    f"?channel_id={CHANNEL_ID}"
)

OUTPUT = Path(
    "data/processed/surveillance/"
    "surveillance_feed_inventory_v0_1.json"
)

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
}


def fetch_feed() -> bytes:

    request = urllib.request.Request(
        FEED_URL,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=60,
    ) as response:

        return response.read()


xml_data = fetch_feed()

root = ET.fromstring(xml_data)

videos = []

for entry in root.findall(
    "atom:entry",
    NS,
):

    title = entry.findtext(
        "atom:title",
        default="",
        namespaces=NS,
    )

    video_id = entry.findtext(
        "yt:videoId",
        default="",
        namespaces=NS,
    )

    published = entry.findtext(
        "atom:published",
        default="",
        namespaces=NS,
    )

    link = entry.find(
        "atom:link",
        NS,
    )

    href = (
        link.attrib.get("href")
        if link is not None
        else ""
    )

    videos.append(
        {
            "video_id": video_id,
            "title": title,
            "published": published,
            "link": href,
        }
    )


print("=" * 100)
print("BLOOMBERG SURVEILLANCE FEED DISCOVERY")
print("=" * 100)
print("FEED ENTRIES:", len(videos))
print("=" * 100)


# NOTE:
# YouTube channel RSS only exposes the channel's recent feed.
# We filter whatever entries are actually present.

selected = []

pattern = re.compile(
    r"Bloomberg Surveillance\s+"
    r"(\d{1,2})/(\d{1,2})/(\d{4})",
    re.IGNORECASE,
)


for video in videos:

    match = pattern.search(
        video["title"]
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

    if START_DATE <= video_date <= END_DATE:

        video["video_date"] = (
            video_date.isoformat()
        )

        selected.append(video)


selected.sort(
    key=lambda x: x["video_date"]
)


OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT.write_text(
    json.dumps(
        {
            "channel_id":
                CHANNEL_ID,
            "start_date":
                START_DATE.isoformat(),
            "end_date":
                END_DATE.isoformat(),
            "feed_entries":
                len(videos),
            "selected_count":
                len(selected),
            "videos":
                selected,
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
    "FEED ENTRIES:",
    len(videos),
)
print(
    "SELECTED:",
    len(selected),
)

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
