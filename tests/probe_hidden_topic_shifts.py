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
    left_segment = segments[boundary - 1]
    right_segment = segments[boundary]

    # --------------------------------------------------------
    # First: exclude explicit A / B / E boundaries.
    # --------------------------------------------------------

    end_matches = matches(
        left_segment["text"],
        END_PATTERNS,
    )

    start_matches = matches(
        right_segment["text"],
        START_PATTERNS,
    )

    left_words = len(
        tokenize(left_segment["text"])
    )

    right_words = len(
        tokenize(right_segment["text"])
    )

    micro_response = (
        left_words <= MICRO_RESPONSE_WORDS
        or right_words <= MICRO_RESPONSE_WORDS
    )

    if end_matches or start_matches or micro_response:
        continue

    # --------------------------------------------------------
    # Contextual semantic comparison.
    # --------------------------------------------------------

    left_context = context_text(
        boundary - WINDOW,
        boundary,
    )

    right_context = context_text(
        boundary,
        boundary + WINDOW,
    )

    similarity = cosine_similarity(
        vectorize(left_context),
        vectorize(right_context),
    )

    semantic_change = 1.0 - similarity

    speaker_change = (
        left_segment["speaker_index"]
        != right_segment["speaker_index"]
    )

    # --------------------------------------------------------
    # Candidate score
    #
    # This is NOT a production threshold.
    # It only ranks hidden topic-shift candidates.
    # --------------------------------------------------------

    score = semantic_change

    if speaker_change:
        score += 0.10

    results.append(
        {
            "boundary": boundary,
            "similarity": similarity,
            "semantic_change": semantic_change,
            "speaker_change": speaker_change,
            "score": score,
        }
    )


ranked = sorted(
    results,
    key=lambda row: row["score"],
    reverse=True,
)


print("=" * 100)
print("HIDDEN TOPIC SHIFT PROBE")
print("=" * 100)
print("DATE:", DATE)
print("WINDOW:", WINDOW)
print()
print(
    "명시적 방송 전환(A/B)과 micro-response(E)를 제외하고"
)
print(
    "숨은 topic-shift 후보만 semantic change 기준으로 정렬합니다."
)
print()
print(
    "주의: 이것은 아직 CUT 규칙이 아닙니다."
)
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
        f"CANDIDATE SCORE:     {row['score']:.3f}"
    )

    print(
        f"Semantic similarity:  {row['similarity']:.3f}"
    )

    print(
        f"Semantic change:      {row['semantic_change']:.3f}"
    )

    print(
        f"Speaker change:       {row['speaker_change']}"
    )

    print()
    print(
        f"LEFT [{left['start_seconds']:.1f}s]:"
    )
    print(left["text"][:350])

    print()
    print(
        f"RIGHT [{right['start_seconds']:.1f}s]:"
    )
    print(right["text"][:350])


print()
print("=" * 100)
print("KNOWN CONTINUATION CHECK")
print("=" * 100)

# 이전 실험에서 같은 대화 흐름으로 확인했던 구간.
known_continuations = [
    19,
    20,
    21,
    22,
]

for boundary in known_continuations:
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
            f"{boundary - 1} → {boundary}: "
            "EXCLUDED"
        )
        continue

    print(
        f"{boundary - 1} → {boundary} | "
        f"CHANGE={row['semantic_change']:.3f} | "
        f"SCORE={row['score']:.3f} | "
        f"SPEAKER_CHANGE={row['speaker_change']}"
    )

print("=" * 100)
