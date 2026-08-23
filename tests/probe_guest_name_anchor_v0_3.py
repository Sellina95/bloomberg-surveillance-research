from __future__ import annotations

import json
import re
from pathlib import Path


PATH = Path(
    "data/processed/surveillance/2026-08-14/youtube_transcript.json"
)

LOOKBACK = 180


def normalize(text: str) -> str:
    return re.sub(
        r"[^a-z0-9 ]+",
        " ",
        text.lower(),
    )


def tokens(guest: str) -> list[str]:
    name = guest.split(",", 1)[0]

    return [
        x
        for x in normalize(name).split()
        if len(x) >= 3
    ]


data = json.loads(
    PATH.read_text(encoding="utf-8")
)

segments = data["segments"]

print("=" * 100)
print("GUEST NAME ANCHOR PROBE v0.3")
print("=" * 100)

for chapter in data["chapters"]:

    guest = chapter.get("guest")

    if not guest:
        continue

    start = chapter["start_seconds"]
    lower = max(0, start - LOOKBACK)

    name_tokens = tokens(guest)

    candidates = []

    for row in segments:

        if not (
            lower
            <= row["start_seconds"]
            <= start + 30
        ):
            continue

        text = normalize(row["text"])

        hits = [
            token
            for token in name_tokens
            if re.search(
                rf"\b{re.escape(token)}\b",
                text,
            )
        ]

        if hits:

            candidates.append(
                (
                    row,
                    hits,
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
        f"CHAPTER START: {start:.2f}s"
    )

    print(
        f"SEARCH WINDOW: "
        f"{lower:.2f}s → {start + 30:.2f}s"
    )

    if not candidates:

        print("NAME ANCHOR: NONE")
        continue

    print(
        f"NAME ANCHORS: {len(candidates)}"
    )

    for row, hits in candidates:

        print()
        print(
            f"{row['start_seconds']:8.2f}s | "
            f"HITS={hits}"
        )

        print(
            row["text"][:700]
        )


print()
print("=" * 100)
print("DONE")
print("=" * 100)
