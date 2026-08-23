from __future__ import annotations

import json
from pathlib import Path


PATH = Path(
    "data/processed/surveillance/2026-08-14/youtube_transcript.json"
)

TARGET_CHAPTERS = [12, 13, 14]

data = json.loads(
    PATH.read_text(encoding="utf-8")
)

segments = data["segments"]


print("=" * 100)
print("CANONICAL GUEST BOUNDARY PROBE")
print("=" * 100)


for chapter in TARGET_CHAPTERS:

    rows = [
        x
        for x in segments
        if x.get("chapter") == chapter
    ]

    print()
    print("=" * 100)
    print(
        f"CHAPTER {chapter:02d}"
    )
    print(
        f"GUEST: {rows[0].get('chapter_guest')}"
        if rows
        else "GUEST: UNKNOWN"
    )
    print(
        f"SEGMENTS: {len(rows)}"
    )
    print("=" * 100)

    # First 8
    print()
    print("----- FIRST 8 -----")

    for row in rows[:8]:

        print(
            f"{row['start_seconds']:8.2f}s | "
            f"{row['text'].replace(chr(10), ' ')[:700]}"
        )

    # Last 8
    print()
    print("----- LAST 8 -----")

    for row in rows[-8:]:

        print(
            f"{row['start_seconds']:8.2f}s | "
            f"{row['text'].replace(chr(10), ' ')[:700]}"
        )


print()
print("=" * 100)
print("DONE")
print("=" * 100)
