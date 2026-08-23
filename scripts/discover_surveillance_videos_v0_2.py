from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_KEY = os.environ["SERPAPI_API_KEY"]

ENDPOINT = "https://serpapi.com/search.json"

QUERIES = [
    "Bloomberg Surveillance Bloomberg Television",
    "Bloomberg Surveillance Bloomberg",
]

OUTPUT = Path(
    "data/processed/surveillance/"
    "surveillance_video_inventory_v0_2.json"
)


def search(query: str) -> list[dict]:
    params = {
        "engine": "youtube",
        "search_query": query,
        "api_key": API_KEY,
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
print("BLOOMBERG SURVEILLANCE DISCOVERY v0.2")
print("=" * 100)

for query in QUERIES:

    print()
    print("QUERY:", query)

    results = search(query)

    print("RESULTS:", len(results))

    for item in results:

        title = item.get("title", "")
        video_id = item.get("id", "")
        link = item.get("link", "")

        if not video_id:
            continue

        if "surveillance" not in title.lower():
            continue

        videos[video_id] = {
            "video_id": video_id,
            "title": title,
            "link": link,
            "channel": item.get(
                "channel",
                {}
            ),
            "published":
                item.get("published"),
            "length":
                item.get("length"),
        }


inventory = list(videos.values())


OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT.write_text(
    json.dumps(
        {
            "query_count": len(QUERIES),
            "video_count": len(inventory),
            "videos": inventory,
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

print()
print("=" * 100)
print("DISCOVERY RESULT")
print("=" * 100)
print("UNIQUE VIDEOS:", len(inventory))

for video in inventory:
    print(
        video["video_id"],
        "|",
        video["title"],
        "|",
        video.get("published_date"),
    )

print()
print("OUTPUT:", OUTPUT)
print("=" * 100)
