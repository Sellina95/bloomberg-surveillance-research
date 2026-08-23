from __future__ import annotations

import json
import re
from collections import Counter
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
    "coming up",
    "stay with us",
    "more bloomberg surveillance coming up",
]

COURTESY_PATTERNS = [
    "thank you",
    "thank you so much",
    "thanks for having me",
    "great to see you",
    "good to see you",
]

MICRO_RESPONSE_WORDS = 3


def tokenize(text: str) -> list[str]:
    return re.findall(
        r"[a-zA-Z][a-zA-Z'-]+",
        text.lower(),
    )


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


def classify_boundary(
    left: dict,
    right: dict,
) -> tuple[str, list[str]]:
    left_text = left["text"]
    right_text = right["text"]

    end_matches = matches(
        left_text,
        END_PATTERNS,
    )

    start_matches = matches(
        right_text,
        START_PATTERNS,
    )

    courtesy_matches = (
        matches(left_text, COURTESY_PATTERNS)
        + matches(right_text, COURTESY_PATTERNS)
    )

    left_words = len(tokenize(left_text))
    right_words = len(tokenize(right_text))

    micro_response = (
        left_words <= MICRO_RESPONSE_WORDS
        or right_words <= MICRO_RESPONSE_WORDS
    )

    speaker_change = (
        left["speaker_index"]
        != right["speaker_index"]
    )

    # --------------------------------------------------------
    # A+B — broadcast ending + new guest/interview
    # --------------------------------------------------------
    if end_matches and start_matches:
        return (
            "A+B",
            [
                "broadcast_end",
                "new_guest_or_interview",
            ],
        )

    # --------------------------------------------------------
    # A — broadcast / program transition
    # --------------------------------------------------------
    if end_matches:
        return (
            "A",
            [
                "broadcast_end",
            ],
        )

    # --------------------------------------------------------
    # B — new guest / interview transition
    # --------------------------------------------------------
    if start_matches:
        return (
            "B",
            [
                "new_guest_or_interview",
            ],
        )

    # --------------------------------------------------------
    # E — micro response
    #
    # Checked before courtesy so that:
    # "Thank you." / "Right." / "Yeah."
    # is not accidentally treated as a meaningful handoff.
    # --------------------------------------------------------
    if micro_response:
        return (
            "E",
            [
                "micro_response",
            ],
        )

    # --------------------------------------------------------
    # B — courtesy + speaker change
    #
    # This is a weaker guest-handoff candidate.
    # It is deliberately NOT treated as a hard break.
    # --------------------------------------------------------
    if courtesy_matches and speaker_change:
        return (
            "B",
            [
                "courtesy_handoff",
                "speaker_change",
            ],
        )

    # --------------------------------------------------------
    # D — continuation
    #
    # Conservative default:
    # without an explicit transition signal,
    # do not break the research chunk yet.
    # --------------------------------------------------------
    return (
        "D",
        [
            "no_explicit_boundary_signal",
        ],
    )


counts = Counter()
examples: dict[str, list[dict]] = {
    "A": [],
    "B": [],
    "A+B": [],
    "C": [],
    "D": [],
    "E": [],
}


for boundary in range(1, len(segments)):
    left = segments[boundary - 1]
    right = segments[boundary]

    category, reasons = classify_boundary(
        left,
        right,
    )

    counts[category] += 1

    if len(examples[category]) < 10:
        examples[category].append(
            {
                "boundary": boundary,
                "reasons": reasons,
                "left": left["text"],
                "right": right["text"],
            }
        )


total = len(segments) - 1


print("=" * 100)
print("BOUNDARY TAXONOMY v0.2")
print("=" * 100)
print("DATE:", DATE)
print("SEGMENTS:", len(segments))
print("BOUNDARIES:", total)
print()
print("A   = BROADCAST / PROGRAM END")
print("B   = NEW GUEST / INTERVIEW START")
print("A+B = END + NEW GUEST COMBINED")
print("C   = TOPIC SHIFT WITHOUT EXPLICIT HANDOFF")
print("D   = CONTINUATION")
print("E   = MICRO RESPONSE")
print("=" * 100)


print()
print("CATEGORY COUNTS")
print("-" * 100)

for category in [
    "A",
    "B",
    "A+B",
    "C",
    "D",
    "E",
]:
    count = counts[category]
    pct = (
        count / total * 100
        if total
        else 0.0
    )

    print(
        f"{category:3s}: {count:3d} "
        f"({pct:5.1f}%)"
    )


for category in [
    "A",
    "B",
    "A+B",
    "C",
    "D",
    "E",
]:
    print()
    print("=" * 100)
    print(f"CATEGORY {category} — EXAMPLES")
    print("=" * 100)

    if not examples[category]:
        print("NO EXAMPLES")
        continue

    for item in examples[category]:
        boundary = item["boundary"]

        print()
        print(
            f"BOUNDARY "
            f"{boundary - 1} → {boundary}"
        )

        print(
            "REASONS:",
            ", ".join(item["reasons"]),
        )

        print(
            "LEFT:",
            item["left"][:240],
        )

        print(
            "RIGHT:",
            item["right"][:240],
        )


print()
print("=" * 100)
print("KNOWN TRANSITION CHECK")
print("=" * 100)

for boundary in [45, 46, 47, 48]:
    left = segments[boundary - 1]
    right = segments[boundary]

    category, reasons = classify_boundary(
        left,
        right,
    )

    print(
        f"{boundary - 1} → {boundary} "
        f"=> {category} | "
        f"{', '.join(reasons)}"
    )

print("=" * 100)
