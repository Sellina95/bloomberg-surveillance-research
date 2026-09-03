from __future__ import annotations
import os

import json
import re
from pathlib import Path


DATE = os.environ.get("SURVEILLANCE_DATE", "2026-08-14")

INPUT = Path(
    f"data/processed/surveillance/{DATE}/"
    "youtube_canonical_v0_2.json"
)

OUTPUT = Path(
    f"data/processed/surveillance/{DATE}/"
    "guest_units_v0_3.json"
)


# ------------------------------------------------------------
# Guest chapter classification
# ------------------------------------------------------------

NON_GUEST_PATTERNS = [
    "ai boom",
    "economic",
    "market",
    "stocks",
    "markets",
    "outlook",
    "surveillance",
    "opening",
    "closing",
    "morning",
    "retail sales",
]

# A chapter is treated as a guest chapter when its title
# contains a guest-style attribution after the main title.
#
# Examples:
#   "... — Julian Emanuel, Evercore ISI"
#   "... — Nick Setyan, Mizuho"
#
# A dash is deliberately required so ordinary editorial
# chapters are not automatically classified as guests.

GUEST_TITLE_RE = re.compile(
    r"^.+\s[—-]\s+"
    r"([^—-]+)"
    r"(?:,\s+(.+))?$"
)


def classify_guest(title: str) -> bool:

    title_normalized = title.lower().strip()

    if any(
        pattern in title_normalized
        for pattern in NON_GUEST_PATTERNS
    ):
        # Do not immediately reject if the title clearly
        # contains a guest attribution.
        pass

    match = GUEST_TITLE_RE.match(title.strip())

    if not match:
        return False

    guest_part = match.group(1).strip()

    # Guest attribution should look like a person's name,
    # not a generic phrase.
    words = guest_part.split()

    if len(words) < 2:
        return False

    return all(
        re.search(r"[A-Za-z]", word)
        for word in words
    )


# ------------------------------------------------------------
# Load canonical dataset
# ------------------------------------------------------------

data = json.loads(
    INPUT.read_text(encoding="utf-8")
)

chapters = data["chapters"]
segments = data["segments"]
chapter_mode = data.get(
    "chapter_mode",
    "source_chapters",
)


# ------------------------------------------------------------
# Classify chapters
# ------------------------------------------------------------

classified = []

for chapter in chapters:

    title = chapter["title"]

    is_guest = classify_guest(title)

    classified.append(
        {
            **chapter,
            "is_guest": is_guest,
        }
    )


guest_chapters = [
    chapter
    for chapter in classified
    if chapter["is_guest"]
]


# ------------------------------------------------------------
# Build Guest Units
# ------------------------------------------------------------

units = []

if chapter_mode == "full_program_fallback":

    start = min(
        s["start_seconds"]
        for s in segments
    )
    end = max(
        s["end_seconds"]
        for s in segments
    )

    units.append(
        {
            "unit_id": 1,
            "chapter": 1,
            "title": (
                "Full program (speaker attribution unavailable)"
            ),
            "guest": None,
            "unit_type": "program",
            "attribution_status": "unavailable",
            "start_seconds": start,
            "end_seconds": end,
            "duration_seconds": end - start,
            "segment_count": len(segments),
            "source_chapter": "full_program_fallback",
            "source_transcript": "supadata",
        }
    )

else:

    for unit_id, chapter in enumerate(
        guest_chapters,
        start=1,
    ):

        chapter_index = classified.index(
            chapter
        )

        start = chapter["start_seconds"]

        # End at the next actual YouTube Chapter,
        # regardless of whether that chapter is a guest.
        if chapter_index + 1 < len(classified):

            end = classified[
                chapter_index + 1
            ]["start_seconds"]

        else:

            end = max(
                s["end_seconds"]
                for s in segments
            )

        rows = [
            s
            for s in segments
            if (
                s["start_seconds"] >= start
                and s["start_seconds"] < end
            )
        ]

        units.append(
            {
                "unit_id": unit_id,
                "chapter": chapter["chapter"],
                "title": chapter["title"],
                "guest": chapter["title"]
                    .split(" — ", 1)[-1]
                    .strip(),
                "unit_type": "guest",
                "attribution_status": "source_chapter",
                "start_seconds": start,
                "end_seconds": end,
                "duration_seconds": end - start,
                "segment_count": len(rows),
                "source_chapter": "serpapi",
                "source_transcript": "supadata",
            }
        )


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

artifact = {
    "date": DATE,
    "method": (
        "full_program_unattributed_v0_1"
        if chapter_mode == "full_program_fallback"
        else "chapter_attribution_v0_3"
    ),
    "total_chapters": len(classified),
    "guest_chapter_count": len(guest_chapters),
    "chapters": classified,
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


# ------------------------------------------------------------
# Result
# ------------------------------------------------------------

print("=" * 100)
print("GUEST UNIT BUILD v0.3")
print("=" * 100)

print(
    "TOTAL CHAPTERS:",
    len(classified),
)

print(
    "GUEST CHAPTERS:",
    len(guest_chapters),
)

print()

for unit in units:

    print(
        f"UNIT {unit['unit_id']:02d} | "
        f"CHAPTER {unit['chapter']:02d} | "
        f"{unit['guest']} | "
        f"{unit['start_seconds']:.2f}s → "
        f"{unit['end_seconds']:.2f}s"
    )

print()
print("=" * 100)

if units:
    print("GUEST UNIT BUILD: PASS")
else:
    print("GUEST UNIT BUILD: FAIL")

print("=" * 100)

print("OUTPUT:", OUTPUT)
