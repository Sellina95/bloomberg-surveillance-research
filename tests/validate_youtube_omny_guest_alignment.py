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

TOLERANCE = 30


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
    for x in YOUTUBE.read_text(
        encoding="utf-8"
    ).splitlines()
    if x.strip()
]

chapter_re = re.compile(
    r"^Chapter\s+(\d+):\s*(.+)$",
    re.IGNORECASE,
)

timestamp_re = re.compile(
    r"^\d{1,2}:\d{2}(?::\d{2})?$"
)

chapters = []

for i, line in enumerate(lines):

    match = chapter_re.match(line)

    if not match:
        continue

    title = match.group(2)

    if "—" not in title:
        continue

    guest = title.split("—", 1)[1].strip()

    timestamp = None

    for j in range(i + 1, min(i + 8, len(lines))):

        if timestamp_re.match(lines[j]):
            timestamp = lines[j]
            break

    if timestamp is None:
        continue

    chapters.append(
        {
            "chapter": int(match.group(1)),
            "guest": guest,
            "youtube_seconds": to_seconds(timestamp),
            "title": title,
        }
    )


payload = json.loads(
    OMNY.read_text(
        encoding="utf-8"
    )
)

segments = payload["segments"]


START_PATTERNS = [
    "joins us now",
    "joins us",
    "joining us",
]


def has_join_signal(text: str) -> bool:

    text = text.lower()

    return any(
        pattern in text
        for pattern in START_PATTERNS
    )


print("=" * 100)
print("YOUTUBE ↔ OMNY GUEST ALIGNMENT")
print("=" * 100)

print(
    f"YOUTUBE GUEST CHAPTERS: {len(chapters)}"
)

print(
    f"OMNY SEGMENTS: {len(segments)}"
)

print("=" * 100)


passed = 0


for chapter in chapters:

    youtube_time = chapter["youtube_seconds"]

    candidates = [
        segment
        for segment in segments
        if has_join_signal(segment["text"])
    ]

    if not candidates:

        print()
        print(
            f"FAIL | CHAPTER {chapter['chapter']}"
        )
        print(
            "GUEST:",
            chapter["guest"]
        )
        print(
            "No OMNY joins-us signal found."
        )

        continue

    nearest = min(
        candidates,
        key=lambda segment:
            abs(
                segment["start_seconds"]
                - youtube_time
            ),
    )

    difference = abs(
        nearest["start_seconds"]
        - youtube_time
    )

    ok = difference <= TOLERANCE

    if ok:
        passed += 1

    print()
    print(
        f"{'PASS' if ok else 'FAIL'} | "
        f"CHAPTER {chapter['chapter']}"
    )

    print(
        "GUEST:",
        chapter["guest"]
    )

    print(
        f"YouTube: "
        f"{youtube_time:.1f}s"
    )

    print(
        f"OMNY: "
        f"{nearest['start_seconds']:.1f}s"
    )

    print(
        f"DIFFERENCE: "
        f"{difference:.1f}s"
    )

    print(
        "OMNY:",
        nearest["text"][:250]
    )


print()
print("=" * 100)
print("ALIGNMENT RESULT")
print("=" * 100)

print(
    f"PASS: {passed}/{len(chapters)}"
)

if passed == len(chapters):
    print(
        "CROSS-SOURCE ALIGNMENT: PASS"
    )
else:
    print(
        "CROSS-SOURCE ALIGNMENT: REVIEW REQUIRED"
    )

print("=" * 100)
