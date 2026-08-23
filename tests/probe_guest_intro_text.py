from __future__ import annotations

import json
from pathlib import Path


DATE = "2026-08-14"

PATH = (
    Path("data/processed/surveillance")
    / DATE
    / "segments.json"
)

INTRO_SEGMENTS = [4, 48, 55, 70]

payload = json.loads(
    PATH.read_text(encoding="utf-8")
)

segments = payload["segments"]


print("=" * 100)
print("GUEST INTRODUCTION TEXT")
print("=" * 100)
print("DATE:", DATE)
print("=" * 100)


for segment_id in INTRO_SEGMENTS:

    segment = segments[segment_id]

    print()
    print("-" * 100)

    print(
        f"SEGMENT: {segment_id}"
    )

    print(
        f"TIME: "
        f"{segment['start_seconds']:.1f}s"
    )

    print(
        f"SPEAKER: "
        f"{segment['speaker_index']}"
    )

    print()
    print(
        segment["text"]
    )


print()
print("=" * 100)
