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
    "surveillance_video_inventory_v0_3.json"
)


def search_youtube(query: str) -> list[dict]:

    params = {
        "engine": "youtube",
        "search_query": query,
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


videos = {}

print("=" * 100)
print("BLOOMBERG SURVEILLANCE DISCOVERY v0.3")
print("=" * 100)


for query in QUERIES:

    print()
    print("QUERY:", query)

    results = search_youtube(query)

    print("RESULTS:", len(results))

    for item in results:

        title = item.get(
            "title",
            ""
        )

        video_id = item.get(
            "video_id",
            ""
        )

        link = item.get(
            "link",
            ""
        )

        # 실제 SerpApi 응답 필드 기준
        if not video_id:
            continue

        if (
            "bloomberg surveillance"
            not in title.lower()
        ):
            continue

        videos[video_id] = {
            "video_id": video_id,
            "title": title,
            "link": link,
            "channel_name":
                item.get(
                    "channel",
                    {}
                ).get(
                    "name"
                ),
            "channel_verified":
                item.get(
                    "channel",
                    {}
                ).get(
                    "verified"
                ),
            "published_date":
                item.get(
                    "published_date"
                ),
            "length":
                item.get(
                    "length"
                ),
            "description":
                item.get(
                    "description"
                ),
        }


inventory = list(
    videos.values()
)


OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT.write_text(
    json.dumps(
        {
            "schema_version":
                "surveillance_video_inventory_v0_3",
            "query_count":
                len(QUERIES),
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
print("DISCOVERY RESULT")
print("=" * 100)
print(
    "UNIQUE VIDEOS:",
    len(inventory)
)

for video in inventory:

    print(
        video["video_id"],
        "|",
        video["title"],
        "|",
        video["length"],
    )

print()
print(
    "OUTPUT:",
    OUTPUT
)
print("=" * 100)

if inventory:
    print("DISCOVERY: PASS")
else:
    print("DISCOVERY: FAIL")
