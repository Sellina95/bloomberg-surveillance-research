from __future__ import annotations

import json
import re
from pathlib import Path


DATE = "2026-08-14"

SUPADATA = Path(
    f"data/raw/youtube_probe/supadata_{DATE}.json"
)

REFERENCE = Path(
    f"data/reference/youtube/{DATE}_transcript.txt"
)

OUTPUT = Path(
    f"data/processed/surveillance/{DATE}/youtube_transcript.json"
)

TIMESTAMP_RE = re.compile(
    r"^\d{1,2}:\d{2}(?::\d{2})?$"
)

CHAPTER_RE = re.compile(
    r"^Chapter\s+(\d+):\s*(.+)$",
    re.IGNORECASE,
)


def to_seconds(value: str) -> float:
    parts = [int(x) for x in value.split(":")]

    if len(parts) == 2:
        return parts[0] * 60 + parts[1]

    return (
        parts[0] * 3600
        + parts[1] * 60
        + parts[2]
    )


# ============================================================
# 1. Load Supadata transcript
# ============================================================

payload = json.loads(
    SUPADATA.read_text(
        encoding="utf-8"
    )
)

content = payload["content"]

segments = []

for index, item in enumerate(content):

    segments.append(
        {
            "segment_id": index,
            "start_seconds":
                item["offset"] / 1000,
            "duration_seconds":
                item.get("duration", 0) / 1000,
            "end_seconds":
                (
                    item["offset"]
                    + item.get("duration", 0)
                ) / 1000,
            "text":
                item["text"].strip(),
            "lang":
                item.get("lang"),
        }
    )


# ============================================================
# 2. Parse YouTube Chapter metadata
# ============================================================

lines = [
    line.strip()
    for line in REFERENCE.read_text(
        encoding="utf-8"
    ).splitlines()
    if line.strip()
]

chapters = []

for i, line in enumerate(lines):

    match = CHAPTER_RE.match(line)

    if not match:
        continue

    chapter_number = int(
        match.group(1)
    )

    title = match.group(2)

    # Find timestamp immediately following chapter title.
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
            "guest": guest,
            "start_seconds": timestamp,
        }
    )


# ============================================================
# 3. Assign every transcript segment to a Chapter
# ============================================================

for i, chapter in enumerate(chapters):

    start = chapter["start_seconds"]

    end = (
        chapters[i + 1]["start_seconds"]
        if i + 1 < len(chapters)
        else None
    )

    for segment in segments:

        midpoint = (
            segment["start_seconds"]
            + segment["duration_seconds"] / 2
        )

        if midpoint < start:
            continue

        if end is not None and midpoint >= end:
            continue

        segment["chapter"] = chapter["chapter"]
        segment["chapter_title"] = chapter["title"]
        segment["chapter_guest"] = chapter["guest"]


# ============================================================
# 4. Build summary
# ============================================================

chapter_summary = []

for chapter in chapters:

    assigned = [
        segment
        for segment in segments
        if segment.get("chapter")
        == chapter["chapter"]
    ]

    chapter_summary.append(
        {
            "chapter":
                chapter["chapter"],
            "title":
                chapter["title"],
            "guest":
                chapter["guest"],
            "start_seconds":
                chapter["start_seconds"],
            "end_seconds":
                (
                    chapters[
                        chapters.index(chapter) + 1
                    ]["start_seconds"]
                    if chapters.index(chapter)
                    + 1 < len(chapters)
                    else None
                ),
            "segment_count":
                len(assigned),
        }
    )


# ============================================================
# 5. Save canonical artifact
# ============================================================

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

artifact = {
    "date": DATE,
    "source": "Supadata YouTube Transcript",
    "source_video":
        "qWYTenEUdFc",
    "language":
        payload.get("lang"),
    "segment_count":
        len(segments),
    "chapter_count":
        len(chapters),
    "chapters":
        chapter_summary,
    "segments":
        segments,
}

OUTPUT.write_text(
    json.dumps(
        artifact,
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)


# ============================================================
# 6. Validation
# ============================================================

print("=" * 100)
print("YOUTUBE CANONICAL TRANSCRIPT")
print("=" * 100)

print(
    "SEGMENTS:",
    len(segments),
)

print(
    "CHAPTERS:",
    len(chapters),
)

print()

for chapter in chapter_summary:

    print(
        f"CHAPTER {chapter['chapter']:02d} | "
        f"{chapter['guest'] or 'NON-GUEST'} | "
        f"SEGMENTS={chapter['segment_count']}"
    )

print()
print("=" * 100)
print("OUTPUT")
print("=" * 100)

print(OUTPUT)

print()
print("CANONICAL TRANSCRIPT BUILD: PASS")
print("=" * 100)
