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


QUESTION_PATTERNS = [
    "what do you",
    "how do you",
    "how would you",
    "why do you",
    "what is",
    "what's",
    "do you think",
    "can you",
    "could you",
    "where do you",
    "what are",
]


def tokenize(text: str) -> list[str]:
    return re.findall(
        r"[a-zA-Z][a-zA-Z'-]+",
        text.lower(),
    )


def question_signal(text: str) -> bool:
    lower = text.lower()

    if "?" in text:
        return True

    return any(
        phrase in lower
        for phrase in QUESTION_PATTERNS
    )


payload = json.loads(
    PATH.read_text(encoding="utf-8")
)

segments = payload["segments"]


profiles = defaultdict(
    lambda: {
        "segments": 0,
        "words": 0,
        "questions": 0,
        "long_segments": 0,
        "short_segments": 0,
        "examples": [],
    }
)


for segment in segments:
    speaker = segment["speaker_index"]
    text = segment["text"]

    words = len(tokenize(text))

    profile = profiles[speaker]

    profile["segments"] += 1
    profile["words"] += words

    if question_signal(text):
        profile["questions"] += 1

    if words >= 50:
        profile["long_segments"] += 1

    if words <= 5:
        profile["short_segments"] += 1

    if len(profile["examples"]) < 3:
        profile["examples"].append(
            segment
        )


print("=" * 100)
print("HOST / GUEST STRUCTURE PROBE")
print("=" * 100)
print("DATE:", DATE)
print("TOTAL SEGMENTS:", len(segments))
print("=" * 100)


print()
print(
    "SPEAKER STATISTICS"
)

print("-" * 100)

for speaker in sorted(profiles):

    p = profiles[speaker]

    avg_words = (
        p["words"] / p["segments"]
        if p["segments"]
        else 0
    )

    print()
    print(
        f"SPEAKER {speaker}"
    )

    print(
        f"  segments:       {p['segments']}"
    )

    print(
        f"  total words:     {p['words']}"
    )

    print(
        f"  avg words:       {avg_words:.1f}"
    )

    print(
        f"  question-like:   {p['questions']}"
    )

    print(
        f"  long >=50 words: {p['long_segments']}"
    )

    print(
        f"  short <=5 words: {p['short_segments']}"
    )


print()
print("=" * 100)
print("QUESTION EXAMPLES BY SPEAKER")
print("=" * 100)


for speaker in sorted(profiles):

    questions = [
        segment
        for segment in segments
        if segment["speaker_index"] == speaker
        and question_signal(segment["text"])
    ]

    if not questions:
        continue

    print()
    print(
        f"SPEAKER {speaker} "
        f"— {len(questions)} question-like segments"
    )

    for segment in questions[:5]:

        print(
            f"[SEG {segment['segment_id']} | "
            f"{segment['start_seconds']:.1f}s]"
        )

        print(
            segment["text"][:400]
        )

        print()


print("=" * 100)
print("LONG ANSWER-LIKE SEGMENTS")
print("=" * 100)


for speaker in sorted(profiles):

    long_segments = [
        segment
        for segment in segments
        if segment["speaker_index"] == speaker
        and segment["word_count"] >= 80
    ]

    if not long_segments:
        continue

    print()
    print(
        f"SPEAKER {speaker} "
        f"— {len(long_segments)} segments >=80 words"
    )

    for segment in long_segments[:3]:

        print(
            f"[SEG {segment['segment_id']} | "
            f"{segment['start_seconds']:.1f}s | "
            f"{segment['word_count']} words]"
        )

        print(
            segment["text"][:500]
        )

        print()


print("=" * 100)
print("INTERVIEW EXAMPLE: FIRST 20 SEGMENTS")
print("=" * 100)

for segment in segments[:20]:

    print(
        f"SEG {segment['segment_id']:3d} | "
        f"{segment['start_seconds']:7.1f}s | "
        f"SPEAKER {segment['speaker_index']} | "
        f"{segment['word_count']:3d} words"
    )

    print(
        f"  {segment['text'][:220]}"
    )

print("=" * 100)
