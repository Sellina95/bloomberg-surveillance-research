from __future__ import annotations

import re
from pathlib import Path


PATH = Path(
    "data/reference/youtube/2026-08-14_transcript.txt"
)

lines = [
    x.strip()
    for x in PATH.read_text(
        encoding="utf-8"
    ).splitlines()
    if x.strip()
]

TIMESTAMP = re.compile(
    r"^\d{1,2}:\d{2}(?::\d{2})?$"
)

CHAPTER = re.compile(
    r"^Chapter\s+(\d+):\s*(.+)$",
    re.IGNORECASE,
)


def to_seconds(value: str) -> int:
    parts = [int(x) for x in value.split(":")]

    if len(parts) == 2:
        return parts[0] * 60 + parts[1]

    return (
        parts[0] * 3600
        + parts[1] * 60
        + parts[2]
    )


chapters = []

for i, line in enumerate(lines):

    match = CHAPTER.match(line)

    if not match:
        continue

    # Find nearest timestamp AFTER the chapter title.
    timestamp = None

    for j in range(i + 1, min(i + 8, len(lines))):

        if TIMESTAMP.match(lines[j]):
            timestamp = lines[j]
            break

    if timestamp is None:
        continue

    title = match.group(2)

    guest = None

    # Most guest chapters use:
    # "... — Guest, Organization"
    if "—" in title:
        guest = title.split("—", 1)[1].strip()

    chapters.append(
        {
            "chapter": int(match.group(1)),
            "timestamp": timestamp,
            "seconds": to_seconds(timestamp),
            "title": title,
            "guest": guest,
        }
    )


print("=" * 100)
print("YOUTUBE CHAPTER → GUEST UNIT VALIDATION")
print("=" * 100)
print(
    f"CHAPTERS FOUND: {len(chapters)}"
)
print("=" * 100)


for row in chapters:

    print()
    print(
        f"CHAPTER {row['chapter']:2d} | "
        f"{row['timestamp']:>8} | "
        f"{row['seconds']:6d}s"
    )

    print(
        f"TITLE: {row['title']}"
    )

    print(
        f"GUEST: {row['guest'] or 'NONE'}"
    )


print()
print("=" * 100)
print("GUEST CHAPTER COUNT")
print("=" * 100)

guest_chapters = [
    row
    for row in chapters
    if row["guest"]
]

print(
    "GUEST CHAPTERS:",
    len(guest_chapters)
)

print(
    "NON-GUEST CHAPTERS:",
    len(chapters) - len(guest_chapters)
)

print()
print("=" * 100)
print("VALIDATION")
print("=" * 100)

if guest_chapters:
    print("PASS — YouTube Chapters expose explicit guest metadata.")
else:
    print("FAIL — No guest metadata detected.")

print("=" * 100)
