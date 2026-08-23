from __future__ import annotations

import json
import re
from pathlib import Path


DATE = "2026-08-14"

PATH = (
    Path("data/processed/surveillance")
    / DATE
    / "segments.json"
)

# Known guest introductions from the transcript.
INTRO_SEGMENTS = [4, 48, 55, 70]

START_PATTERNS = [
    "joins us now",
    "joins us",
]

END_PATTERNS = [
    "stay with us",
    "coming up after",
    "more bloomberg surveillance coming up",
    "thank you so much",
    "thanks for having me",
]


def normalize(text: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        text.lower(),
    ).strip()


def contains_any(
    text: str,
    patterns: list[str],
) -> bool:
    text = normalize(text)
    return any(
        pattern in text
        for pattern in patterns
    )


payload = json.loads(
    PATH.read_text(encoding="utf-8")
)

segments = payload["segments"]


results = []


for intro_id in INTRO_SEGMENTS:

    intro = segments[intro_id]

    start_ok = contains_any(
        intro["text"],
        START_PATTERNS,
    )

    end_id = None

    for segment in segments[intro_id + 1:]:

        if contains_any(
            segment["text"],
            END_PATTERNS,
        ):
            end_id = segment["segment_id"]
            break

    end_ok = end_id is not None

    duration = None

    if end_ok:
        duration = (
            segments[end_id]["start_seconds"]
            - intro["start_seconds"]
        )

    results.append(
        {
            "intro_id": intro_id,
            "start_time": intro["start_seconds"],
            "start_ok": start_ok,
            "end_id": end_id,
            "end_ok": end_ok,
            "duration": duration,
        }
    )


print("=" * 100)
print("GUEST BOUNDARY VALIDATION v0.1")
print("=" * 100)
print("DATE:", DATE)
print("GUEST CANDIDATES:", len(results))
print("=" * 100)


all_pass = True


for row in results:

    passed = (
        row["start_ok"]
        and row["end_ok"]
    )

    if not passed:
        all_pass = False

    status = "PASS" if passed else "FAIL"

    print()
    print(
        f"{status} | "
        f"START SEGMENT {row['intro_id']} "
        f"→ END SEGMENT {row['end_id']}"
    )

    print(
        f"START TIME: "
        f"{row['start_time']:.1f}s"
    )

    if row["duration"] is not None:
        print(
            f"DURATION: "
            f"{row['duration']:.1f}s"
        )

    print(
        f"START SIGNAL: {row['start_ok']}"
    )

    print(
        f"END SIGNAL: {row['end_ok']}"
    )


print()
print("=" * 100)

if all_pass:
    print(
        "GUEST BOUNDARY VALIDATION: PASS"
    )
else:
    print(
        "GUEST BOUNDARY VALIDATION: FAIL"
    )

print("=" * 100)
