from __future__ import annotations

import json
import subprocess
from pathlib import Path
from datetime import date, timedelta


BASE = Path("data/processed/surveillance")

START_DATE = date(2026, 8, 1)
END_DATE = date(2026, 8, 31)


def dates_between(start: date, end: date):
    current = start

    while current <= end:
        yield current.isoformat()
        current += timedelta(days=1)


results = []

print("=" * 100)
print("BLOOMBERG SURVEILLANCE RESEARCH BATCH v0.1")
print("=" * 100)
print(
    f"DATE RANGE: {START_DATE} -> {END_DATE}"
)
print("=" * 100)


for date_str in dates_between(
    START_DATE,
    END_DATE,
):

    day = BASE / date_str

    canonical = day / "youtube_canonical.json"
    guests = day / "guest_transcripts.json"

    print()
    print("-" * 100)
    print("DATE:", date_str)

    if not canonical.exists():
        print("STATUS: SKIP — canonical missing")

        results.append(
            {
                "date": date_str,
                "status": "SKIPPED",
                "reason": "canonical_missing",
            }
        )

        continue

    if not guests.exists():
        print(
            "STATUS: SKIP — guest transcripts missing"
        )

        results.append(
            {
                "date": date_str,
                "status": "SKIPPED",
                "reason":
                    "guest_transcripts_missing",
            }
        )

        continue

    print("CANONICAL: PASS")
    print("GUEST TRANSCRIPTS: PASS")

    results.append(
        {
            "date": date_str,
            "status": "READY",
        }
    )


print()
print("=" * 100)
print("BATCH INVENTORY")
print("=" * 100)

ready = sum(
    x["status"] == "READY"
    for x in results
)

skipped = sum(
    x["status"] == "SKIPPED"
    for x in results
)

print("READY:", ready)
print("SKIPPED:", skipped)
print("TOTAL DAYS:", len(results))

OUTPUT = (
    BASE
    / "batch_inventory_2026-08-01_to_2026-08-31.json"
)

OUTPUT.write_text(
    json.dumps(
        {
            "start_date":
                START_DATE.isoformat(),
            "end_date":
                END_DATE.isoformat(),
            "ready_days":
                ready,
            "skipped_days":
                skipped,
            "days":
                results,
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

print("OUTPUT:", OUTPUT)
print("=" * 100)
