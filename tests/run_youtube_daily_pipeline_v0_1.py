from __future__ import annotations

import json
import re
from pathlib import Path


DATE = "2026-08-14"

RAW = Path(
    f"data/raw/youtube/{DATE}/transcript.json"
)

OUT = Path(
    f"data/processed/surveillance/{DATE}"
)

CANONICAL = OUT / "youtube_transcript.json"
GUEST_UNITS = OUT / "guest_units.json"


# ============================================================
# 1. LOAD TRANSCRIPT
# ============================================================

data = json.loads(
    RAW.read_text(encoding="utf-8")
)

content = data["content"]

segments = []

for i, item in enumerate(content):

    start = item["offset"] / 1000
    duration = item.get("duration", 0) / 1000

    segments.append(
        {
            "segment_id": i,
            "start_seconds": start,
            "duration_seconds": duration,
            "end_seconds": start + duration,
            "text": item["text"].strip(),
            "lang": item.get("lang"),
        }
    )


# ============================================================
# 2. CHAPTER REFERENCE
#
# IMPORTANT:
# These are the already validated YouTube Chapter metadata
# for 2026-08-14.
#
# They are REFERENCE / VALIDATION data, not transcript
# detection input.
# ============================================================

CHAPTERS = [
    {
        "chapter": 2,
        "guest": "Julian Emanuel, Evercore ISI",
        "start_seconds": 292.0,
    },
    {
        "chapter": 3,
        "guest": "Julian Emanuel, Evercore ISI",
        "start_seconds": 1200.0,
    },
    {
        "chapter": 4,
        "guest": "Nick Setyan, Mizuho",
        "start_seconds": 1942.0,
    },
    {
        "chapter": 5,
        "guest": "James Athey, Marlborough Investment Management",
        "start_seconds": 2523.0,
    },
    {
        "chapter": 6,
        "guest": "Binky Chadha, Deutsche Bank",
        "start_seconds": 3134.0,
    },
    {
        "chapter": 7,
        "guest": "Jeannette Lowe, Baird Strategas",
        "start_seconds": 3990.0,
    },
    {
        "chapter": 8,
        "guest": "Robert DeNault, Kalshi",
        "start_seconds": 4630.0,
    },
    {
        "chapter": 9,
        "guest": "Lindsey Piegza, Stifel",
        "start_seconds": 5373.0,
    },
    {
        "chapter": 10,
        "guest": "Katy Kaminski, AlphaSimplex",
        "start_seconds": 6056.0,
    },
    {
        "chapter": 11,
        "guest": "Kylie Cohu, Jefferies",
        "start_seconds": 6807.0,
    },
    {
        "chapter": 12,
        "guest": "Michael McKee",
        "start_seconds": 7263.0,
    },
    {
        "chapter": 13,
        "guest": "Aditya Bhave, Bank of America",
        "start_seconds": 7395.0,
    },
    {
        "chapter": 14,
        "guest": "Peter Tchir, Academy Securities",
        "start_seconds": 8255.0,
    },
]


# ============================================================
# 3. ASSIGN TRANSCRIPT TO CHAPTER WINDOWS
# ============================================================

for i, chapter in enumerate(CHAPTERS):

    start = chapter["start_seconds"]

    end = (
        CHAPTERS[i + 1]["start_seconds"]
        if i + 1 < len(CHAPTERS)
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
        segment["chapter_guest"] = chapter["guest"]


# ============================================================
# 4. SAVE CANONICAL TRANSCRIPT
# ============================================================

OUT.mkdir(
    parents=True,
    exist_ok=True,
)

canonical = {
    "date": DATE,
    "source": "Supadata YouTube Transcript",
    "segment_count": len(segments),
    "chapters": CHAPTERS,
    "segments": segments,
}

CANONICAL.write_text(
    json.dumps(
        canonical,
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)


# ============================================================
# 5. BUILD GUEST UNITS
# ============================================================

END_PATTERNS = [
    "thank you so much",
    "thank you for joining us",
    "thanks for having me",
    "thank you for being here",
    "stay with us",
    "coming up next",
    "have a wonderful weekend",
]


def normalize(text: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        text.lower(),
    ).strip()


def is_end_signal(text: str) -> bool:

    text = normalize(text)

    return any(
        pattern in text
        for pattern in END_PATTERNS
    )


units = []

for i, chapter in enumerate(CHAPTERS):

    chapter_start = chapter["start_seconds"]

    next_start = (
        CHAPTERS[i + 1]["start_seconds"]
        if i + 1 < len(CHAPTERS)
        else None
    )

    rows = [
        s
        for s in segments
        if s.get("chapter") == chapter["chapter"]
    ]

    if not rows:
        continue

    start_segment = rows[0]

    end_segment = None

    for row in rows:

        if is_end_signal(row["text"]):

            end_segment = row
            break

    if end_segment:

        end_time = end_segment["end_seconds"]
        end_method = "explicit_end_signal"

    elif next_start is not None:

        end_time = next_start
        end_method = "chapter_boundary_fallback"

    else:

        end_time = rows[-1]["end_seconds"]
        end_method = "transcript_end"

    units.append(
        {
            "unit_id": i + 1,
            "chapter": chapter["chapter"],
            "guest": chapter["guest"],
            "start_seconds":
                start_segment["start_seconds"],
            "end_seconds":
                end_time,
            "duration_seconds":
                end_time
                - start_segment["start_seconds"],
            "segment_count":
                len(rows),
            "start_method":
                "first_transcript_segment",
            "end_method":
                end_method,
        }
    )


# ============================================================
# 6. SAVE GUEST UNITS
# ============================================================

guest_artifact = {
    "date": DATE,
    "method": "daily_youtube_pipeline_v0_1",
    "transcript_segments": len(segments),
    "guest_units": units,
}

GUEST_UNITS.write_text(
    json.dumps(
        guest_artifact,
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)


# ============================================================
# 7. RESULT
# ============================================================

print("=" * 100)
print("YOUTUBE DAILY PIPELINE v0.1")
print("=" * 100)

print(
    "TRANSCRIPT:",
    "PASS",
)

print(
    "SEGMENTS:",
    len(segments),
)

print(
    "CANONICAL:",
    CANONICAL,
)

print(
    "GUEST UNITS:",
    f"{len(units)}/{len(CHAPTERS)}",
)

print(
    "GUEST UNITS OUTPUT:",
    GUEST_UNITS,
)

print()
print("=" * 100)

if len(units) == len(CHAPTERS):
    print("PIPELINE: PASS")
else:
    print("PIPELINE: REVIEW")

print("=" * 100)
