from __future__ import annotations
import os

import json
from pathlib import Path


DATE = os.environ.get("SURVEILLANCE_DATE", "2026-08-14")

SERPAPI = Path(
    "data/raw/youtube_probe/serpapi_2026-08-14.json"
)

SUPADATA = Path(
    "data/raw/youtube_probe/supadata_2026-08-14.json"
)

OUTPUT = Path(
    f"data/processed/surveillance/{DATE}/"
    "youtube_canonical_v0_2.json"
)


serp = json.loads(
    SERPAPI.read_text(encoding="utf-8")
)

supadata = json.loads(
    SUPADATA.read_text(encoding="utf-8")
)


# ============================================================
# 1. CHAPTERS — SerpApi
# ============================================================

chapters_raw = serp.get("chapters", [])

if not chapters_raw:
    raise SystemExit(
        "FAIL — no chapters from SerpApi"
    )

chapters = []

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
        "chapters": "SerpApi",
        "transcript": "Supadata",
    },
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

if (
    len(chapters) > 0
    and len(segments) > 0
    and coverage_minutes > 120
):
    print("CANONICAL BUILD: PASS")
else:
    print("CANONICAL BUILD: REVIEW")

print("=" * 100)
