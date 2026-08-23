from __future__ import annotations

import json
import math
import re
from pathlib import Path
from collections import Counter


DATE = "2026-08-14"

PATH = (
    Path("data/processed/surveillance")
    / DATE
    / "segments.json"
)


def tokenize(text: str) -> list[str]:
    return re.findall(
        r"[a-zA-Z][a-zA-Z'-]+",
        text.lower(),
    )


def vectorize(tokens: list[str]) -> Counter[str]:
    return Counter(tokens)


def cosine_similarity(
    left: Counter[str],
    right: Counter[str],
) -> float:
    if not left or not right:
        return 0.0

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


payload = json.loads(
    PATH.read_text(encoding="utf-8")
)

segments = payload["segments"]

vectors = [
    vectorize(tokenize(segment["text"]))
    for segment in segments
]


results = []

for i in range(1, len(segments)):
    previous = vectors[i - 1]
    current = vectors[i]

    similarity = cosine_similarity(
        previous,
        current,
    )

    results.append(
        {
            "index": i,
            "previous_segment": segments[i - 1],
            "current_segment": segments[i],
            "similarity": similarity,
        }
    )


# 가장 큰 의미 변화 후보부터 확인
ranked = sorted(
    results,
    key=lambda row: row["similarity"],
)


print("=" * 100)
print("SEMANTIC BOUNDARY PROBE")
print("=" * 100)
print("DATE:", DATE)
print("SEGMENTS:", len(segments))
print()

print(
    "Lowest-similarity adjacent segments "
    "(potential topic boundaries)"
)
print("=" * 100)


for row in ranked[:20]:
    previous = row["previous_segment"]
    current = row["current_segment"]

    print()
    print(
        f"SIMILARITY: {row['similarity']:.3f}"
    )

    print(
        f"PREVIOUS "
        f"SEGMENT {previous['segment_id']} "
        f"[{previous['start_seconds']:.1f}s]"
    )
    print(
        previous["text"][:300]
    )

    print(
        f"CURRENT "
        f"SEGMENT {current['segment_id']} "
        f"[{current['start_seconds']:.1f}s]"
    )
    print(
        current["text"][:300]
    )


print()
print("=" * 100)
print("HIGH-SIMILARITY EXAMPLES")
print("=" * 100)

for row in ranked[-5:]:
    previous = row["previous_segment"]
    current = row["current_segment"]

    print()
    print(
        f"SIMILARITY: {row['similarity']:.3f} | "
        f"{previous['segment_id']} → "
        f"{current['segment_id']}"
    )

    print(
        "PREVIOUS:",
        previous["text"][:180]
    )
    print(
        "CURRENT :",
        current["text"][:180]
    )

print("=" * 100)
