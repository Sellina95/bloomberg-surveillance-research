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


def tokenize(text: str) -> list[str]:
    return re.findall(
        r"[a-zA-Z][a-zA-Z'-]+",
        text.lower(),
    )


def build_vector(text: str) -> Counter[str]:
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


payload = json.loads(
    PATH.read_text(encoding="utf-8")
)

segments = payload["segments"]


def context_text(start: int, end: int) -> str:
    return " ".join(
        segment["text"]
        for segment in segments[start:end]
    )


results = []

# 앞 WINDOW개 발언과 뒤 WINDOW개 발언을 비교한다.
for boundary in range(
    WINDOW,
    len(segments) - WINDOW + 1,
):
    left_text = context_text(
        boundary - WINDOW,
        boundary,
    )

    right_text = context_text(
        boundary,
        boundary + WINDOW,
    )

    similarity = cosine_similarity(
        build_vector(left_text),
        build_vector(right_text),
    )

    results.append(
        {
            "boundary": boundary,
            "similarity": similarity,
            "left": segments[
                boundary - WINDOW
            ],
            "right": segments[
                boundary
            ],
        }
    )


ranked = sorted(
    results,
    key=lambda row: row["similarity"],
)


print("=" * 100)
print("CONTEXTUAL SEMANTIC BOUNDARY PROBE")
print("=" * 100)
print("DATE:", DATE)
print("SEGMENTS:", len(segments))
print("WINDOW:", WINDOW)
print()
print(
    "앞 5개 발언 vs 뒤 5개 발언의 의미 유사도를 비교합니다."
)
print(
    "낮은 값일수록 '주제가 바뀌었을 가능성'이 높습니다."
)
print("=" * 100)


for row in ranked[:15]:
    left = row["left"]
    right = row["right"]

    print()
    print(
        f"SIMILARITY: {row['similarity']:.3f}"
    )

    print(
        f"BOUNDARY: "
        f"SEGMENT {row['boundary'] - 1} "
        f"→ SEGMENT {row['boundary']}"
    )

    print(
        f"LEFT CONTEXT ENDS: "
        f"[{left['start_seconds']:.1f}s]"
    )
    print(
        left["text"][:250]
    )

    print(
        f"RIGHT CONTEXT STARTS: "
        f"[{right['start_seconds']:.1f}s]"
    )
    print(
        right["text"][:250]
    )


print()
print("=" * 100)
print("KNOWN TRANSITION CHECK")
print("=" * 100)

# 우리가 실제 방송상 전환으로 확인했던 구간.
known_boundaries = [47, 48]

for boundary in known_boundaries:
    matches = [
        row
        for row in results
        if row["boundary"] == boundary
    ]

    if not matches:
        continue

    row = matches[0]

    print(
        f"BOUNDARY {boundary - 1} → {boundary}: "
        f"SIMILARITY={row['similarity']:.3f}"
    )

print("=" * 100)
