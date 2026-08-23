from __future__ import annotations

import json
import re
from pathlib import Path


PATH = Path(
    "data/processed/surveillance/2026-08-14/youtube_transcript.json"
)

START_PATTERNS = [
    "joins us now",
    "joins us",
    "joining us",
]

END_PATTERNS = [
    "thank you so much",
    "thank you for joining us",
    "thanks for having me",
    "thank you for being here",
    "stay with us",
    "coming up next",
]


data = json.loads(PATH.read_text(encoding="utf-8"))
segments = data["segments"]


def hits(text: str, patterns: list[str]) -> list[str]:
    text = text.lower()
    return [
        p for p in patterns
        if p in text
    ]


print("=" * 100)
print("GUEST DETECTION v0.1")
print("=" * 100)

guest_chapters = [
    c for c in data["chapters"]
    if c.get("guest")
]

print(
    f"GUEST CHAPTERS: {len(guest_chapters)}"
)

for chapter in guest_chapters:

    rows = [
        s for s in segments
        if s.get("chapter") == chapter["chapter"]
    ]

    start_hits = []
    end_hits = []

    for row in rows:

        start = hits(
            row["text"],
            START_PATTERNS,
        )

        end = hits(
            row["text"],
            END_PATTERNS,
        )

        if start:
            start_hits.append((row, start))

        if end:
            end_hits.append((row, end))

    print()
    print("-" * 100)

    print(
        f"CHAPTER {chapter['chapter']:02d}"
    )

    print(
        f"GUEST: {chapter['guest']}"
    )

    print(
        f"CHAPTER START: "
        f"{chapter['start_seconds']}s"
    )

    print(
        f"SEGMENTS: {len(rows)}"
    )

    print()
    print("START SIGNALS:")

    if start_hits:
        for row, found in start_hits[:5]:
            print(
                f"  {row['start_seconds']:8.2f}s | "
                f"{found} | "
                f"{row['text'][:400]}"
            )
    else:
        print("  NONE")

    print()
    print("END SIGNALS:")

    if end_hits:
        for row, found in end_hits[-5:]:
            print(
                f"  {row['start_seconds']:8.2f}s | "
                f"{found} | "
                f"{row['text'][:400]}"
            )
    else:
        print("  NONE")


print()
print("=" * 100)
print("GROUND-TRUTH COMPARISON")
print("=" * 100)

print(
    "YouTube Chapter metadata = reference ground truth"
)

print(
    "Transcript signals = detection candidates"
)

print()
print("=" * 100)
print("DONE")
print("=" * 100)
