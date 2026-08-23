from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


VIDEO_URL = "https://www.youtube.com/watch?v=qWYTenEUdFc"
API_KEY = os.environ["SUPADATA_API_KEY"]

url = (
    "https://api.supadata.ai/v1/youtube/video"
    "?url="
    + quote(VIDEO_URL, safe="")
)

request = Request(
    url,
    headers={
        "x-api-key": API_KEY,
        "Accept": "application/json",
    },
)

print("=" * 100)
print("SUPADATA CHAPTER PROBE")
print("=" * 100)

with urlopen(request, timeout=60) as response:
    data = json.loads(
        response.read().decode("utf-8")
    )

print("TOP LEVEL:", list(data.keys()))

chapters = data.get("chapters")

if chapters:
    print("CHAPTER COUNT:", len(chapters))

    for chapter in chapters:
        print(
            chapter
        )

    print()
    print("CHAPTER INGESTION: PASS")
else:
    print()
    print("CHAPTER INGESTION: NOT AVAILABLE")
    print()
    print("RAW RESPONSE:")
    print(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        )[:5000]
    )
