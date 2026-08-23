from __future__ import annotations

import json
from pathlib import Path


BASE = Path(
    "data/processed/surveillance/2026-08-14"
)

UNITS = BASE / "guest_units_v0_2.json"
CHAPTERS = BASE / "youtube_transcript.json"


units = json.loads(
    UNITS.read_text(encoding="utf-8")
)["guest_units"]

chapters = [
    x
    for x in json.loads(
        CHAPTERS.read_text(encoding="utf-8")
    )["chapters"]
    if x.get("guest")
]


print("=" * 100)
print("GUEST UNIT AUDIT v0.2")
print("=" * 100)

print(
    f"UNITS: {len(units)}"
)

print(
    f"GROUND TRUTH CHAPTERS: {len(chapters)}"
)

print()

for unit, chapter in zip(units, chapters):

    chapter_start = chapter["start_seconds"]

    diff = (
        unit["start_seconds"]
        - chapter_start
    )

    print(
        f"UNIT {unit['unit_id']:02d} | "
        f"{unit['guest']} | "
        f"UNIT START={unit['start_seconds']:.2f}s | "
        f"CHAPTER={chapter_start:.2f}s | "
        f"Δ={diff:+.2f}s | "
        f"END={unit['end_seconds']:.2f}s"
    )


print()
print("=" * 100)

if len(units) == len(chapters):
    print("STRUCTURAL AUDIT: PASS")
else:
    print("STRUCTURAL AUDIT: FAIL")

print("=" * 100)
