from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path


DATE = "2026-08-14"
WINDOW = 8

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

MICRO_RESPONSE_WORDS = 3


def tokenize(text: str) -> list[str]:
    return re.findall(
        r"[a-zA-Z][a-zA-Z'-]+",
        text.lower(),
    )


def vectorize(text: str) -> Counter[str]:
    return Counter(tokenize(text))


def cosine_similarity(
    left: Counter[str],
    right: Counter[str],
) -> float:
    common = set(left) & set(right)

    numerator = sum(
        left[token] * right[token]
        for token in common
    )

    left_norm = math.sqrt(
        sum(value * value for value in left.values())
    )

    right_norm = math.sqrt(
        sum(value * value for value in right.values())
    )

    if left_norm == 0 or right_norm == 0:
        return 0.0

    return numerator / (left_norm * right_norm)


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


def context_text(
    start: int,
    end: int,
) -> str:
    return " ".join(
        segment["text"]
        for segment in segments[start:end]
    )


results = []

for boundary in range(
    WINDOW,
    len(segments) - WINDOW + 1,
):
    left = segments[boundary - 1]
    right = segments[boundary]

    # --------------------------------------------------------
    # Explicit boundaries are handled by the broadcast
    # taxonomy, not by semantic detection.
    # --------------------------------------------------------

    if matches(left["text"], END_PATTERNS):
        continue

    if matches(right["text"], START_PATTERNS):
        continue

    left_words = len(
        tokenize(left["text"])
    )

    right_words = len(
        tokenize(right["text"])
    )

    if (
        left_words <= MICRO_RESPONSE_WORDS
        or right_words <= MICRO_RESPONSE_WORDS
    ):
        continue

    # --------------------------------------------------------
    # Wider context.
    #
    # Exclude the immediate boundary segments themselves.
    # This reduces the influence of "Yeah", "Right", etc.
    # and tests broader topic continuity.
    # --------------------------------------------------------

    left_start = max(
        0,
        boundary - WINDOW,
    )

    left_end = boundary - 1

    right_start = boundary + 1

    right_end = min(
        len(segments),
        boundary + WINDOW + 1,
    )

    left_context = context_text(
        left_start,
        left_end,
    )

    right_context = context_text(
        right_start,
        right_end,
    )

    similarity = cosine_similarity(
        vectorize(left_context),
        vectorize(right_context),
    )

    topic_change = 1.0 - similarity

    results.append(
        {
            "boundary": boundary,
            "similarity": similarity,
            "topic_change": topic_change,
        }
    )


ranked = sorted(
    results,
    key=lambda row: row["topic_change"],
    reverse=True,
)


print("=" * 100)
print("TOPIC CONTINUITY PROBE v0.2")
print("=" * 100)
print("DATE:", DATE)
print("WINDOW:", WINDOW)
print()
print(
    "Speaker change is deliberately NOT used as a topic-shift signal."
)
print(
    "Immediate boundary segments are excluded from the semantic comparison."
)
print()
print("This is a research diagnostic, not a CUT rule.")
print("=" * 100)


for row in ranked[:15]:
    boundary = row["boundary"]

    left = segments[boundary - 1]
    right = segments[boundary]

    print()
    print("-" * 100)

    print(
        f"BOUNDARY: SEGMENT {boundary - 1} "
        f"→ SEGMENT {boundary}"
    )

    print(
        f"TOPIC CHANGE: {row['topic_change']:.3f}"
    )

    print(
        f"SIMILARITY:   {row['similarity']:.3f}"
    )

    print()
    print(
        f"LEFT [{left['start_seconds']:.1f}s]:"
    )
    print(left["text"][:300])

    print()
    print(
        f"RIGHT [{right['start_seconds']:.1f}s]:"
    )
    print(right["text"][:300])


print()
print("=" * 100)
print("KNOWN CONTINUATION CHECK")
print("=" * 100)

for boundary in [
    19,
    20,
    21,
    22,
]:
    row = next(
        (
            item
            for item in results
            if item["boundary"] == boundary
        ),
        None,
    )

    if row is None:
        print(
            f"{boundary - 1} → {boundary}: EXCLUDED"
        )
        continue

    print(
        f"{boundary - 1} → {boundary} | "
        f"CHANGE={row['topic_change']:.3f} | "
        f"SIM={row['similarity']:.3f}"
    )

print("=" * 100)
