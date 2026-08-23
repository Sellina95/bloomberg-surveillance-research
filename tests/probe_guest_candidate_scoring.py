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

LOOKAHEAD = 12


payload = json.loads(
    PATH.read_text(encoding="utf-8")
)

segments = payload["segments"]


def score_candidate(
    speaker: int,
    intro_id: int,
) -> dict:

    window = segments[
        intro_id + 1:
        min(
            intro_id + LOOKAHEAD + 1,
            len(segments),
        )
    ]

    speaker_segments = [
        segment
        for segment in window
        if segment["speaker_index"] == speaker
    ]

    long_segments = [
        segment
        for segment in speaker_segments
        if segment["word_count"] >= 40
    ]

    total_words = sum(
        segment["word_count"]
        for segment in speaker_segments
    )

    # 보수적인 diagnostic score.
    score = 0

    if len(long_segments) >= 1:
        score += 1

    if len(long_segments) >= 2:
        score += 1

    if len(speaker_segments) >= 3:
        score += 1

    if total_words >= 120:
        score += 1

    return {
        "speaker": speaker,
        "segments": len(speaker_segments),
        "long_segments": len(long_segments),
        "total_words": total_words,
        "score": score,
    }


print("=" * 100)
print("GUEST CANDIDATE SCORING PROBE")
print("=" * 100)
print("DATE:", DATE)
print("=" * 100)


for intro_id in INTRO_SEGMENTS:

    intro = segments[intro_id]

    print()
    print("-" * 100)
    print(
        f"INTRO SEGMENT {intro_id} "
        f"[{intro['start_seconds']:.1f}s]"
    )
    print(
        intro["text"][:500]
    )
    print("-" * 100)

    speaker_ids = sorted(
        {
            segment["speaker_index"]
            for segment in segments[
                intro_id + 1:
                min(
                    intro_id + LOOKAHEAD + 1,
                    len(segments),
                )
            ]
        }
    )

    results = [
        score_candidate(
            speaker,
            intro_id,
        )
        for speaker in speaker_ids
    ]

    results.sort(
        key=lambda row: (
            row["score"],
            row["long_segments"],
            row["total_words"],
        ),
        reverse=True,
    )

    for result in results:

        print(
            f"SPEAKER {result['speaker']:2d} | "
            f"SCORE {result['score']} | "
            f"SEGMENTS {result['segments']:2d} | "
            f"LONG {result['long_segments']:2d} | "
            f"WORDS {result['total_words']:3d}"
        )


print()
print("=" * 100)
print("INTERPRETATION")
print("=" * 100)
print(
    "Score is diagnostic only."
)
print(
    "No speaker identity is automatically assigned."
)
print(
    "A high score means the speaker behaves like a sustained "
    "post-introduction participant."
)
print("=" * 100)
