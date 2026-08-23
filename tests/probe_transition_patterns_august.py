from __future__ import annotations

import json
from pathlib import Path


ROOT = Path("data/processed/surveillance")

DATES = [
    "2026-08-03",
    "2026-08-04",
    "2026-08-05",
    "2026-08-06",
    "2026-08-07",
    "2026-08-10",
    "2026-08-11",
    "2026-08-12",
    "2026-08-13",
    "2026-08-14",
    "2026-08-17",
    "2026-08-18",
    "2026-08-19",
    "2026-08-20",
    "2026-08-21",
]


PATTERNS = [
    "joins us now",
    "joins us",
    "joined by",
    "join us",
    "coming up",
    "stay with us",
    "more bloomberg surveillance coming up",
    "welcome back",
    "thank you so much",
    "thank you",
    "thanks for having me",
    "great to see you",
    "good to see you",
    "let's turn",
    "let us turn",
    "up next",
]


counts = {
    pattern: 0
    for pattern in PATTERNS
}

dates_seen = {
    pattern: set()
    for pattern in PATTERNS
}

examples = {
    pattern: []
    for pattern in PATTERNS
}


for date in DATES:
    path = (
        ROOT
        / date
        / "segments.json"
    )

    if not path.exists():
        print(
            f"SKIP {date}: processed transcript missing"
        )
        continue

    payload = json.loads(
        path.read_text(encoding="utf-8")
    )

    for segment in payload["segments"]:
        text = segment["text"]
        lower = text.lower()

        for pattern in PATTERNS:
            if pattern not in lower:
                continue

            counts[pattern] += 1
            dates_seen[pattern].add(date)

            if len(examples[pattern]) < 5:
                preview = text

                if len(preview) > 250:
                    preview = (
                        preview[:247] + "..."
                    )

                examples[pattern].append(
                    (
                        date,
                        segment["segment_id"],
                        preview,
                    )
                )


print("=" * 90)
print("BLOOMBERG SURVEILLANCE TRANSITION PATTERN AUDIT")
print("=" * 90)

for pattern in PATTERNS:
    print()
    print(
        f"{pattern:<35} "
        f"COUNT={counts[pattern]:<3} "
        f"DATES={len(dates_seen[pattern])}"
    )

    for (
        date,
        segment_id,
        preview,
    ) in examples[pattern]:
        print(
            f"  {date} | "
            f"SEGMENT {segment_id} | "
            f"{preview}"
        )

print()
print("=" * 90)
print("SUMMARY")
print("=" * 90)

for pattern in PATTERNS:
    if counts[pattern] == 0:
        classification = "NO EVIDENCE"
    elif len(dates_seen[pattern]) >= 8:
        classification = "RECURRING"
    elif len(dates_seen[pattern]) >= 3:
        classification = "OCCASIONAL"
    else:
        classification = "RARE"

    print(
        f"{pattern:<35} "
        f"{classification}"
    )

print("=" * 90)
