from __future__ import annotations

import json
from pathlib import Path


BASE = Path(
    "data/processed/surveillance/2026-08-14"
)

DETECTION = BASE / "guest_detection_v0_1.json"
TRANSCRIPT = BASE / "youtube_transcript.json"

detection = json.loads(
    DETECTION.read_text(encoding="utf-8")
)

transcript = json.loads(
    TRANSCRIPT.read_text(encoding="utf-8")
)

segments = transcript["segments"]

print("=" * 100)
print("GUEST DETECTION v0.1 — MISS AUDIT")
print("=" * 100)

misses = [
    row
    for row in detection["matches"]
    if row["detected_start"] is None
]

print("MISSES:", len(misses))

for row in misses:

    chapter = row["chapter"]
    guest = row["guest"]
    start = row["chapter_start"]

    print()
    print("-" * 100)
    print(
        f"CHAPTER {chapter:02d} | "
        f"GUEST: {guest}"
    )
    print(
        f"CHAPTER START: {start:.2f}s"
    )

    # Show transcript around chapter start.
    nearby = [
        s
        for s in segments
        if start - 180
        <= s["start_seconds"]
        <= start + 180
    ]

    print()
    print("TRANSCRIPT AROUND CHAPTER:")

    for s in nearby:

        text = (
            s["text"]
            .replace("\n", " ")
            .strip()
        )

        print(
            f"{s['start_seconds']:8.2f}s | "
            f"{text[:600]}"
        )

print()
print("=" * 100)
print("MISS AUDIT COMPLETE")
print("=" * 100)
