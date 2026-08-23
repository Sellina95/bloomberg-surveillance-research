from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


DATE = "2026-08-10"
VIDEO_URL = "https://www.youtube.com/watch?v=8j3SSyrHU2Y"

API_KEY = os.environ.get("SUPADATA_API_KEY")

if not API_KEY:
    raise SystemExit("FAIL — SUPADATA_API_KEY is not set")


OUT = Path(f"data/raw/youtube/{DATE}")
OUT.mkdir(parents=True, exist_ok=True)

OUTPUT = OUT / "transcript.json"


url = (
    "https://api.supadata.ai/v1/youtube/transcript"
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
print("CROSS-DAY YOUTUBE INGESTION")
print("=" * 100)
print("DATE:", DATE)
print("VIDEO:", VIDEO_URL)
print()

with urlopen(request, timeout=120) as response:
    data = json.loads(
        response.read().decode("utf-8")
    )

content = data.get("content", [])

if not content:
    raise SystemExit(
        "FAIL — empty transcript"
    )

OUTPUT.write_text(
    json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

first = content[0]["offset"] / 1000

last = max(
    (
        x["offset"]
        + x.get("duration", 0)
    )
    for x in content
) / 1000

print("TRANSCRIPT: PASS")
print("SEGMENTS:", len(content))
print(
    "COVERAGE:",
    f"{last / 60:.1f} minutes"
)
print("OUTPUT:", OUTPUT)

print()
print("=" * 100)

if last >= 60 * 60:
    print("FULL-LENGTH COVERAGE: PASS")
else:
    print("FULL-LENGTH COVERAGE: REVIEW")

print("=" * 100)
