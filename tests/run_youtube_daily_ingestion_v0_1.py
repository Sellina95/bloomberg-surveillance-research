from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


DATE = os.environ.get("SURVEILLANCE_DATE")
VIDEO_ID = os.environ.get("VIDEO_ID")

if not DATE:
    raise SystemExit("FAIL — SURVEILLANCE_DATE is not set")

if not VIDEO_ID:
    raise SystemExit("FAIL — VIDEO_ID is not set")

VIDEO_URL = f"https://www.youtube.com/watch?v={VIDEO_ID}"

API_KEY = os.environ.get("SUPADATA_API_KEY")

if not API_KEY:
    raise SystemExit("FAIL — SUPADATA_API_KEY is not set")

OUT = Path(
    f"data/raw/youtube/{DATE}"
)
OUT.mkdir(parents=True, exist_ok=True)

OUTPUT = OUT / "transcript.json"


def fetch_transcript() -> dict:
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

    with urlopen(request, timeout=120) as response:
        return json.loads(
            response.read().decode("utf-8")
        )


print("=" * 100)
print("YOUTUBE DAILY INGESTION RUNNER v0.1")
print("=" * 100)

print("DATE:", DATE)
print("VIDEO:", VIDEO_URL)
print()

print("STEP 1 — FETCH TRANSCRIPT")

data = fetch_transcript()

content = data.get("content", [])

if not content:
    raise SystemExit(
        "FAIL — transcript content is empty"
    )

OUTPUT.write_text(
    json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

print("TRANSCRIPT: PASS")
print("SEGMENTS:", len(content))
print("OUTPUT:", OUTPUT)

print()
print("=" * 100)
print("INGESTION RESULT")
print("=" * 100)
print("FULL TRANSCRIPT: PASS")
print("ARTIFACT SAVED: PASS")
print("=" * 100)
