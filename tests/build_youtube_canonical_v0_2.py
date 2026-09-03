from __future__ import annotations
import os

import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DATE = os.environ.get("SURVEILLANCE_DATE")

VIDEO_ID = os.environ.get("VIDEO_ID")

if not DATE:
    raise SystemExit(
        "FAIL — SURVEILLANCE_DATE is not set"
    )

if not VIDEO_ID:
    raise SystemExit(
        "FAIL — VIDEO_ID is not set"
    )

SERPAPI_API_KEY = os.environ.get(
    "SERPAPI_API_KEY"
)

if not SERPAPI_API_KEY:
    raise SystemExit(
        "FAIL — SERPAPI_API_KEY is not set"
    )

BASE_RAW = Path(
    f"data/raw/youtube/{DATE}"
)

BASE_PROCESSED = Path(
    f"data/processed/surveillance/{DATE}"
)

SUPADATA = (
    BASE_RAW / "transcript.json"
)

SERPAPI = (
    BASE_RAW / "serpapi_video.json"
)

OUTPUT = (
    BASE_PROCESSED
    / "youtube_canonical_v0_2.json"
)


# ============================================================
# 0. CURRENT VIDEO METADATA — SerpApi
#
# IMPORTANT:
# Never use a historical probe artifact here.
# Query the exact VIDEO_ID being processed.
# ============================================================

params = {
    "engine": "youtube_video",
    "v": VIDEO_ID,
    "api_key": SERPAPI_API_KEY,
}

url = (
    "https://serpapi.com/search.json?"
    + urlencode(params)
)

request = Request(
    url,
    headers={
        "User-Agent": "Mozilla/5.0",
    },
)

with urlopen(
    request,
    timeout=60,
) as response:

    serp = json.loads(
        response.read().decode("utf-8")
    )


# Persist the exact metadata used by this run.
BASE_RAW.mkdir(
    parents=True,
    exist_ok=True,
)

SERPAPI.write_text(
    json.dumps(
        serp,
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)


# ============================================================
# 0.1 CURRENT TRANSCRIPT — Supadata
# ============================================================

if not SUPADATA.exists():
    raise SystemExit(
        f"FAIL — transcript artifact not found: "
        f"{SUPADATA}"
    )

supadata = json.loads(
    SUPADATA.read_text(
        encoding="utf-8"
    )
)


# ============================================================
# 1. CHAPTERS — SerpApi
# ============================================================

chapters_raw = serp.get("chapters", [])

chapters = []
chapter_mode = "source_chapters"

if chapters_raw:

    for i, chapter in enumerate(chapters_raw, start=1):

        chapters.append(
            {
                "chapter": i,
                "title": chapter.get("title"),
                "start_seconds": (
                    chapter["time_start"]
                ),
                "source": "serpapi",
            }
        )

else:

    # Some official Bloomberg program uploads do not expose
    # YouTube chapters. Preserve timestamp grounding without
    # inventing guest boundaries or speaker attribution.
    chapter_mode = "full_program_fallback"
    chapters.append(
        {
            "chapter": 1,
            "title": (
                "Full program (speaker attribution unavailable)"
            ),
            "start_seconds": 0.0,
            "source": "full_program_fallback",
        }
    )


# ============================================================
# 2. TRANSCRIPT — Supadata
# ============================================================

content = supadata.get("content", [])

if not content:
    raise SystemExit(
        "FAIL — no transcript from Supadata"
    )

segments = []

for i, item in enumerate(content):

    offset_ms = item["offset"]
    duration_ms = item.get(
        "duration",
        0,
    )

    start = offset_ms / 1000
    duration = duration_ms / 1000

    segments.append(
        {
            "segment_id": i,
            "start_seconds": start,
            "end_seconds": start + duration,
            "duration_seconds": duration,
            "text": item["text"],
            "lang": item.get("lang"),
            "source": "supadata",
        }
    )


# ============================================================
# 3. ASSIGN EACH TRANSCRIPT SEGMENT TO A CHAPTER
#
# Chapter metadata is NOT inferred.
# It comes directly from SerpApi.
# ============================================================

for i, chapter in enumerate(chapters):

    start = chapter["start_seconds"]

    end = (
        chapters[i + 1]["start_seconds"]
        if i + 1 < len(chapters)
        else None
    )

    for segment in segments:

        t = segment["start_seconds"]

        if t < start:
            continue

        if end is not None and t >= end:
            continue

        segment["chapter"] = chapter["chapter"]
        segment["chapter_title"] = chapter["title"]


# ============================================================
# 4. VALIDATION
# ============================================================

unassigned = [
    s
    for s in segments
    if "chapter" not in s
]

# Transcript may legitimately contain material before
# Chapter 1, so this is informational rather than failure.

coverage_start = min(
    s["start_seconds"]
    for s in segments
)

coverage_end = max(
    s["end_seconds"]
    for s in segments
)

coverage_minutes = (
    coverage_end - coverage_start
) / 60

if coverage_minutes < 15:
    raise SystemExit(
        "FAIL — transcript coverage below 15 minutes"
    )


# ============================================================
# 5. SAVE CANONICAL DATASET
# ============================================================

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

artifact = {
    "date": DATE,
    "sources": {
        "chapters": (
            "SerpApi"
            if chapter_mode == "source_chapters"
            else "full_program_fallback"
        ),
        "transcript": "Supadata",
    },
    "chapter_mode": chapter_mode,
    "chapter_count": len(chapters),
    "transcript_segment_count": len(segments),
    "transcript_coverage_minutes":
        coverage_minutes,
    "unassigned_segments":
        len(unassigned),
    "chapters": chapters,
    "segments": segments,
}

OUTPUT.write_text(
    json.dumps(
        artifact,
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)


# ============================================================
# RESULT
# ============================================================

print("=" * 100)
print("YOUTUBE CANONICAL BUILD v0.2")
print("=" * 100)

print(
    "CHAPTERS:",
    len(chapters),
)

print(
    "TRANSCRIPT SEGMENTS:",
    len(segments),
)

print(
    "TRANSCRIPT COVERAGE:",
    f"{coverage_minutes:.1f} minutes",
)

print(
    "UNASSIGNED SEGMENTS:",
    len(unassigned),
)

print(
    "OUTPUT:",
    OUTPUT,
)

print()
print("=" * 100)

if len(chapters) > 0 and len(segments) > 0:
    print("CANONICAL BUILD: PASS")
else:
    print("CANONICAL BUILD: REVIEW")

print("=" * 100)
