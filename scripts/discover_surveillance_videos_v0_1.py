from __future__ import annotations

import json
import os
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_KEY = os.environ["SERPAPI_API_KEY"]

ENDPOINT = "https://serpapi.com/search.json"

START_DATE = date(2026, 8, 1)
END_DATE = date(2026, 8, 24)

OUTPUT = Path(
    "data/processed/surveillance/"
    "surveillance_video_inventory_v0_1.json"
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
            "User-Agent":
                "Mozilla/5.0"
        },
    )

    with urlopen(
        request,
        timeout=60,
    ) as response:

        return json.loads(
            response.read().decode("utf-8")
        ).get(
            "video_results",
            []
        )


def date_range():

    current = START_DATE

    while current <= END_DATE:

        yield current

        current += timedelta(
            days=1
        )


results = []

print("=" * 100)
print("BLOOMBERG SURVEILLANCE VIDEO DISCOVERY")
print("=" * 100)
print(
    f"DATE RANGE: "
    f"{START_DATE} -> {END_DATE}"
)
print("=" * 100)


for target_date in date_range():

    date_text = target_date.strftime(
        "%B %d %Y"
    )

    query = (
        f"Bloomberg Surveillance "
        f"{date_text}"
    )

    print()
    print(
        f"SEARCH | {target_date.isoformat()}"
    )

    try:

        videos = search_youtube(
            query
        )

    except Exception as exc:

        print(
            "FAIL:",
            exc
        )

        results.append(
            {
                "date":
                    target_date.isoformat(),
                "status":
                    "FAILED",
                "error":
                    str(exc),
            }
        )

        continue


    candidates = []

    for video in videos:

        title = video.get(
            "title",
            ""
        )

        link = video.get(
            "link",
            ""
        )

        video_id = video.get(
            "id",
            ""
        )

        # We only want Bloomberg Surveillance
        if (
            "surveillance"
            not in title.lower()
        ):
            continue

        candidates.append(
            {
                "video_id":
                    video_id,
                "title":
                    title,
                "link":
                    link,
                "channel":
                    video.get(
                        "channel",
                        {}
                    ),
                "length":
                    video.get(
                        "length"
                    ),
            }
        )


    # Deduplicate by video ID

    unique = {}

    for video in candidates:

        if video["video_id"]:
            unique[
                video["video_id"]
            ] = video

    candidates = list(
        unique.values()
    )


    print(
        "CANDIDATES:",
        len(candidates)
    )

    for video in candidates[:10]:

        print(
            " ",
            video["video_id"],
            "|",
            video["title"],
        )


    results.append(
        {
            "date":
                target_date.isoformat(),
            "status":
                "FOUND"
                if candidates
                else "NOT_FOUND",
            "query":
                query,
            "candidates":
                candidates,
        }
    )


OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT.write_text(
    json.dumps(
        {
            "start_date":
                START_DATE.isoformat(),
            "end_date":
                END_DATE.isoformat(),
            "results":
                results,
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)


found = sum(
    x["status"] == "FOUND"
    for x in results
)

failed = sum(
    x["status"] == "FAILED"
    for x in results
)

not_found = sum(
    x["status"] == "NOT_FOUND"
    for x in results
)


print()
print("=" * 100)
print("DISCOVERY RESULT")
print("=" * 100)
print("FOUND:", found)
print("NOT FOUND:", not_found)
print("FAILED:", failed)
print("TOTAL:", len(results))
print("OUTPUT:", OUTPUT)
print("=" * 100)
