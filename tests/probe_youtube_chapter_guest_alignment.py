from __future__ import annotations

import re
from pathlib import Path


PATH = Path(
    "data/reference/youtube/2026-08-14_transcript.txt"
)

CHAPTER_PATTERN = re.compile(
    r"chapter\s+\d+:\s*(.+)",
    re.IGNORECASE,
)

GUEST_PATTERN = re.compile(
    r"—\s*([^—]+)$"
)


lines = [
    x.strip()
    for x in PATH.read_text(
        encoding="utf-8"
    ).splitlines()
    if x.strip()
]


print("=" * 100)
print("YOUTUBE CHAPTER / GUEST STRUCTURE")
print("=" * 100)

found = []

for i, line in enumerate(lines):

    match = CHAPTER_PATTERN.search(line)

    if not match:
        continue

    title = match.group(1)

    # Look backwards for the nearest timestamp.
    timestamp = None

    for previous in reversed(lines[:i]):
        if re.fullmatch(
            r"\d{1,2}:\d{2}(?::\d{2})?",
            previous,
        ):
            timestamp = previous
            break

    if timestamp is None:
        continue

    guest = None

    guest_match = GUEST_PATTERN.search(title)

    if guest_match:
        guest = guest_match.group(1).strip()

    found.append(
        {
            "timestamp": timestamp,
            "title": title,
            "guest": guest,
        }
    )


print(
    f"CHAPTERS FOUND: {len(found)}"
)

print("=" * 100)

for row in found:

    print()
    print(
        f"{row['timestamp']:>10} | "
        f"GUEST: {row['guest'] or 'NONE'}"
    )

    print(
        f"TITLE: {row['title']}"
    )


print()
print("=" * 100)
print("DONE")
print("=" * 100)
