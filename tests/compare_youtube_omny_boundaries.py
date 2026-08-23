from __future__ import annotations

import json
from pathlib import Path


OMNY = Path(
    "data/processed/surveillance/2026-08-14/segments.json"
)

YOUTUBE = Path(
    "data/reference/youtube/2026-08-14_transcript.txt"
)


OMNY_GUESTS = [
    {
        "name": "Julian",
        "start_segment": 4,
        "end_segment": 46,
    },
    {
        "name": "Michael Halen",
        "start_segment": 48,
        "end_segment": 54,
    },
    {
        "name": "Nick Setyan",
        "start_segment": 55,
        "end_segment": 69,
    },
    {
        "name": "Robert DeNault",
        "start_segment": 70,
        "end_segment": 71,
    },
]


def seconds(value: str) -> int:
    parts = [int(x) for x in value.split(":")]

    if len(parts) == 2:
        return parts[0] * 60 + parts[1]

    return (
        parts[0] * 3600
        + parts[1] * 60
        + parts[2]
    )


text = YOUTUBE.read_text(
    encoding="utf-8"
)

lines = [
    x.strip()
    for x in text.splitlines()
    if x.strip()
]


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


youtube_events = []

for i, line in enumerate(lines):

    # YouTube transcript timestamps.
    if not line[:1].isdigit():
        continue

    parts = line.split(":")

    if len(parts) not in (2, 3):
        continue

    try:
        t = seconds(line)
    except ValueError:
        continue

    text_after = " ".join(
        lines[i + 1:i + 4]
    ).lower()

    starts = [
        p for p in START_PATTERNS
        if p in text_after
    ]

    ends = [
        p for p in END_PATTERNS
        if p in text_after
    ]

    if starts or ends:
        youtube_events.append(
            {
                "time": t,
                "starts": starts,
                "ends": ends,
                "text": text_after,
            }
        )


payload = json.loads(
    OMNY.read_text(
        encoding="utf-8"
    )
)

segments = payload["segments"]


print("=" * 100)
print("YOUTUBE ↔ OMNY GUEST BOUNDARY COMPARISON")
print("=" * 100)

print()
print("OMNY boundaries")
print("-" * 100)

for guest in OMNY_GUESTS:

    start = segments[
        guest["start_segment"]
    ]

    end = segments[
        guest["end_segment"]
    ]

    print(
        f"{guest['name']:20s} | "
        f"OMNY {start['start_seconds']:.1f}s"
        f" → "
        f"{end['start_seconds']:.1f}s"
    )


print()
print("YOUTUBE boundary signals")
print("-" * 100)

for event in youtube_events:

    print(
        f"{event['time']:7d}s | "
        f"START={event['starts']} "
        f"END={event['ends']}"
    )

    print(
        "  ",
        event["text"][:250]
    )


print()
print("=" * 100)
print("COMPARISON COMPLETE")
print("=" * 100)
