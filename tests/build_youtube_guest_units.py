from __future__ import annotations

import json
import re
from pathlib import Path


INPUT = Path(
    "data/reference/youtube/2026-08-14_transcript.txt"
)

OUTPUT = Path(
    "data/processed/surveillance/2026-08-14/youtube_guest_units.json"
)

TIMESTAMP_RE = re.compile(
    r"^\d{1,2}:\d{2}(?::\d{2})?$"
)

CHAPTER_RE = re.compile(
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


def find_timestamp(lines: list[str], start: int) -> str | None:
    for i in range(start, min(start + 8, len(lines))):
        if TIMESTAMP_RE.match(lines[i]):
            return lines[i]
    return None


lines = [
    line.strip()
    for line in INPUT.read_text(
        encoding="utf-8"
    ).splitlines()
    if line.strip()
]


# ------------------------------------------------------------
# 1. Parse YouTube chapters
# ------------------------------------------------------------

chapters = []

for i, line in enumerate(lines):

    match = CHAPTER_RE.match(line)

    if not match:
        continue

    chapter_number = int(match.group(1))
    title = match.group(2)

    timestamp = find_timestamp(
        lines,
        i + 1,
    )

    if timestamp is None:
        continue

    guest = None

    if "—" in title:
        guest = title.split(
            "—",
            1,
        )[1].strip()

    chapters.append(
        {
            "chapter": chapter_number,
            "title": title,
            "start_timestamp": timestamp,
            "start_seconds": to_seconds(timestamp),
            "guest": guest,
        }
    )


# ------------------------------------------------------------
# 2. Use next chapter as deterministic end boundary
# ------------------------------------------------------------

guest_units = []

for i, chapter in enumerate(chapters):

    if chapter["guest"] is None:
        continue

    next_chapter = (
        chapters[i + 1]
        if i + 1 < len(chapters)
        else None
    )

    end_seconds = (
        next_chapter["start_seconds"]
        if next_chapter
        else None
    )

    end_timestamp = (
        next_chapter["start_timestamp"]
        if next_chapter
        else None
    )

    guest_units.append(
        {
            "unit_id": len(guest_units) + 1,
            "chapter": chapter["chapter"],
            "guest": chapter["guest"],
            "title": chapter["title"],
            "start_timestamp":
                chapter["start_timestamp"],
            "start_seconds":
                chapter["start_seconds"],
            "end_timestamp":
                end_timestamp,
            "end_seconds":
                end_seconds,
            "boundary_method":
                "youtube_chapter_to_next_chapter",
        }
    )


# ------------------------------------------------------------
# 3. Print validation
# ------------------------------------------------------------

print("=" * 100)
print("YOUTUBE GUEST UNIT BUILDER")
print("=" * 100)

print(
    f"TOTAL CHAPTERS: {len(chapters)}"
)

print(
    f"GUEST UNITS: {len(guest_units)}"
)

print("=" * 100)


for unit in guest_units:

    duration = None

    if unit["end_seconds"] is not None:
        duration = (
            unit["end_seconds"]
            - unit["start_seconds"]
        )

    print()
    print(
        f"UNIT {unit['unit_id']:02d} | "
        f"CHAPTER {unit['chapter']:02d}"
    )

    print(
        f"GUEST: {unit['guest']}"
    )

    print(
        f"START: "
        f"{unit['start_timestamp']}"
    )

    print(
        f"END: "
        f"{unit['end_timestamp'] or 'END_OF_VIDEO'}"
    )

    if duration is not None:
        print(
            f"DURATION: {duration}s"
        )

    print(
        f"METHOD: "
        f"{unit['boundary_method']}"
    )


# ------------------------------------------------------------
# 4. Save artifact
# ------------------------------------------------------------

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT.write_text(
    json.dumps(
        {
            "date": "2026-08-14",
            "source":
                "YouTube Transcript / Chapters",
            "guest_units":
                guest_units,
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)


print()
print("=" * 100)
print("BUILD COMPLETE")
print("=" * 100)

print(
    "OUTPUT:",
    OUTPUT,
)

print(
    "GUEST UNITS:",
    len(guest_units),
)
