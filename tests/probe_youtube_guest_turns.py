from __future__ import annotations

import re
from pathlib import Path


INPUT = Path(
    "data/reference/youtube/2026-08-14_transcript.txt"
)

TIMESTAMP_RE = re.compile(
    r"^\d{1,2}:\d{2}(?::\d{2})?$"
)

CHAPTER_RE = re.compile(
    r"^Chapter\s+(\d+):\s*(.+)$",
    re.IGNORECASE,
)

SPEAKER_RE = re.compile(
    r"^(?:>>\s*)?([A-Z][A-Z ]{1,30}):\s*(.*)$"
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


lines = [
    x.strip()
    for x in INPUT.read_text(
        encoding="utf-8"
    ).splitlines()
    if x.strip()
]


# ------------------------------------------------------------
# Parse timestamped transcript rows
# ------------------------------------------------------------

rows = []

for i, line in enumerate(lines):

    if not TIMESTAMP_RE.match(line):
        continue

    timestamp = to_seconds(line)

    text_parts = []

    j = i + 1

    while (
        j < len(lines)
        and not TIMESTAMP_RE.match(lines[j])
    ):
        text_parts.append(lines[j])
        j += 1

    text = " ".join(text_parts)

    rows.append(
        {
            "seconds": timestamp,
            "text": text,
        }
    )


# ------------------------------------------------------------
# Parse guest chapters
# ------------------------------------------------------------

chapters = []

for i, line in enumerate(lines):

    match = CHAPTER_RE.match(line)

    if not match:
        continue

    title = match.group(2)

    if "—" not in title:
        continue

    guest = title.split(
        "—",
        1,
    )[1].strip()

    timestamp = None

    for j in range(
        i + 1,
        min(i + 8, len(lines)),
    ):
        if TIMESTAMP_RE.match(lines[j]):
            timestamp = to_seconds(lines[j])
            break

    if timestamp is None:
        continue

    chapters.append(
        {
            "chapter": int(match.group(1)),
            "guest": guest,
            "start": timestamp,
        }
    )


print("=" * 100)
print("YOUTUBE GUEST TURN PROBE")
print("=" * 100)


for index, chapter in enumerate(chapters):

    start = chapter["start"]

    end = (
        chapters[index + 1]["start"]
        if index + 1 < len(chapters)
        else float("inf")
    )

    window = [
        row
        for row in rows
        if start <= row["seconds"] < end
    ]

    print()
    print("-" * 100)

    print(
        f"CHAPTER {chapter['chapter']:02d}"
    )

    print(
        f"GUEST: {chapter['guest']}"
    )

    print(
        f"WINDOW: {start}s → "
        f"{end if end != float('inf') else 'END'}"
    )

    print()

    # Print speaker-labelled turns and obvious guest answers.
    for row in window:

        text = row["text"]

        speaker = SPEAKER_RE.match(text)

        if speaker:

            name = speaker.group(1)
            content = speaker.group(2)

            print(
                f"{row['seconds']:7.1f}s | "
                f"{name:20s} | "
                f"{content[:350]}"
            )

        elif text.startswith(">>"):

            print(
                f"{row['seconds']:7.1f}s | "
                f"UNKNOWN >> | "
                f"{text[:350]}"
            )


print()
print("=" * 100)
print("DONE")
print("=" * 100)
