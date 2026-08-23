from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path


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


payload = json.loads(
    PATH.read_text(encoding="utf-8")
)

segments = payload["segments"]


profiles = defaultdict(
    lambda: {
        "segments": [],
        "questions": 0,
        "answers": 0,
    }
)


for segment in segments:
    speaker = segment["speaker_index"]
    text = segment["text"].strip()

    profiles[speaker]["segments"].append(segment)

    # 매우 보수적인 probe.
    # 이것을 speaker-role 판정 규칙으로 사용하지 않는다.
    if "?" in text:
        profiles[speaker]["questions"] += 1

    lower = text.lower()

    if (
        lower.startswith("so i ")
        or lower.startswith("i think ")
        or lower.startswith("well, ")
        or lower.startswith("we ")
        or lower.startswith("our ")
    ):
        profiles[speaker]["answers"] += 1


print("=" * 100)
print("SPEAKER ROLE PROBE")
print("=" * 100)
print("DATE:", DATE)
print("=" * 100)


for speaker in sorted(profiles):

    items = profiles[speaker]["segments"]

    words = sum(
        item["word_count"]
        for item in items
    )

    print()
    print("-" * 100)

    print(
        f"SPEAKER {speaker}"
    )

    print(
        f"SEGMENTS: {len(items)}"
    )

    print(
        f"WORDS: {words}"
    )

    print(
        f"QUESTION-LIKE: "
        f"{profiles[speaker]['questions']}"
    )

    print(
        f"ANSWER-LIKE:   "
        f"{profiles[speaker]['answers']}"
    )

    print()
    print("REPRESENTATIVE UTTERANCES:")

    # 짧은 것만 계속 나오는 speaker와
    # 긴 발언을 주로 하는 speaker를 구분하기 위해
    # 가장 긴 발언 3개를 보여준다.
    longest = sorted(
        items,
        key=lambda item: item["word_count"],
        reverse=True,
    )[:3]

    for item in longest:
        print()
        print(
            f"[SEG {item['segment_id']} | "
            f"{item['start_seconds']:.1f}s | "
            f"{item['word_count']} words]"
        )

        print(
            item["text"][:500]
        )


print()
print("=" * 100)
print("IMPORTANT")
print("=" * 100)
print(
    "This is a diagnostic only."
)
print(
    "It does NOT assign real identities."
)
print(
    "It does NOT create production speaker roles."
)
print("=" * 100)
