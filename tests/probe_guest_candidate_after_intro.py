from __future__ import annotations

import json
from pathlib import Path


DATE = "2026-08-14"

PATH = (
    Path("data/processed/surveillance")
    / DATE
    / "segments.json"
)

INTRO_SEGMENTS = [4, 48, 55, 70]

LOOKAHEAD = 8
LONG_RESPONSE_WORDS = 40


payload = json.loads(
    PATH.read_text(encoding="utf-8")
)

segments = payload["segments"]


print("=" * 100)
print("GUEST CANDIDATE AFTER INTRODUCTION")
print("=" * 100)
print("DATE:", DATE)
print("=" * 100)


for intro_id in INTRO_SEGMENTS:

    intro = segments[intro_id]

    print()
    print("=" * 100)
    print(
        f"INTRO SEGMENT {intro_id}"
    )
    print(
        f"TIME: {intro['start_seconds']:.1f}s"
    )
    print(
        intro["text"]
    )
    print("=" * 100)

    candidates = []

    for j in range(
        intro_id + 1,
        min(
            intro_id + LOOKAHEAD + 1,
            len(segments),
        ),
    ):

        segment = segments[j]

        # 이후 동일 speaker가 몇 번 등장하는지 확인
        later_count = sum(
            1
            for later in segments[j + 1 :]
            if later["speaker_index"]
            == segment["speaker_index"]
        )

        candidates.append(
            {
                "segment": j,
                "speaker": segment["speaker_index"],
                "words": segment["word_count"],
                "later_occurrences": later_count,
                "text": segment["text"],
            }
        )

    # 긴 발언 + 이후 반복 등장 우선
    ranked = sorted(
        candidates,
        key=lambda row: (
            row["words"],
            row["later_occurrences"],
        ),
        reverse=True,
    )

    print()
    print("CANDIDATE SPEAKERS")
    print("-" * 100)

    for row in ranked:

        marker = ""

        if row["words"] >= LONG_RESPONSE_WORDS:
            marker = " <-- LONG RESPONSE CANDIDATE"

        print(
            f"SEG {row['segment']:3d} | "
            f"SPEAKER {row['speaker']:2d} | "
            f"WORDS {row['words']:3d} | "
            f"LATER OCCURRENCES "
            f"{row['later_occurrences']:2d}"
            f"{marker}"
        )

        print(
            f"  {row['text'][:400]}"
        )


print()
print("=" * 100)
print("INTERPRETATION")
print("=" * 100)

print(
    "This probe does not assign a guest identity."
)

print(
    "It identifies speakers after an introduction who "
    "show sustained/long-form participation."
)

print("=" * 100)
