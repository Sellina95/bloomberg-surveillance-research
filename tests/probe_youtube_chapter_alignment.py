from __future__ import annotations

import json
import subprocess
from pathlib import Path


# ============================================================
# PUT THE BLOOMBERG SURVEILLANCE YOUTUBE URL HERE
# ============================================================

VIDEO_URL = "https://www.youtube.com/watch?v=qWYTenEUdFc"

DATE = "2026-08-14"

TRANSCRIPT_PATH = (
    Path("data/processed/surveillance")
    / DATE
    / "segments.json"
)

MAX_MATCH_DISTANCE = 15.0


# ============================================================
# Load YouTube metadata
# ============================================================

def load_youtube_metadata(url: str) -> dict:

    if url == "PASTE_YOUTUBE_URL_HERE":
        raise SystemExit(
            "ERROR: Replace VIDEO_URL with the YouTube URL."
        )

    result = subprocess.run(
        [
            "yt-dlp",
            "--dump-single-json",
            "--skip-download",
            url,
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    return json.loads(result.stdout)


# ============================================================
# Load transcript
# ============================================================

payload = json.loads(
    TRANSCRIPT_PATH.read_text(
        encoding="utf-8"
    )
)

segments = payload["segments"]


# ============================================================
# YouTube
# ============================================================

metadata = load_youtube_metadata(
    VIDEO_URL
)

chapters = metadata.get(
    "chapters",
    [],
)


print("=" * 100)
print("YOUTUBE CHAPTER → OMNY TRANSCRIPT ALIGNMENT")
print("=" * 100)

print(
    "VIDEO:",
    metadata.get("title"),
)

print(
    "DATE:",
    DATE,
)

print(
    "YOUTUBE CHAPTERS:",
    len(chapters),
)

print(
    "TRANSCRIPT SEGMENTS:",
    len(segments),
)

print("=" * 100)


if not chapters:
    print()
    print(
        "NO YOUTUBE CHAPTERS FOUND."
    )
    print()
    print(
        "This means the video metadata does not expose "
        "publisher chapter timestamps through yt-dlp."
    )
    raise SystemExit(0)


# ============================================================
# Match each chapter to nearest transcript segment
# ============================================================

matches = []

for chapter in chapters:

    chapter_start = float(
        chapter["start_time"]
    )

    title = chapter.get(
        "title",
        "",
    )

    nearest = min(
        segments,
        key=lambda segment: abs(
            segment["start_seconds"]
            - chapter_start
        ),
    )

    distance = abs(
        nearest["start_seconds"]
        - chapter_start
    )

    matches.append(
        {
            "chapter_start": chapter_start,
            "chapter_title": title,
            "segment_id": nearest["segment_id"],
            "segment_start": nearest["start_seconds"],
            "distance": distance,
            "speaker_index": nearest[
                "speaker_index"
            ],
            "transcript_text": nearest[
                "text"
            ],
        }
    )


# ============================================================
# Report
# ============================================================

for item in matches:

    status = (
        "PASS"
        if item["distance"]
        <= MAX_MATCH_DISTANCE
        else "REVIEW"
    )

    minutes = int(
        item["chapter_start"] // 60
    )

    seconds = int(
        item["chapter_start"] % 60
    )

    print()
    print("-" * 100)

    print(
        f"{status} | "
        f"YouTube {minutes:02d}:{seconds:02d}"
    )

    print(
        "CHAPTER:",
        item["chapter_title"],
    )

    print(
        "TRANSCRIPT SEGMENT:",
        item["segment_id"],
    )

    print(
        "TRANSCRIPT TIME:",
        f"{item['segment_start']:.2f}s",
    )

    print(
        "TIME DIFFERENCE:",
        f"{item['distance']:.2f}s",
    )

    print(
        "SPEAKER:",
        item["speaker_index"],
    )

    print()
    print(
        "TRANSCRIPT:"
    )

    print(
        item["transcript_text"][:500]
    )


# ============================================================
# Summary
# ============================================================

passed = sum(
    1
    for item in matches
    if item["distance"]
    <= MAX_MATCH_DISTANCE
)

review = len(matches) - passed


print()
print("=" * 100)
print("SUMMARY")
print("=" * 100)

print(
    "TOTAL CHAPTERS:",
    len(matches),
)

print(
    "MATCH PASS:",
    passed,
)

print(
    "REVIEW:",
    review,
)

if matches:
    print(
        "PASS RATE:",
        f"{passed / len(matches) * 100:.1f}%",
    )

print()
print(
    "MAX MATCH DISTANCE:",
    f"{MAX_MATCH_DISTANCE:.1f}s",
)

print("=" * 100)
