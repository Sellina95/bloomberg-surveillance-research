from __future__ import annotations

import json
from pathlib import Path
from collections import Counter


DATES = [
    "2026-08-10",
    "2026-08-14",
]


for date in DATES:

    path = Path(
        f"data/processed/surveillance/{date}/"
        "guest_transcripts.json"
    )

    data = json.loads(
        path.read_text(encoding="utf-8")
    )

    print("=" * 100)
    print("SPEAKER PATTERN PROBE:", date)
    print("=" * 100)

    for unit in data["units"]:

        print()
        print(
            f"UNIT {unit['unit_id']:02d} | "
            f"{unit['title']}"
        )

        print(
            "SEGMENTS:",
            unit["transcript_segment_count"]
        )

        print("-" * 100)

        # Show only the first 12 transcript segments.
        for segment in unit["transcript_segments"][:12]:

            print(
                f"{segment['start_seconds']:8.2f}s | "
                f"{segment['text']}"
            )

print()
print("=" * 100)
print("DONE")
print("=" * 100)
