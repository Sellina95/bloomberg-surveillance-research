from __future__ import annotations

import json
from pathlib import Path


DATE = "2026-08-14"

BASE = Path(
    f"data/processed/surveillance/{DATE}"
)

UNITS = BASE / "guest_units_v0_3.json"
CANONICAL = BASE / "youtube_canonical_v0_2.json"


units_data = json.loads(
    UNITS.read_text(encoding="utf-8")
)

canonical = json.loads(
    CANONICAL.read_text(encoding="utf-8")
)

units = units_data["guest_units"]
chapters = canonical["chapters"]
segments = canonical["segments"]


# ============================================================
# AUDIT
# ============================================================

print("=" * 100)
print("GUEST UNIT AUDIT v0.3")
print("=" * 100)

print(
    "TOTAL CHAPTERS:",
    len(chapters),
)

print(
    "GUEST UNITS:",
    len(units),
)

print()

errors = []

for unit in units:

    chapter_no = unit["chapter"]

    chapter = next(
        c
        for c in chapters
        if c["chapter"] == chapter_no
    )

    expected_start = chapter["start_seconds"]

    # Find next actual chapter
    following = [
        c
        for c in chapters
        if c["start_seconds"] > expected_start
    ]

    expected_end = (
        min(
            c["start_seconds"]
            for c in following
        )
        if following
        else max(
            s["end_seconds"]
            for s in segments
        )
    )

    start_diff = (
        unit["start_seconds"]
        - expected_start
    )

    end_diff = (
        unit["end_seconds"]
        - expected_end
    )

    start_pass = abs(start_diff) < 0.001
    end_pass = abs(end_diff) < 0.001

    status = (
        "PASS"
        if start_pass and end_pass
        else "FAIL"
    )

    if status == "FAIL":
        errors.append(unit["unit_id"])

    print(
        f"{status} | "
        f"UNIT {unit['unit_id']:02d} | "
        f"CHAPTER {chapter_no:02d} | "
        f"{unit['guest']}"
    )

    print(
        f"       START "
        f"{unit['start_seconds']:.2f}s "
        f"vs "
        f"{expected_start:.2f}s "
        f"Δ={start_diff:+.2f}s"
    )

    print(
        f"       END   "
        f"{unit['end_seconds']:.2f}s "
        f"vs "
        f"{expected_end:.2f}s "
        f"Δ={end_diff:+.2f}s"
    )


print()
print("=" * 100)
print("RESULT")
print("=" * 100)

print(
    f"PASS: "
    f"{len(units) - len(errors)}/{len(units)}"
)

print(
    f"FAIL: {len(errors)}"
)

if not errors:
    print(
        "GUEST UNIT STRUCTURAL AUDIT: PASS"
    )
else:
    print(
        "GUEST UNIT STRUCTURAL AUDIT: FAIL"
    )

print("=" * 100)
