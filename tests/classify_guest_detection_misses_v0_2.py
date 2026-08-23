from __future__ import annotations

import json
import re
from pathlib import Path


BASE = Path(
    "data/processed/surveillance/2026-08-14"
)

DETECTION = BASE / "guest_detection_v0_1.json"
TRANSCRIPT = BASE / "youtube_transcript.json"

data = json.loads(
    DETECTION.read_text(encoding="utf-8")
)

transcript = json.loads(
    TRANSCRIPT.read_text(encoding="utf-8")
)

segments = transcript["segments"]


def normalize(text: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        text.lower()
    ).strip()


START_PATTERNS = [
    "joins us",
    "joining us",
    "welcome to the program",
    "great to see you",
    "thank you for being here",
]

END_PATTERNS = [
    "thank you so much",
    "thank you for joining us",
    "thanks for having me",
    "stay with us",
]


def find_patterns(start: float, end: float, patterns):
    hits = []

    for s in segments:
        if not (
            start <= s["start_seconds"] <= end
        ):
            continue

        text = normalize(s["text"])

        found = [
            p for p in patterns
            if p in text
        ]

        if found:
            hits.append(
                {
                    "time": s["start_seconds"],
                    "signals": found,
                    "text": text,
                }
            )

    return hits


print("=" * 100)
print("GUEST DETECTION MISS CLASSIFICATION v0.2")
print("=" * 100)

misses = [
    x
    for x in data["matches"]
    if x["detected_start"] is None
]

results = []

for row in misses:

    chapter = row["chapter"]
    guest = row["guest"]
    chapter_start = row["chapter_start"]

    # --------------------------------------------------------
    # Search before chapter.
    # --------------------------------------------------------

    pre_start = max(
        0,
        chapter_start - 180
    )

    pre_end = chapter_start

    pre_segments = [
        s for s in segments
        if pre_start
        <= s["start_seconds"]
        < pre_end
    ]

    # --------------------------------------------------------
    # Search introduction signals.
    # --------------------------------------------------------

    intro_hits = find_patterns(
        pre_start,
        chapter_start + 30,
        START_PATTERNS,
    )

    # --------------------------------------------------------
    # Determine whether transcript is already in
    # guest-style dialogue before Chapter.
    #
    # We use speaker markers as a weak structural signal.
    # --------------------------------------------------------

    speaker_like = []

    for s in pre_segments:

        text = s["text"].strip()

        if re.match(
            r"^(?:>>\s*)?[A-Z][A-Z ]{1,20}:",
            text
        ):
            speaker_like.append(s)

    # --------------------------------------------------------
    # Classification
    # --------------------------------------------------------

    if intro_hits:

        earliest_intro = min(
            x["time"]
            for x in intro_hits
        )

        classification = (
            "INTRO_BEFORE_CHAPTER"
        )

        evidence = (
            f"intro at "
            f"{earliest_intro:.2f}s"
        )

    elif len(pre_segments) >= 8:

        classification = (
            "GUEST_DIALOGUE_ALREADY_ACTIVE"
        )

        evidence = (
            f"{len(pre_segments)} transcript "
            f"segments before chapter"
        )

    else:

        classification = (
            "NO_CLEAR_SIGNAL"
        )

        evidence = (
            "no intro signal / insufficient "
            "pre-chapter dialogue"
        )

    result = {
        "chapter": chapter,
        "guest": guest,
        "chapter_start": chapter_start,
        "classification": classification,
        "evidence": evidence,
        "intro_hits": intro_hits,
        "speaker_like_count":
            len(speaker_like),
    }

    results.append(result)

    print(
        f"CH{chapter:02d} | "
        f"{classification:32s} | "
        f"{guest}"
    )

    print(
        f"       {evidence}"
    )


# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------

from collections import Counter

counts = Counter(
    x["classification"]
    for x in results
)

print()
print("=" * 100)
print("SUMMARY")
print("=" * 100)

for key, value in counts.items():
    print(
        f"{key}: {value}"
    )

print(
    f"TOTAL MISSES: {len(results)}"
)

print("=" * 100)


OUTPUT = BASE / (
    "guest_detection_miss_classification_v0_2.json"
)

OUTPUT.write_text(
    json.dumps(
        results,
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

print(
    "ARTIFACT:",
    OUTPUT
)

print(
    "MISS CLASSIFICATION COMPLETE"
)
