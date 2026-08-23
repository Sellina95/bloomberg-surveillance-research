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

START_PATTERNS = [
    "joins us now",
    "joins us",
    "joined by",
]

END_PATTERNS = [
    "thank you so much",
    "thank you",
    "thanks for having me",
    "thanks for being",
    "stay with us",
    "coming up",
]


def normalize(text: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        text.strip(),
    )


def find_matches(
    text: str,
    patterns: list[str],
) -> list[str]:
    lower = text.lower()

    return [
        pattern
        for pattern in patterns
        if pattern in lower
    ]


payload = json.loads(
    PATH.read_text(encoding="utf-8")
)

segments = payload["segments"]


# ------------------------------------------------------------
# Find likely interview starts
# ------------------------------------------------------------

starts = []

for i, segment in enumerate(segments):
    matches = find_matches(
        segment["text"],
        START_PATTERNS,
    )

    if not matches:
        continue

    starts.append(
        {
            "segment": i,
            "time": segment["start_seconds"],
            "text": segment["text"],
            "patterns": matches,
        }
    )


# ------------------------------------------------------------
# Find likely interview endings
# ------------------------------------------------------------

ends = []

for i, segment in enumerate(segments):
    matches = find_matches(
        segment["text"],
        END_PATTERNS,
    )

    if not matches:
        continue

    ends.append(
        {
            "segment": i,
            "time": segment["start_seconds"],
            "text": segment["text"],
            "patterns": matches,
        }
    )


# ------------------------------------------------------------
# Pair each start with the next plausible ending.
#
# This is deliberately only a probe.
# We are not claiming perfect guest identity resolution.
# ------------------------------------------------------------

intervals = []

for start in starts:
    start_segment = start["segment"]

    next_end = next(
        (
            end
            for end in ends
            if end["segment"] > start_segment
        ),
        None,
    )

    if next_end is None:
        continue

    interval_segments = segments[
        start_segment:next_end["segment"] + 1
    ]

    speaker_ids = sorted(
        {
            segment["speaker_index"]
            for segment in interval_segments
        }
    )

    intervals.append(
        {
            "start_segment": start_segment,
            "end_segment": next_end["segment"],
            "start_time": start["time"],
            "end_time": next_end["time"],
            "duration_seconds": (
                next_end["time"] - start["time"]
            ),
            "start_patterns": start["patterns"],
            "end_patterns": next_end["patterns"],
            "speaker_ids": speaker_ids,
            "segment_count": len(interval_segments),
        }
    )


print("=" * 100)
print("GUEST / INTERVIEW INTERVAL PROBE")
print("=" * 100)
print("DATE:", DATE)
print("TOTAL SEGMENTS:", len(segments))
print()
print("This probe identifies likely interview intervals.")
print("It does NOT resolve guest names or institutions yet.")
print("=" * 100)


print()
print("START CANDIDATES")
print("-" * 100)

for item in starts:
    print()
    print(
        f"SEGMENT {item['segment']} "
        f"[{item['time']:.1f}s]"
    )

    print(
        "PATTERNS:",
        ", ".join(item["patterns"]),
    )

    print(
        normalize(item["text"])[:350]
    )


print()
print("=" * 100)
print("INTERVAL CANDIDATES")
print("=" * 100)

for number, interval in enumerate(
    intervals,
    start=1,
):
    print()
    print("-" * 100)

    print(
        f"INTERVAL {number}"
    )

    print(
        f"SEGMENTS: "
        f"{interval['start_segment']} "
        f"→ "
        f"{interval['end_segment']}"
    )

    print(
        f"TIME: "
        f"{interval['start_time']:.1f}s "
        f"→ "
        f"{interval['end_time']:.1f}s"
    )

    print(
        f"DURATION: "
        f"{interval['duration_seconds']:.1f}s"
    )

    print(
        f"SEGMENT COUNT: "
        f"{interval['segment_count']}"
    )

    print(
        "START SIGNAL:",
        ", ".join(
            interval["start_patterns"]
        ),
    )

    print(
        "END SIGNAL:",
        ", ".join(
            interval["end_patterns"]
        ),
    )

    print(
        "SPEAKER IDS:",
        interval["speaker_ids"],
    )


print()
print("=" * 100)
print("INTERVAL COVERAGE")
print("=" * 100)

covered = set()

for interval in intervals:
    covered.update(
        range(
            interval["start_segment"],
            interval["end_segment"] + 1,
        )
    )

print(
    "INTERVALS FOUND:",
    len(intervals),
)

print(
    "SEGMENTS COVERED:",
    len(covered),
)

print(
    "COVERAGE:",
    f"{len(covered) / len(segments) * 100:.1f}%"
)

print("=" * 100)
