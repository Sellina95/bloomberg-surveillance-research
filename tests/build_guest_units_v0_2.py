from __future__ import annotations

import json
import re
from pathlib import Path


BASE = Path(
    "data/processed/surveillance/2026-08-14"
)

TRANSCRIPT = BASE / "youtube_transcript.json"

OUTPUT = BASE / "guest_units_v0_2.json"


data = json.loads(
    TRANSCRIPT.read_text(encoding="utf-8")
)

segments = data["segments"]
chapters = [
    x for x in data["chapters"]
    if x.get("guest")
]


def normalize(text: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        text.lower(),
    ).strip()


END_PATTERNS = [
    "thank you so much",
    "thank you for joining us",
    "thanks for having me",
    "thank you for being here",
    "stay with us",
    "coming up next",
    "have a wonderful weekend",
]


def is_end_signal(text: str) -> bool:
    text = normalize(text)

    return any(
        pattern in text
        for pattern in END_PATTERNS
    )


units = []


for i, chapter in enumerate(chapters):

    chapter_start = chapter[
        "start_seconds"
    ]

    next_chapter_start = (
        chapters[i + 1]["start_seconds"]
        if i + 1 < len(chapters)
        else None
    )

    # --------------------------------------------------------
    # Find transcript region belonging to this chapter.
    # Chapter is used only as a broad research window.
    # --------------------------------------------------------

    rows = [
        s
        for s in segments
        if s["start_seconds"] >= chapter_start
        and (
            next_chapter_start is None
            or s["start_seconds"]
            < next_chapter_start
        )
    ]

    if not rows:
        continue

    # --------------------------------------------------------
    # Find first meaningful transcript segment.
    # --------------------------------------------------------

    start_segment = rows[0]

    # --------------------------------------------------------
    # Find end signal.
    # --------------------------------------------------------

    end_segment = None

    for row in rows:

        if is_end_signal(row["text"]):

            end_segment = row
            break

    # --------------------------------------------------------
    # If no explicit end signal, use chapter boundary.
    # --------------------------------------------------------

    if end_segment:

        end_time = end_segment[
            "end_seconds"
        ]

        method = (
            "explicit_end_signal"
        )

    else:

        end_time = (
            next_chapter_start
            if next_chapter_start is not None
            else rows[-1]["end_seconds"]
        )

        method = (
            "chapter_boundary_fallback"
        )

    unit = {
        "unit_id": i + 1,
        "chapter": chapter["chapter"],
        "guest": chapter["guest"],
        "title": chapter["title"],
        "start_seconds":
            start_segment["start_seconds"],
        "end_seconds":
            end_time,
        "duration_seconds":
            end_time
            - start_segment["start_seconds"],
        "start_method":
            "first_transcript_segment_after_chapter",
        "end_method":
            method,
        "segment_count":
            len(rows),
    }

    units.append(unit)


# ------------------------------------------------------------
# Output
# ------------------------------------------------------------

artifact = {
    "date": "2026-08-14",
    "method": "guest_units_v0_2",
    "ground_truth_chapters": len(chapters),
    "guest_units": units,
}


OUTPUT.write_text(
    json.dumps(
        artifact,
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)


print("=" * 100)
print("GUEST UNIT BUILD v0.2")
print("=" * 100)

print(
    f"GUEST UNITS: {len(units)}/{len(chapters)}"
)

for unit in units:

    print(
        f"UNIT {unit['unit_id']:02d} | "
        f"{unit['guest']} | "
        f"{unit['start_seconds']:.2f}s → "
        f"{unit['end_seconds']:.2f}s"
    )

print()
print("=" * 100)

if len(units) == len(chapters):
    print("BUILD: PASS")
else:
    print("BUILD: REVIEW")

print("=" * 100)
print("OUTPUT:", OUTPUT)
