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
CONTEXT = 2


payload = json.loads(
    PATH.read_text(encoding="utf-8")
)

segments = payload["segments"]


print("=" * 100)
print("GUEST INTRODUCTION CONTEXT PROBE")
print("=" * 100)
print("DATE:", DATE)
print("INTRO SEGMENTS:", INTRO_SEGMENTS)
print("CONTEXT:", CONTEXT, "segments before / after")
print("=" * 100)


for intro_id in INTRO_SEGMENTS:

    intro = segments[intro_id]

    start = max(
        0,
        intro_id - CONTEXT,
    )

    end = min(
        len(segments),
        intro_id + CONTEXT + 1,
    )

    print()
    print("=" * 100)
    print(
        f"INTRODUCTION EVENT @ SEGMENT {intro_id}"
    )
    print("=" * 100)

    for i in range(start, end):

        segment = segments[i]

        if i < intro_id:
            position = "BEFORE"
        elif i == intro_id:
            position = "INTRO"
        else:
            position = "AFTER"

        print()
        print(
            f"[{position:5s}] "
            f"SEGMENT {i:3d} | "
            f"{segment['start_seconds']:7.1f}s | "
            f"SPEAKER {segment['speaker_index']} | "
            f"{segment['word_count']:3d} words"
        )

        print(
            segment["text"]
        )


print()
print("=" * 100)
print("WHAT TO INSPECT")
print("=" * 100)
print("1. 이름이 INTRO 앞에 등장하는가?")
print("2. INTRO 문장 안에서 이름 + joins us가 함께 나오는가?")
print("3. INTRO 직후 다른 speaker가 등장하는가?")
print("4. INTRO 직후 'Hi / great to see you / thank you'가 나오는가?")
print("5. 다음 speaker가 이후에도 지속적으로 발언하는가?")
print("=" * 100)
