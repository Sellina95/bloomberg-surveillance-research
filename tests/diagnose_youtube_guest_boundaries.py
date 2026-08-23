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

TIMESTAMP_RE = re.compile(
    r"^\d{1,2}:\d{2}(?::\d{2})?$"
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


def signal_matches(text: str, patterns: list[str]) -> list[str]:
    lowered = text.lower()

    return [
        pattern
        for pattern in patterns
        if pattern in lowered
    ]


lines = [
    x.strip()
    for x in TRANSCRIPT.read_text(
        encoding="utf-8"
    ).splitlines()
    if x.strip()
]


# ------------------------------------------------------------
# Parse timestamped transcript rows
# ------------------------------------------------------------

rows = []

for i, line in enumerate(lines):

    if not TIMESTAMP_RE.match(line):
        continue

    try:
        timestamp = to_seconds(line)
    except ValueError:
        continue

    # Collect transcript text until next timestamp.
    text_parts = []

    j = i + 1

    while (
        j < len(lines)
        and not TIMESTAMP_RE.match(lines[j])
    ):
        text_parts.append(lines[j])
        j += 1

    text = " ".join(text_parts)

    if text:
        rows.append(
            {
                "seconds": timestamp,
                "text": text,
            }
        )


units = json.loads(
    UNITS.read_text(
        encoding="utf-8"
    )
)["guest_units"]


print("=" * 100)
print("YOUTUBE GUEST BOUNDARY DIAGNOSTIC")
print("=" * 100)

print(
    f"TRANSCRIPT ROWS: {len(rows)}"
)

print(
    f"GUEST UNITS: {len(units)}"
)

print("=" * 100)


for unit in units:

    start = unit["start_seconds"]
    end = unit["end_seconds"]

    # --------------------------------------------------------
    # IMPORTANT:
    # Include a small look-behind before Chapter start.
    # The host may introduce the guest immediately before
    # the chapter marker.
    # --------------------------------------------------------

    lower_bound = max(
        0,
        start - 120,
    )

    upper_bound = (
        end
        if end is not None
        else float("inf")
    )

    candidates = [
        row
        for row in rows
        if lower_bound <= row["seconds"] < upper_bound
    ]

    start_hits = []

    end_hits = []

    for row in candidates:

        starts = signal_matches(
            row["text"],
            START_PATTERNS,
        )

        ends = signal_matches(
            row["text"],
            END_PATTERNS,
        )

        if starts:
            start_hits.append(
                (
                    row,
                    starts,
                )
            )

        if ends:
            end_hits.append(
                (
                    row,
                    ends,
                )
            )

    print()
    print("-" * 100)

    print(
        f"UNIT {unit['unit_id']:02d} | "
        f"CHAPTER {unit['chapter']:02d}"
    )

    print(
        f"GUEST: {unit['guest']}"
    )

    print(
        f"CHAPTER START: "
        f"{unit['start_timestamp']} "
        f"({start}s)"
    )

    print(
        f"CHAPTER END: "
        f"{unit['end_timestamp'] or 'END_OF_VIDEO'}"
    )

    print()

    print(
        "START SIGNALS:"
    )

    if start_hits:
        for row, signals in start_hits:
            print(
                f"  {row['seconds']}s | "
                f"{signals}"
            )
            print(
                f"    {row['text'][:500]}"
            )
    else:
        print(
            "  NONE"
        )

    print()

    print(
        "END SIGNALS:"
    )

    if end_hits:
        for row, signals in end_hits:
            print(
                f"  {row['seconds']}s | "
                f"{signals}"
            )
            print(
                f"    {row['text'][:500]}"
            )
    else:
        print(
            "  NONE"
        )

    # --------------------------------------------------------
    # Show immediate chapter neighborhood
    # --------------------------------------------------------

    print()

    print(
        "CHAPTER NEIGHBORHOOD:"
    )

    neighborhood = [
        row
        for row in rows
        if abs(row["seconds"] - start) <= 45
    ]

    for row in neighborhood:

        print(
            f"  {row['seconds']:7.1f}s | "
            f"{row['text'][:180]}"
        )


print()
print("=" * 100)
print("DIAGNOSTIC COMPLETE")
print("=" * 100)
