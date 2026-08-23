from __future__ import annotations

import json
import re
from pathlib import Path


DATE = "2026-08-14"

YOUTUBE = Path(
    "data/reference/youtube/2026-08-14_transcript.txt"
)

OMNY = Path(
    "data/processed/surveillance/2026-08-14/segments.json"
)


def normalize(text: str) -> str:
    return re.sub(
        r"[^a-z0-9]+",
        " ",
        text.lower(),
    ).strip()


def name_tokens(name: str) -> list[str]:
    return [
        token
        for token in normalize(name).split()
        if len(token) > 2
    ]


youtube_lines = [
    x.strip()
    for x in YOUTUBE.read_text(
        encoding="utf-8"
    ).splitlines()
    if x.strip()
]


chapter_re = re.compile(
    r"^Chapter\s+(\d+):\s*(.+)$",
    re.IGNORECASE,
)

chapters = []

for line in youtube_lines:

    match = chapter_re.match(line)

    if not match:
        continue

    title = match.group(2)

    if "—" not in title:
        continue

    guest = title.split("—", 1)[1].strip()

    chapters.append(
        {
            "chapter": int(match.group(1)),
            "guest": guest,
            "title": title,
        }
    )


payload = json.loads(
    OMNY.read_text(
        encoding="utf-8"
    )
)

segments = payload["segments"]


print("=" * 100)
print("GUEST NAME → OMNY TEXT ALIGNMENT")
print("=" * 100)

print(
    f"YOUTUBE GUEST CHAPTERS: {len(chapters)}"
)

print(
    f"OMNY SEGMENTS: {len(segments)}"
)

print("=" * 100)


for chapter in chapters:

    guest = chapter["guest"]

    # Remove organization after comma.
    person = guest.split(",", 1)[0].strip()

    tokens = name_tokens(person)

    matches = []

    for segment in segments:

        normalized = normalize(
            segment["text"]
        )

        hits = [
            token
            for token in tokens
            if token in normalized
        ]

        if hits:
            matches.append(
                (
                    len(hits),
                    segment,
                    hits,
                )
            )

    matches.sort(
        key=lambda x: (
            -x[0],
            x[1]["start_seconds"],
        )
    )

    print()
    print("-" * 100)

    print(
        f"CHAPTER {chapter['chapter']}"
    )

    print(
        "GUEST:",
        guest
    )

    if not matches:
        print(
            "RESULT: NO TEXT MATCH"
        )
        continue

    best_score, best, hits = matches[0]

    print(
        f"RESULT: MATCH "
        f"({best_score}/{len(tokens)} name tokens)"
    )

    print(
        f"OMNY SEGMENT: "
        f"{best['segment_id']}"
    )

    print(
        f"OMNY TIME: "
        f"{best['start_seconds']:.1f}s"
    )

    print(
        "NAME HITS:",
        hits
    )

    print(
        "TEXT:",
        best["text"][:500]
    )


print()
print("=" * 100)
print("DONE")
print("=" * 100)
