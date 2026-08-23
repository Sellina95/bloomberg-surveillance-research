from __future__ import annotations

import json
import re
from pathlib import Path


PATH = Path(
    "data/processed/surveillance/2026-08-14/youtube_transcript.json"
)

OUTPUT = Path(
    "data/processed/surveillance/2026-08-14/"
    "guest_detection_v0_1.json"
)

# ------------------------------------------------------------
# Research parameters
# ------------------------------------------------------------

LOOKBACK = 180
LOOKAHEAD = 120

START_PATTERNS = [
    "joins us now",
    "joins us",
    "joining us",
    "welcome to the program",
    "welcome to the programme",
    "great to see you",
    "thank you for being here",
    "thank you for joining us",
]

END_PATTERNS = [
    "thank you so much",
    "thank you for joining us",
    "thanks for having me",
    "thank you for being here",
    "stay with us",
    "coming up next",
    "have a wonderful weekend",
]

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------


def normalize(text: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        text.lower(),
    ).strip()


def pattern_hits(
    text: str,
    patterns: list[str],
) -> list[str]:

    text = normalize(text)

    return [
        pattern
        for pattern in patterns
        if pattern in text
    ]


def words(text: str) -> int:
    return len(
        normalize(text).split()
    )


# ------------------------------------------------------------
# Load canonical transcript
# ------------------------------------------------------------

data = json.loads(
    PATH.read_text(
        encoding="utf-8"
    )
)

segments = data["segments"]
chapters = data["chapters"]


# ------------------------------------------------------------
# Detect candidate guest units
#
# IMPORTANT:
# Chapter metadata is NOT used to detect boundaries.
# It is only used later for validation.
# ------------------------------------------------------------

candidates = []


for i, segment in enumerate(segments):

    text = segment["text"]

    start_hits = pattern_hits(
        text,
        START_PATTERNS,
    )

    if not start_hits:
        continue

    start_time = segment["start_seconds"]

    # --------------------------------------------------------
    # Look forward for sustained speech.
    # --------------------------------------------------------

    following = [
        s
        for s in segments
        if (
            s["start_seconds"] >= start_time
            and s["start_seconds"]
            <= start_time + LOOKAHEAD
        )
    ]

    if not following:
        continue

    total_words = sum(
        words(s["text"])
        for s in following
    )

    duration = (
        following[-1]["end_seconds"]
        - start_time
    )

    # Sustained transcript after introduction.
    sustained = (
        total_words >= 80
        and duration >= 30
    )

    score = 0

    score += 3

    if sustained:
        score += 3

    if total_words >= 150:
        score += 1

    candidates.append(
        {
            "start_segment":
                segment["segment_id"],
            "start_seconds":
                start_time,
            "start_text":
                text,
            "start_signals":
                start_hits,
            "lookahead_words":
                total_words,
            "lookahead_duration":
                duration,
            "sustained":
                sustained,
            "score":
                score,
        }
    )


# ------------------------------------------------------------
# Detect possible end signals
# ------------------------------------------------------------

for candidate in candidates:

    start_time = candidate[
        "start_seconds"
    ]

    end_candidates = []

    for segment in segments:

        if segment["start_seconds"] <= start_time:
            continue

        if segment["start_seconds"] > (
            start_time + 900
        ):
            break

        hits = pattern_hits(
            segment["text"],
            END_PATTERNS,
        )

        if hits:

            end_candidates.append(
                {
                    "segment_id":
                        segment["segment_id"],
                    "start_seconds":
                        segment["start_seconds"],
                    "text":
                        segment["text"],
                    "signals":
                        hits,
                }
            )

    candidate["end_candidates"] = (
        end_candidates[:5]
    )


# ------------------------------------------------------------
# Deduplicate nearby intro signals
#
# Multiple phrases can occur in the same introduction.
# Keep the highest-scoring candidate in a 30-second cluster.
# ------------------------------------------------------------

candidates.sort(
    key=lambda x: x["start_seconds"]
)

deduped = []

