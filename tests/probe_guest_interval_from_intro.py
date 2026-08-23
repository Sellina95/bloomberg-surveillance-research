from __future__ import annotations

import json
from pathlib import Path


DATE = "2026-08-14"

PATH = (
    Path("data/processed/surveillance")
    / DATE
    / "segments.json"
)

START_SEGMENT = 55
END_SEGMENT = 69


payload = json.loads(
    PATH.read_text(encoding="utf-8")
)

segments = payload["segments"]


print("=" * 100)
print("GUEST INTERVAL INSPECTION")
print("=" * 100)
print("DATE:", DATE)
print(
    f"SEGMENTS: {START_SEGMENT} → {END_SEGMENT}"
)
print("=" * 100)


for segment in segments[
    START_SEGMENT : END_SEGMENT + 1
]:

    print()
    print("-" * 100)

    print(
        f"SEGMENT {segment['segment_id']:3d} | "
        f"{segment['start_seconds']:7.1f}s | "
        f"SPEAKER {segment['speaker_index']:2d} | "
        f"{segment['word_count']:3d} words"
    )

    print(segment["text"])


print()
print("=" * 100)
print("INSPECTION COMPLETE")
print("=" * 100)
