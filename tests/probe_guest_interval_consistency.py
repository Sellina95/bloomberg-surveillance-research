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


payload = json.loads(
    PATH.read_text(encoding="utf-8")
)

segments = payload["segments"]


def is_transition_end(text: str) -> bool:
    text = text.lower()

    patterns = [
        "stay with us",
        "coming up after",
        "more bloomberg surveillance coming up",
        "thank you so much",
        "thanks for having me",
    ]

    return any(
        pattern in text
        for pattern in patterns
    )


print("=" * 100)
print("GUEST INTERVAL CONSISTENCY CHECK")
print("=" * 100)
print("DATE:", DATE)
print("INTRO SEGMENTS:", INTRO_SEGMENTS)
print("=" * 100)


for intro in INTRO_SEGMENTS:

    intro_segment = segments[intro]

    print()
    print("-" * 100)

    print(
        f"INTRO SEGMENT: {intro}"
    )

    print(
        f"TIME: "
        f"{intro_segment['start_seconds']:.1f}s"
    )

    print(
        f"SPEAKER: "
        f"{intro_segment['speaker_index']}"
    )

    print(
        "INTRO:",
        intro_segment["text"][:300],
    )

    end_segment = None

    for segment in segments[intro + 1:]:

        if is_transition_end(
            segment["text"]
        ):
            end_segment = segment
            break

    if end_segment is None:

        print(
            "END: NOT FOUND"
        )

        continue

    print(
        f"END SEGMENT: "
        f"{end_segment['segment_id']}"
    )

    print(
        f"END TIME: "
        f"{end_segment['start_seconds']:.1f}s"
    )

    duration = (
        end_segment["start_seconds"]
        - intro_segment["start_seconds"]
    )

    print(
        f"DURATION: "
        f"{duration:.1f}s"
    )

    print(
        "END SIGNAL:",
        end_segment["text"][:250],
    )


print()
print("=" * 100)
print("CONSISTENCY CHECK COMPLETE")
print("=" * 100)
