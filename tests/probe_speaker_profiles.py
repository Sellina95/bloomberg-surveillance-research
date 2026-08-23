from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


DATE = "2026-08-14"

PATH = (
    Path("data/processed/surveillance")
    / DATE
    / "segments.json"
)


payload = json.loads(
    PATH.read_text(encoding="utf-8")
)

segments = payload["segments"]


profiles = defaultdict(
    lambda: {
        "segments": 0,
        "words": 0,
        "first_segment": None,
        "last_segment": None,
        "times": [],
        "examples": [],
    }
)


for segment in segments:
    speaker = segment["speaker_index"]

    profile = profiles[speaker]

    profile["segments"] += 1
    profile["words"] += segment["word_count"]

    if profile["first_segment"] is None:
        profile["first_segment"] = segment["segment_id"]

    profile["last_segment"] = segment["segment_id"]

    profile["times"].append(
        segment["start_seconds"]
    )

    if len(profile["examples"]) < 3:
        profile["examples"].append(
            segment["text"]
        )


print("=" * 100)
print("SPEAKER PROFILE PROBE")
print("=" * 100)
print("DATE:", DATE)
print("TOTAL SEGMENTS:", len(segments))
print("=" * 100)


for speaker in sorted(profiles):
    profile = profiles[speaker]

    duration_start = min(profile["times"])
    duration_end = max(profile["times"])

    print()
    print("-" * 100)

    print(
        f"SPEAKER INDEX: {speaker}"
    )

    print(
        f"SEGMENTS:       {profile['segments']}"
    )

    print(
        f"WORDS:          {profile['words']}"
    )

    print(
        f"FIRST SEGMENT:  {profile['first_segment']}"
    )

    print(
        f"LAST SEGMENT:   {profile['last_segment']}"
    )

    print(
        f"TIME RANGE:     "
        f"{duration_start:.1f}s → "
        f"{duration_end:.1f}s"
    )

    print()
    print("EXAMPLES:")

    for example in profile["examples"]:
        print(
            f"  - {example[:300]}"
        )


print()
print("=" * 100)
print("FIRST 30 SPEAKER TRANSITIONS")
print("=" * 100)

previous = None

for segment in segments:
    speaker = segment["speaker_index"]

    if speaker != previous:
        print(
            f"SEGMENT {segment['segment_id']:3d} | "
            f"{segment['start_seconds']:7.1f}s | "
            f"SPEAKER {speaker}"
        )

        previous = speaker

print("=" * 100)
