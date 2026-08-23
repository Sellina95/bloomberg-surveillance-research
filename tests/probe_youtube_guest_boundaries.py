from __future__ import annotations

import re
from pathlib import Path


INPUT = Path("data/reference/youtube/2026-08-14_transcript.txt")

START_PATTERNS = [
    "joins us now",
    "joins us",
    "joining us",
]

END_PATTERNS = [
    "thank you so much",
    "thank you for joining us",
    "thanks for having me",
    "thank you for being here",
    "great to see you",
    "stay with us",
    "coming up next",
    "coming up",
]


def to_seconds(value: str) -> int:
    parts = [int(x) for x in value.split(":")]

    if len(parts) == 2:
        return parts[0] * 60 + parts[1]

    return (
        parts[0] * 3600
        + parts[1] * 60
        + parts[2]
    )


def parse(text: str):
    lines = [
        x.strip()
        for x in text.splitlines()
        if x.strip()
    ]

    timestamp_re = re.compile(
        r"^\d{1,2}:\d{2}(?::\d{2})?$"
    )

    rows = []

    current_time = None
    current_text = []

    def flush():
        nonlocal current_time, current_text

        if current_time is not None and current_text:
            rows.append(
                {
                    "seconds": current_time,
                    "text": " ".join(current_text),
                }
            )

        current_text = []

    for line in lines:

        if timestamp_re.match(line):

            flush()

            current_time = to_seconds(line)

        elif line.startswith("Sync to video time"):
            continue

        else:
            current_text.append(line)

    flush()

    return rows


text = INPUT.read_text(
    encoding="utf-8"
)

rows = parse(text)

print("=" * 100)
print("YOUTUBE TRANSCRIPT GUEST BOUNDARY PROBE")
print("=" * 100)
print("ROWS:", len(rows))
print("=" * 100)

for i, row in enumerate(rows):

    lowered = row["text"].lower()

    starts = [
        p for p in START_PATTERNS
        if p in lowered
    ]

    ends = [
        p for p in END_PATTERNS
        if p in lowered
    ]

    if not starts and not ends:
        continue

    print()
    print("-" * 100)
    print(
        f"TIME: {row['seconds']}s "
        f"({row['seconds'] // 60}:{row['seconds'] % 60:02d})"
    )

    if starts:
        print(
            "START:",
            ", ".join(starts)
        )

    if ends:
        print(
            "END:",
            ", ".join(ends)
        )

    print()
    print(row["text"][:1200])


print()
print("=" * 100)
print("DONE")
print("=" * 100)
