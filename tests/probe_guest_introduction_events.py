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


INTRO_PATTERNS = [
    "next is",
    "with us now",
    "joining us",
    "joins us now",
    "joins us",
    "joined by",
    "we're joined by",
    "our guest",
    "speaking with us",
]

GREETING_PATTERNS = [
    "hi ",
    "hello ",
    "great to see you",
    "good to see you",
    "thanks for joining",
    "thank you for joining",
]


def matches(
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


print("=" * 100)
print("GUEST INTRODUCTION EVENT PROBE")
print("=" * 100)
print("DATE:", DATE)
print("SEGMENTS:", len(segments))
print("=" * 100)


events = []


for i, segment in enumerate(segments):

    intro = matches(
        segment["text"],
        INTRO_PATTERNS,
    )

    if not intro:
        continue

    print()
    print("-" * 100)

    print(
        f"INTRODUCTION CANDIDATE"
    )

    print(
        f"SEGMENT: {i}"
    )

    print(
        f"TIME: "
        f"{segment['start_seconds']:.1f}s"
    )

    print(
        f"SPEAKER: "
        f"{segment['speaker_index']}"
    )

    print(
        "INTRO SIGNAL:",
        ", ".join(intro),
    )

    print()
    print(
        "INTRO TEXT:"
    )

    print(
        segment["text"][:700]
    )

    # --------------------------------------------------------
    # Look at the next 5 segments.
    # --------------------------------------------------------

    print()
    print(
        "FOLLOWING SPEAKER SEQUENCE:"
    )

    for j in range(
        i + 1,
        min(i + 6, len(segments)),
    ):

        next_segment = segments[j]

        greeting = matches(
            next_segment["text"],
            GREETING_PATTERNS,
        )

        print(
            f"  SEG {j:3d} | "
            f"{next_segment['start_seconds']:7.1f}s | "
            f"SPEAKER "
            f"{next_segment['speaker_index']} | "
            f"{next_segment['word_count']:3d} words"
        )

        if greeting:
            print(
                "      GREETING:",
                ", ".join(greeting),
            )

        print(
            f"      "
            f"{next_segment['text'][:300]}"
        )

    events.append(i)


print()
print("=" * 100)
print("SUMMARY")
print("=" * 100)

print(
    "INTRODUCTION CANDIDATES:",
    len(events),
)

print(
    "SEGMENTS:",
    events,
)

print()
print(
    "This probe does not identify guest names."
)

print(
    "It tests whether introduction language is followed "
    "by a stable speaker transition."
)

print("=" * 100)