for candidate in candidates:

    if not deduped:

        deduped.append(candidate)
        continue

    previous = deduped[-1]

    if (
        candidate["start_seconds"]
        - previous["start_seconds"]
        <= 30
    ):

        if candidate["score"] > previous["score"]:
            deduped[-1] = candidate

    else:

        deduped.append(candidate)


# ------------------------------------------------------------
# Validation against YouTube Chapter ground truth
#
# Chapter data is NOT used by detector.
# It is only used after detection.
# ------------------------------------------------------------

guest_chapters = [
    chapter
    for chapter in chapters
    if chapter.get("guest")
]

matched = []

TOLERANCE = 180


for chapter in guest_chapters:

    chapter_start = chapter[
        "start_seconds"
    ]

    nearby = [
        candidate
        for candidate in deduped
        if abs(
            candidate["start_seconds"]
            - chapter_start
        ) <= TOLERANCE
    ]

    if nearby:

        best = min(
            nearby,
            key=lambda x: abs(
                x["start_seconds"]
                - chapter_start
            ),
        )

        matched.append(
            {
                "chapter":
                    chapter["chapter"],
                "guest":
                    chapter["guest"],
                "chapter_start":
                    chapter_start,
                "detected_start":
                    best["start_seconds"],
                "difference_seconds":
                    abs(
                        best["start_seconds"]
                        - chapter_start
                    ),
                "score":
                    best["score"],
                "signals":
                    best["start_signals"],
            }
        )

    else:

        matched.append(
            {
                "chapter":
                    chapter["chapter"],
                "guest":
                    chapter["guest"],
                "chapter_start":
                    chapter_start,
                "detected_start":
                    None,
                "difference_seconds":
                    None,
                "score":
                    None,
                "signals":
                    [],
            }
        )


# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------

matches = [
    row
    for row in matched
    if row["detected_start"] is not None
]

print("=" * 100)
print("GUEST DETECTION v0.1")
print("=" * 100)

print(
    "TRANSCRIPT SEGMENTS:",
    len(segments),
)

print(
    "GROUND-TRUTH GUEST CHAPTERS:",
    len(guest_chapters),
)

print(
    "RAW START CANDIDATES:",
    len(candidates),
)

print(
    "DEDUPED CANDIDATES:",
    len(deduped),
)

print()
print("-" * 100)
print("GROUND-TRUTH COMPARISON")
print("-" * 100)

for row in matched:

    status = (
        "MATCH"
        if row["detected_start"] is not None
        else "MISS"
    )

    print(
        f"{status:5s} | "
        f"CHAPTER {row['chapter']:02d} | "
        f"{row['guest']}"
    )

    print(
        f"       "
        f"CHAPTER={row['chapter_start']:.2f}s | "
        f"DETECTED="
        f"{row['detected_start']}"
    )

    if row["difference_seconds"] is not None:

        print(
            f"       "
            f"DIFF="
            f"{row['difference_seconds']:.2f}s | "
            f"SCORE={row['score']}"
        )

        print(
            f"       SIGNALS="
            f"{row['signals']}"
        )


print()
print("=" * 100)

print(
    f"MATCHED: {len(matches)}/{len(guest_chapters)}"
)

if guest_chapters:

    recall = (
        len(matches)
        / len(guest_chapters)
    )

    print(
        f"RECALL: {recall:.2%}"
    )

print("=" * 100)


# ------------------------------------------------------------
# Save artifact
# ------------------------------------------------------------

artifact = {
    "date": "2026-08-14",
    "method": "guest_detection_v0_1",
    "parameters": {
        "lookback_seconds": LOOKBACK,
        "lookahead_seconds": LOOKAHEAD,
        "tolerance_seconds": TOLERANCE,
    },
    "candidate_count":
        len(deduped),
    "ground_truth_guest_chapters":
        len(guest_chapters),
    "matches":
        matched,
    "candidates":
        deduped,
}

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT.write_text(
    json.dumps(
        artifact,
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

print()
print("ARTIFACT:")
print(OUTPUT)
print()
print("GUEST DETECTION v0.1 COMPLETE")
