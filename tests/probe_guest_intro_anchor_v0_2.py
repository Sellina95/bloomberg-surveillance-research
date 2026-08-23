from __future__ import annotations

import json
import re
from pathlib import Path


PATH = Path(
    "data/processed/surveillance/2026-08-14/youtube_transcript.json"
)

LOOKBACK = 120

START_PATTERNS = [
    "joins us now",
    "joins us",
    "joining us",
    "great to see you",
    "welcome to the program",
    "thank you for being here",
]

data = json.loads(
    PATH.read_text(encoding="utf-8")
)

segments = data["segments"]


def normalize(text: str) -> str:
    return re.sub(
        r"[^a-z0-9 ]+",
        " ",
        text.lower(),
    )


def name_tokens(guest: str) -> list[str]:
    # "Michael McKee, Bloomberg" -> ["michael", "mckee"]
    name = guest.split(",", 1)[0]

    return [
        token
        for token in normalize(name).split()
        if len(token) >= 3
    ]


print("=" * 100)
print("GUEST INTRO ANCHOR PROBE v0.2")
print("=" * 100)

guest_chapters = [
    c
    for c in data["chapters"]
    if c.get("guest")
]


for chapter in guest_chapters:

    chapter_start = chapter["start_seconds"]

    lower = max(
        0,
        chapter_start - LOOKBACK,
    )

    guest = chapter["guest"]

    tokens = name_tokens(guest)

    candidates = [
        row
        for row in segments
        if lower <= row["start_seconds"] <= chapter_start + 30
    ]

    scored = []

    for row in candidates:

        text = normalize(row["text"])

        score = 0
        signals = []

        # Guest name
        name_hits = sum(
            1
            for token in tokens
            if token in text
        )

        if name_hits:
            score += 5 * name_hits
            signals.append(
                f"NAME:{name_hits}"
            )

        # Introduction language
        for pattern in START_PATTERNS:

            if pattern in text:
                score += 3
                signals.append(
                    f"PHRASE:{pattern}"
                )

        if score > 0:
            scored.append(
                (
                    score,
                    row,
                    signals,
                )
            )

    scored.sort(
        key=lambda x: (
            x[1]["start_seconds"],
            -x[0],
        )
    )

    print()
    print("-" * 100)

    print(
        f"CHAPTER {chapter['chapter']:02d}"
    )

    print(
        f"GUEST: {guest}"
    )

    print(
        f"CHAPTER START: "
        f"{chapter_start:.2f}s"
    )

    print(
        f"LOOKBACK: "
        f"{lower:.2f}s"
    )

    print()

    if not scored:
        print("NO INTRO ANCHOR FOUND")
        continue

    print("CANDIDATE ANCHORS:")

    # Show highest quality candidates,
    # preserving chronological order.
    for score, row, signals in scored[-10:]:

        print()
        print(
            f"SCORE {score:2d} | "
            f"{row['start_seconds']:8.2f}s | "
            f"{signals}"
        )

        print(
            row["text"][:700]
        )


print()
print("=" * 100)
print("DONE")
print("=" * 100)
