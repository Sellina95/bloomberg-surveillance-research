from __future__ import annotations

import json
import os
from pathlib import Path


DATE = os.environ.get("SURVEILLANCE_DATE")

if not DATE:
    raise SystemExit(
        "FAIL — SURVEILLANCE_DATE is not set"
    )

DATES = [DATE]


for date in DATES:

    base = Path(
        f"data/processed/surveillance/{date}"
    )

    canonical_path = (
        base / "youtube_canonical_v0_2.json"
    )

    guest_path = (
        base / "guest_units_v0_3.json"
    )

    output_path = (
        base / "guest_transcripts.json"
    )

    canonical = json.loads(
        canonical_path.read_text(
            encoding="utf-8"
        )
    )

    guest_data = json.loads(
        guest_path.read_text(
            encoding="utf-8"
        )
    )

    segments = canonical["segments"]

    output_units = []

    for unit in guest_data["guest_units"]:

        start = unit["start_seconds"]
        end = unit["end_seconds"]

        rows = [
            segment
            for segment in segments
            if (
                start
                <= segment["start_seconds"]
                < end
            )
        ]

        output_units.append(
            {
                **unit,
                "transcript_segment_count":
                    len(rows),

                "transcript_segments":
                    rows,

                "transcript_text":
                    " ".join(
                        row["text"]
                        for row in rows
                    ),
            }
        )

    artifact = {
        "date": date,
        "guest_count":
            len(output_units),
        "units":
            output_units,
    }

    output_path.write_text(
        json.dumps(
            artifact,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("=" * 100)
    print(
        "GUEST TRANSCRIPT BUILD",
        date,
    )
    print("=" * 100)

    print(
        "GUEST UNITS:",
        len(output_units),
    )

    for unit in output_units:

        print(
            f"UNIT {unit['unit_id']:02d} | "
            f"{unit['guest'] if 'guest' in unit else unit['title']} | "
            f"SEGMENTS="
            f"{unit['transcript_segment_count']}"
        )

    print(
        "OUTPUT:",
        output_path,
    )

print()
print("=" * 100)
print("BUILD COMPLETE")
print("=" * 100)
