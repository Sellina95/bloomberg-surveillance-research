from __future__ import annotations

import json
import os
import re
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DATE = "2026-08-10"
VIDEO_ID = "8j3SSyrHU2Y"

SERP_KEY = os.environ["SERPAPI_API_KEY"]

RAW = Path(f"data/raw/youtube/{DATE}")
OUT = Path(f"data/processed/surveillance/{DATE}")

RAW.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)


# ============================================================
# 1. SERPAPI — REAL YOUTUBE CHAPTERS
# ============================================================

params = {
    "engine": "youtube_video",
    "v": VIDEO_ID,
    "api_key": SERP_KEY,
}

url = (
    "https://serpapi.com/search.json?"
    + urlencode(params)
)

request = Request(
    url,
    headers={"Accept": "application/json"},
)

with urlopen(request, timeout=120) as response:
    serp = json.loads(
        response.read().decode("utf-8")
    )

chapters_raw = serp.get("chapters", [])

if not chapters_raw:
    raise SystemExit(
        "FAIL — no YouTube chapters returned"
    )

chapters = [
    {
        "chapter": i + 1,
        "title": c["title"],
        "start_seconds": c["time_start"],
        "source": "serpapi",
    }
    for i, c in enumerate(chapters_raw)
]


# ============================================================
# 2. SUPADATA — FULL TRANSCRIPT
# ============================================================

supadata_path = RAW / "transcript.json"

supadata = json.loads(
    supadata_path.read_text(
        encoding="utf-8"
    )
)

content = supadata.get("content", [])

if not content:
    raise SystemExit(
        "FAIL — empty Supadata transcript"
    )

segments = []

for i, item in enumerate(content):

    start = item["offset"] / 1000
    duration = item.get("duration", 0) / 1000

    segments.append(
        {
            "segment_id": i,
            "start_seconds": start,
            "end_seconds": start + duration,
            "duration_seconds": duration,
            "text": item["text"],
            "lang": item.get("lang"),
        }
    )


# ============================================================
# 3. CHAPTER ASSIGNMENT
# ============================================================

for i, chapter in enumerate(chapters):

    start = chapter["start_seconds"]

    end = (
        chapters[i + 1]["start_seconds"]
        if i + 1 < len(chapters)
        else max(
            s["end_seconds"]
            for s in segments
        )
    )

    for segment in segments:

        if (
            start
            <= segment["start_seconds"]
            < end
        ):
            segment["chapter"] = chapter["chapter"]


# ============================================================
# 4. AUTOMATIC GUEST CHAPTER CLASSIFICATION
# ============================================================

# Guest chapter titles in Bloomberg's YouTube structure
# normally use:
#
#   "Editorial headline — Person, Organization"
#
# We infer Guest ONLY from the chapter title structure.
# No fixed guest count.

GUEST_RE = re.compile(
    r"^.+\s+[—-]\s+"
    r"[A-Z][A-Za-z.'-]+"
    r"(?:\s+[A-Z][A-Za-z.'-]+)+"
)


def is_guest_chapter(title: str) -> bool:

    title = title.strip()

    return bool(
        GUEST_RE.match(title)
    )


guest_chapters = []

for chapter in chapters:

    guest = is_guest_chapter(
        chapter["title"]
    )

    chapter["is_guest"] = guest

    if guest:
        guest_chapters.append(
            chapter
        )


# ============================================================
# 5. BUILD GUEST UNITS
# ============================================================

units = []

for unit_id, chapter in enumerate(
    guest_chapters,
    start=1,
):

    index = chapters.index(
        chapter
    )

    start = chapter["start_seconds"]

    end = (
        chapters[index + 1]["start_seconds"]
        if index + 1 < len(chapters)
        else max(
            s["end_seconds"]
            for s in segments
        )
    )

    rows = [
        s
        for s in segments
        if (
            start
            <= s["start_seconds"]
            < end
        )
    ]

    units.append(
        {
            "unit_id": unit_id,
            "chapter": chapter["chapter"],
            "title": chapter["title"],
            "start_seconds": start,
            "end_seconds": end,
            "duration_seconds": end - start,
            "segment_count": len(rows),
        }
    )


# ============================================================
# 6. SAVE CANONICAL
# ============================================================

canonical = {
    "date": DATE,
    "video_id": VIDEO_ID,
    "sources": {
        "chapters": "serpapi",
        "transcript": "supadata",
    },
    "chapter_count": len(chapters),
    "transcript_segment_count": len(segments),
    "chapters": chapters,
    "segments": segments,
}

canonical_path = (
    OUT / "youtube_canonical.json"
)

canonical_path.write_text(
    json.dumps(
        canonical,
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)


# ============================================================
# 7. SAVE GUEST UNITS
# ============================================================

units_path = (
    OUT / "guest_units.json"
)

units_path.write_text(
    json.dumps(
        {
            "date": DATE,
            "video_id": VIDEO_ID,
            "guest_count": len(units),
            "guest_units": units,
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)


# ============================================================
# RESULT
# ============================================================

coverage = (
    max(s["end_seconds"] for s in segments)
    - min(s["start_seconds"] for s in segments)
) / 60

unassigned = sum(
    1
    for s in segments
    if "chapter" not in s
)

print("=" * 100)
print("CROSS-DAY YOUTUBE PIPELINE")
print("=" * 100)

print("DATE:", DATE)
print("CHAPTERS:", len(chapters))
print("TRANSCRIPT SEGMENTS:", len(segments))
print(f"COVERAGE: {coverage:.1f} minutes")
print("UNASSIGNED:", unassigned)
print("GUEST COUNT:", len(units))

print()
print("-" * 100)
print("GUEST UNITS")
print("-" * 100)

for unit in units:
    print(
        f"UNIT {unit['unit_id']:02d} | "
        f"CHAPTER {unit['chapter']:02d} | "
        f"{unit['title']}"
    )

print()
print("=" * 100)

if (
    len(chapters) > 0
    and len(segments) > 0
    and coverage > 120
    and unassigned == 0
    and len(units) > 0
):
    print("CROSS-DAY PIPELINE: PASS")
else:
    print("CROSS-DAY PIPELINE: REVIEW")

print("=" * 100)

print("CANONICAL:", canonical_path)
print("GUEST UNITS:", units_path)
