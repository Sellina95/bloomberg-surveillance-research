from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

VIDEO_ID = "qWYTenEUdFc"
API_KEY = os.environ["SERPAPI_API_KEY"]

params = {
    "engine": "youtube_video",
    "v": VIDEO_ID,
    "api_key": API_KEY,
}

url = "https://serpapi.com/search.json?" + urlencode(params)

request = Request(
    url,
    headers={"Accept": "application/json"},
)

with urlopen(request, timeout=120) as response:
    data = json.loads(
        response.read().decode("utf-8")
    )

output = Path(
    "data/raw/youtube_probe/serpapi_2026-08-14.json"
)

output.parent.mkdir(
    parents=True,
    exist_ok=True,
)

output.write_text(
    json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

chapters = data.get("chapters", [])
transcript = data.get("transcript")

print("=" * 100)
print("SERPAPI YOUTUBE PROBE")
print("=" * 100)

print("CHAPTER COUNT:", len(chapters))
print(
    "TRANSCRIPT TYPE:",
    type(transcript).__name__,
)

if isinstance(transcript, dict):
    print(
        "TRANSCRIPT KEYS:",
        list(transcript.keys()),
    )

    for key, value in transcript.items():

        if isinstance(value, list):
            print(
                f"{key}: LIST[{len(value)}]"
            )

        elif isinstance(value, str):
            print(
                f"{key}: STRING[{len(value)}]"
            )

        else:
            print(
                f"{key}: {type(value).__name__}"
            )

elif isinstance(transcript, list):

    print(
        "TRANSCRIPT COUNT:",
        len(transcript),
    )

else:

    print("TRANSCRIPT: NOT FOUND")

print()
print("OUTPUT:", output)

print()
print("=" * 100)

if chapters:
    print("CHAPTER INGESTION: PASS")
else:
    print("CHAPTER INGESTION: FAIL")

if transcript:
    print("TRANSCRIPT INGESTION: PASS")
else:
    print("TRANSCRIPT INGESTION: FAIL")

print("=" * 100)
