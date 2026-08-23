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


profiles = defaultdict(list)

for segment in segments:
    profiles[segment["speaker_index"]].append(segment)


print("=" * 100)
print("SPEAKER DIARIZATION CONSISTENCY PROBE")
print("=" * 100)
print("DATE:", DATE)
print("TOTAL SEGMENTS:", len(segments))
print("SPEAKER IDS:", sorted(profiles))
print("=" * 100)


for speaker in sorted(profiles):

    items = profiles[speaker]

    total_words = sum(
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
        f"WORDS:    {total_words}"
    )

    print(
        f"FIRST:    "
        f"{items[0]['start_seconds']:.1f}s"
    )

    print(
        f"LAST:     "
        f"{items[-1]['start_seconds']:.1f}s"
    )

    print()
    print("SPEAKER OCCURRENCES:")

    print(
        " ".join(
            str(item["segment_id"])
            for item in items
        )
    )


print()
print("=" * 100)
print("LOCAL SPEAKER CONTINUITY")
print("=" * 100)

previous_speaker = None

runs = []
current_run = []

for segment in segments:

    speaker = segment["speaker_index"]

    if speaker != previous_speaker:

        if current_run:
            runs.append(current_run)

        current_run = [segment]

        previous_speaker = speaker

    else:
        current_run.append(segment)

if current_run:
    runs.append(current_run)


for run in runs:

    speaker = run[0]["speaker_index"]

    start = run[0]["start_seconds"]
    end = run[-1]["end_seconds"]

    words = sum(
        item["word_count"]
        for item in run
    )

    print(
        f"SPEAKER {speaker:2d} | "
        f"SEGMENTS {run[0]['segment_id']:3d}"
        f"→{run[-1]['segment_id']:3d} | "
        f"{start:7.1f}s → {end:7.1f}s | "
        f"{words:4d} words"
    )


print()
print("=" * 100)
print("PAIRWISE SPEAKER TRANSITIONS")
print("=" * 100)

transitions = defaultdict(int)

for previous, current in zip(
    segments,
    segments[1:],
):

    left = previous["speaker_index"]
    right = current["speaker_index"]

    if left == right:
        continue

    transitions[(left, right)] += 1


for (left, right), count in sorted(
    transitions.items(),
    key=lambda item: item[1],
    reverse=True,
):

    print(
        f"SPEAKER {left} → SPEAKER {right}: "
        f"{count} times"
    )


print()
print("=" * 100)
print("CONCLUSION")
print("=" * 100)

print(
    "This probe evaluates stability of the existing "
    "speaker_index diarization."
)

print(
    "It does NOT claim that speaker_index maps to a real person's name."
)

print(
    "AUDIO-LEVEL IDENTITY VERIFICATION requires access "
    "to the original audio stream."
)

print("=" * 100)
