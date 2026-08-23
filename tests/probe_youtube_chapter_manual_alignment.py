from __future__ import annotations

import json
from pathlib import Path


DATE = "2026-08-14"

TRANSCRIPT_PATH = (
    Path("data/processed/surveillance")
    / DATE
    / "segments.json"
)


CHAPTERS = [
    (
        "32:16",
        "Fast-Food Prices Are Driving Diners Elsewhere — Nick Setyan, Mizuho",
    ),
    (
        "42:00",
        "AI Debt Could Crowd Out the US Treasury — James Athey, Marlborough Investment Management",
    ),
    (
        "52:12",
        "AI Is Driving Wider Growth — Binky Chadha, Deutsche Bank",
    ),
    (
        "1:06:28",
        "Treasury Leans on T-Bills as Deficit Risks Mount — Jeannette Lowe, Baird Strategies",
    ),
]


def timestamp_to_seconds(value: str) -> float:
    parts = value.split(":")

    if len(parts) == 2:
        minutes, seconds = parts
        return int(minutes) * 60 + float(seconds)

    if len(parts) == 3:
        hours, minutes, seconds = parts
        return (
            int(hours) * 3600
            + int(minutes) * 60
            + float(seconds)
        )

    raise ValueError(f"Invalid timestamp: {value}")


payload = json.loads(
    TRANSCRIPT_PATH.read_text(
        encoding="utf-8"
    )
)

segments = payload["segments"]


print("=" * 100)
print("YOUTUBE CHAPTER → OMNY TRANSCRIPT ALIGNMENT")
print("=" * 100)
print("DATE:", DATE)
print("TRANSCRIPT SEGMENTS:", len(segments))
print("CHAPTERS:", len(CHAPTERS))
print("=" * 100)


for timestamp, title in CHAPTERS:

    chapter_seconds = timestamp_to_seconds(
        timestamp
    )

    nearest = min(
        segments,
        key=lambda segment: abs(
            segment["start_seconds"]
            - chapter_seconds
        ),
    )

    difference = abs(
        nearest["start_seconds"]
        - chapter_seconds
    )

    print()
    print("-" * 100)

    print("YOUTUBE CHAPTER")
    print("TIME:", timestamp)
    print("TITLE:", title)

    print()
    print("NEAREST OMNY SEGMENT")
    print(
        "SEGMENT:",
        nearest["segment_id"],
    )

    print(
        "TIME:",
        f"{nearest['start_seconds']:.2f}s",
    )

    print(
        "DIFFERENCE:",
        f"{difference:.2f}s",
    )

    print(
        "SPEAKER INDEX:",
        nearest["speaker_index"],
    )

    print()
    print("TRANSCRIPT:")
    print(nearest["text"][:500])


print()
print("=" * 100)
print("ALIGNMENT COMPLETE")
print("=" * 100)
