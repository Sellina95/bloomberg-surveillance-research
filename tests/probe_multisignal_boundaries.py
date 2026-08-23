from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path


DATE = "2026-08-14"
WINDOW = 5

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


def find_patterns(
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
    1,
    len(segments),
):
    left_segment = segments[boundary - 1]
    right_segment = segments[boundary]

    left_start = max(
        0,
        boundary - WINDOW,
    )

    right_end = min(
        len(segments),
        boundary + WINDOW,
    )

    left_context = context_text(
        left_start,
        boundary,
    )

    right_context = context_text(
        boundary,
        right_end,
    )

    similarity = cosine_similarity(
        vectorize(left_context),
        vectorize(right_context),
    )

    semantic_change = 1.0 - similarity

    start_matches = find_patterns(
        right_segment["text"],
        START_PATTERNS,
    )

    end_matches = find_patterns(
        left_segment["text"],
        END_PATTERNS,
    )

    courtesy_matches = (
        find_patterns(
            left_segment["text"],
            COURTESY_PATTERNS,
        )
        + find_patterns(
            right_segment["text"],
            COURTESY_PATTERNS,
        )
    )

    speaker_change = (
        left_segment["speaker_index"]
        != right_segment["speaker_index"]
    )

    previous_words = len(
        tokenize(left_segment["text"])
    )

    current_words = len(
        tokenize(right_segment["text"])
    )

    short_response = (
        previous_words <= 3
        or current_words <= 3
    )

    score = 0.0

    # Semantic change = supporting evidence.
    if semantic_change >= 0.60:
        score += 2.0
    elif semantic_change >= 0.45:
        score += 1.0

    # Explicit broadcast transition.
    if start_matches:
        score += 2.0

    if end_matches:
        score += 2.0

    # Speaker change = weak supporting evidence.
    if speaker_change:
        score += 0.5

    # Courtesy phrases alone should NOT create a boundary.
    if courtesy_matches:
        score -= 0.25

    # Very short responses are often false positives.
    if short_response:
        score -= 1.0

    results.append(
        {
            "boundary": boundary,
            "similarity": similarity,
            "semantic_change": semantic_change,
            "start_matches": start_matches,
            "end_matches": end_matches,
            "courtesy_matches": courtesy_matches,
            "speaker_change": speaker_change,
            "short_response": short_response,
            "score": score,
        }
    )


ranked = sorted(
    results,
    key=lambda row: row["score"],
    reverse=True,
)


print("=" * 100)
print("MULTI-SIGNAL BOUNDARY PROBE")
print("=" * 100)
print("DATE:", DATE)
print("SEGMENTS:", len(segments))
print("CONTEXT WINDOW:", WINDOW)
print()
print("SCORE는 아직 확정된 규칙이 아닙니다.")
print("실제 방송 전환과 어떤 신호가 함께 나타나는지 확인하는 실험입니다.")
print("=" * 100)


for row in ranked[:20]:
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
        f"SCORE:              {row['score']:.2f}"
    )

    print(
        f"Semantic similarity: {row['similarity']:.3f}"
    )

    print(
        f"Semantic change:     {row['semantic_change']:.3f}"
    )

    print(
        f"Speaker change:      {row['speaker_change']}"
    )

    print(
        f"Short response:      {row['short_response']}"
    )

    print(
        "Start phrase:        "
        + (
            ", ".join(row["start_matches"])
            if row["start_matches"]
            else "NONE"
        )
    )

    print(
        "End phrase:          "
        + (
            ", ".join(row["end_matches"])
            if row["end_matches"]
            else "NONE"
        )
    )

    print(
        "Courtesy phrase:     "
        + (
            ", ".join(row["courtesy_matches"])
            if row["courtesy_matches"]
            else "NONE"
        )
    )

    print()
    print(
        f"PREVIOUS [{left['start_seconds']:.1f}s]:"
    )
    print(left["text"][:300])

    print()
    print(
        f"CURRENT [{right['start_seconds']:.1f}s]:"
    )
    print(right["text"][:300])


print()
print("=" * 100)
print("KNOWN TRANSITION CHECK")
print("=" * 100)

for boundary in [47, 48]:
    row = next(
        (
            item
            for item in results
            if item["boundary"] == boundary
        ),
        None,
    )

    if row is None:
        continue

    print(
        f"SEGMENT {boundary - 1} → SEGMENT {boundary} | "
        f"SCORE={row['score']:.2f} | "
        f"SIM={row['similarity']:.3f} | "
        f"START={row['start_matches']} | "
        f"END={row['end_matches']} | "
        f"SPEAKER_CHANGE={row['speaker_change']} | "
        f"SHORT={row['short_response']}"
    )

print("=" * 100)
