from __future__ import annotations

import json
import re
from pathlib import Path
from collections import Counter


YOUTUBE = Path(
    "data/reference/youtube/2026-08-14_transcript.txt"
)

OMNY = Path(
    "data/processed/surveillance/2026-08-14/segments.json"
)


def tokenize(text: str) -> set[str]:
    words = re.findall(
        r"[a-zA-Z][a-zA-Z'-]+",
        text.lower(),
    )

    stop = {
        "the", "and", "that", "this", "with",
        "from", "have", "been", "they", "will",
        "would", "what", "about", "there",
        "just", "into", "were", "your", "their",
        "you", "for", "are", "has", "not",
    }

    return {
        word
        for word in words
        if word not in stop
        and len(word) > 3
    }


def overlap(left: str, right: str) -> float:

    a = tokenize(left)
    b = tokenize(right)

    if not a or not b:
        return 0.0

    return len(a & b) / len(a | b)


lines = [
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

for i, line in enumerate(lines):

    match = chapter_re.match(line)

    if not match:
        continue

    chapter = int(match.group(1))
    title = match.group(2)

    # Text after chapter title until next chapter.
    body = []

    for j in range(i + 1, len(lines)):

        if chapter_re.match(lines[j]):
            break

        body.append(lines[j])

    chapters.append(
        {
            "chapter": chapter,
            "title": title,
            "text": " ".join(body),
        }
    )


payload = json.loads(
    OMNY.read_text(
        encoding="utf-8"
    )
)

segments = payload["segments"]


print("=" * 100)
print("YOUTUBE ↔ OMNY CONTENT ALIGNMENT")
print("=" * 100)

print(
    "Goal: identify which YouTube chapter contains the "
    "current Omny transcript window."
)

print("=" * 100)


# Build a single text window from the current Omny transcript.
omny_text = " ".join(
    segment["text"]
    for segment in segments
)


results = []

for chapter in chapters:

    score = overlap(
        omny_text,
        chapter["text"],
    )

    results.append(
        {
            "chapter": chapter["chapter"],
            "title": chapter["title"],
            "score": score,
        }
    )


results.sort(
    key=lambda row: row["score"],
    reverse=True,
)


for row in results:

    print(
        f"{row['score']:.4f} | "
        f"CHAPTER {row['chapter']:2d} | "
        f"{row['title']}"
    )


print()
print("=" * 100)
print("TOP CONTENT MATCH")
print("=" * 100)

for row in results[:5]:

    print()
    print(
        f"SCORE: {row['score']:.4f}"
    )

    print(
        f"CHAPTER: {row['chapter']}"
    )

    print(
        f"TITLE: {row['title']}"
    )


print()
print("=" * 100)
print("DONE")
print("=" * 100)
