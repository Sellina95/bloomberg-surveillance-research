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

    start_matches = matches(
        right_text,
        START_PATTERNS,
    )

    end_matches = matches(
        left_text,
        END_PATTERNS,
    )

    courtesy_matches = (
        matches(left_text, COURTESY_PATTERNS)
        + matches(right_text, COURTESY_PATTERNS)
    )

    left_words = len(
        tokenize(left_text)
    )

    right_words = len(
        tokenize(right_text)
    )

    micro_response = (
        left_words <= MICRO_RESPONSE_WORDS
        or right_words <= MICRO_RESPONSE_WORDS
    )

    speaker_change = (
        left["speaker_index"]
        != right["speaker_index"]
    )

    # --------------------------------------------------------
    # A — HARD BREAK
    # --------------------------------------------------------
    if end_matches and start_matches:
        return (
            "A",
            [
                "explicit_end_transition",
                "explicit_new_segment_transition",
            ],
        )

    if end_matches:
        return (
            "A",
            [
                "explicit_end_transition",
            ],
        )

    # --------------------------------------------------------
    # B — INTERVIEW / GUEST TRANSITION
    # --------------------------------------------------------
    if start_matches:
        return (
            "B",
            [
                "explicit_guest_transition",
            ],
        )

    # --------------------------------------------------------
    # E — MICRO RESPONSE
    # --------------------------------------------------------
    if micro_response:
        return (
            "E",
            [
                "very_short_segment",
            ],
        )

    # --------------------------------------------------------
    # B — COURTESY / GUEST HANDOFF
    #
    # Courtesy alone is NOT enough for a hard break.
    # We classify it separately for inspection.
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
    # D — CONTINUATION
    #
    # Default assumption:
    # if there is no explicit transition signal,
    # treat the conversation as continuous.
    # --------------------------------------------------------
    if speaker_change:
        return (
            "D",
            [
                "speaker_change_only",
            ],
        )

    return (
        "D",
        [
            "no_explicit_transition",
        ],
    )


counts = Counter()
examples: dict[str, list[tuple[int, str, str, list[str]]]] = {
    "A": [],
    "B": [],
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

    if len(examples[category]) < 8:
        examples[category].append(
            (
                boundary,
                left["text"],
                right["text"],
                reasons,
            )
        )


print("=" * 100)
print("BOUNDARY TAXONOMY PROBE")
print("=" * 100)
print("DATE:", DATE)
print("BOUNDARIES:", len(segments) - 1)
print()
print("A = HARD BREAK")
print("B = INTERVIEW / GUEST TRANSITION")
print("C = TOPIC SHIFT WITHOUT EXPLICIT HANDOFF")
print("D = CONTINUATION")
print("E = MICRO RESPONSE / FALSE-POSITIVE RISK")
print("=" * 100)


print()
print("CATEGORY COUNTS")
print("-" * 100)

for category in ["A", "B", "C", "D", "E"]:
    count = counts[category]
    pct = count / (len(segments) - 1) * 100

    print(
        f"{category}: {count:3d} "
        f"({pct:5.1f}%)"
    )


for category in ["A", "B", "C", "D", "E"]:
    print()
    print("=" * 100)
    print(f"CATEGORY {category}")
    print("=" * 100)

    if not examples[category]:
        print("NO EXAMPLES")
        continue

    for (
        boundary,
        left_text,
        right_text,
        reasons,
    ) in examples[category]:

        print()
        print(
            f"BOUNDARY {boundary - 1} → {boundary}"
        )

        print(
            "REASONS:",
            ", ".join(reasons),
        )

        print(
            f"LEFT:  {left_text[:220]}"
        )

        print(
            f"RIGHT: {right_text[:220]}"
        )


print()
print("=" * 100)
print("KNOWN TRANSITION CHECK")
print("=" * 100)

for boundary in [46, 47, 48]:
    left = segments[boundary - 1]
    right = segments[boundary]

    category, reasons = classify_boundary(
        left,
        right,
    )

    print(
        f"{boundary - 1} → {boundary} "
        f"=> CATEGORY {category} | "
        f"{', '.join(reasons)}"
    )

print("=" * 100)
