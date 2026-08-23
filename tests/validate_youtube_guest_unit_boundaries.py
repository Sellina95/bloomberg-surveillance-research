from __future__ import annotations

import json
import re
from pathlib import Path


TRANSCRIPT = Path(
    "data/reference/youtube/2026-08-14_transcript.txt"
)

UNITS = Path(
    "data/processed/surveillance/2026-08-14/youtube_guest_units.json"
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
]


def to_seconds(value: str) -> int:
    parts = [int(x) for x in value.split(":")]

    if len(parts) == 2:
        return parts[0] * 60 + parts[1]

    return (
        parts[0] * 3600
        + parts[1] * 60
        + parts[2]
    )


timestamp_re = re.compile(
    r"^\d{1,2}:\d{2}(?::\d{2})?$"
)


lines = [
    x.strip()
    for x in TRANSCRIPT.read_text(
        encoding="utf-8"
    ).splitlines()
    if x.strip()
]


rows = []

for i, line in enumerate(lines):

    if not timestamp_re.match(line):
        continue

    try:
        seconds = to_seconds(line)
    except ValueError:
        continue

    text = " ".join(
        lines[i + 1:i + 4]
    )

    rows.append(
        {
            "seconds": seconds,
            "text": text,
        }
    )


units = json.loads(
    UNITS.read_text(
        encoding="utf-8"
    )
)["guest_units"]


print("=" * 100)
print("YOUTUBE GUEST UNIT BOUNDARY VALIDATION")
print("=" * 100)

passed = 0


for unit in units:

    start = unit["start_seconds"]
    end = unit["end_seconds"]

    candidates = [
        row
        for row in rows
        if row["seconds"] >= start
        and (
            end is None
            or row["seconds"] < end
        )
    ]

    start_hits = [
        row
        for row in candidates
        if any(
            p in row["text"].lower()
            for p in START_PATTERNS
        )
    ]

    end_hits = [
        row
        for row in candidates
        if any(
            p in row["text"].lower()
            for p in END_PATTERNS
        )
    ]

    start_found = bool(start_hits)
    end_found = bool(end_hits)

    ok = start_found and end_found

    if ok:
        passed += 1

    print()
    print("-" * 100)

    print(
        f"{'PASS' if ok else 'REVIEW'} | "
        f"UNIT {unit['unit_id']:02d} | "
        f"CHAPTER {unit['chapter']:02d}"
    )

    print(
        f"GUEST: {unit['guest']}"
    )

    print(
        f"CHAPTER START: "
        f"{unit['start_timestamp']}"
    )

    if start_hits:
        first = start_hits[0]
        print(
            f"INTRO SIGNAL: "
            f"{first['seconds']}s"
        )
        print(
            first["text"][:500]
        )
    else:
        print(
            "INTRO SIGNAL: NOT FOUND"
        )

    if end_hits:
        last = end_hits[-1]
        print(
            f"END SIGNAL: "
            f"{last['seconds']}s"
        )
        print(
            last["text"][:500]
        )
    else:
        print(
            "END SIGNAL: NOT FOUND"
        )


print()
print("=" * 100)
print("RESULT")
print("=" * 100)

print(
    f"PASS: {passed}/{len(units)}"
)

print(
    f"REVIEW: {len(units) - passed}"
)

print("=" * 100)
