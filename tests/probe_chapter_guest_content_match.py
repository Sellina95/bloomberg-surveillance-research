from __future__ import annotations

import json
import re
from pathlib import Path


DATE = "2026-08-14"

PATH = (
    Path("data/processed/surveillance")
    / DATE
    / "segments.json"
)

# YouTube Chapter에서 확인한 정보
GUESTS = [
    {
        "name": "Nick Setyan",
        "organization": "Mizuho",
        "topic": "Fast-Food Prices Are Driving Diners Elsewhere",
    },
    {
        "name": "James Athey",
        "organization": "Marlborough Investment Management",
        "topic": "AI Debt Could Crowd Out the US Treasury",
    },
    {
        "name": "Binky Chadha",
        "organization": "Deutsche Bank",
        "topic": "AI Is Driving Wider Growth",
    },
    {
        "name": "Jeannette Lowe",
        "organization": "Baird Strategies",
        "topic": "Treasury Leans on T-Bills as Deficit Risks Mount",
    },
]


payload = json.loads(
    PATH.read_text(encoding="utf-8")
)

segments = payload["segments"]


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


print("=" * 100)
print("YOUTUBE CHAPTER → TRANSCRIPT CONTENT MATCH")
print("=" * 100)
print("DATE:", DATE)
print("=" * 100)


for guest in GUESTS:

    name_parts = [
        normalize(part)
        for part in guest["name"].split()
    ]

    organization = normalize(
        guest["organization"]
    )

    topic_words = [
        word
        for word in normalize(
            guest["topic"]
        ).split()
        if len(word) >= 5
    ]

    print()
    print("-" * 100)
    print(
        "YOUTUBE CHAPTER:",
        guest["topic"],
    )
    print(
        "GUEST:",
        guest["name"],
    )
    print(
        "ORGANIZATION:",
        guest["organization"],
    )
    print("-" * 100)

    candidates = []

    for segment in segments:

        text = normalize(
            segment["text"]
        )

        name_hits = sum(
            1
            for part in name_parts
            if part in text
        )

        topic_hits = sum(
            1
            for word in topic_words
            if word in text
        )

        org_hit = (
            organization in text
            if organization
            else False
        )

        score = (
            name_hits * 5
            + topic_hits
            + (3 if org_hit else 0)
        )

        if score > 0:

            candidates.append(
                (
                    score,
                    segment,
                    name_hits,
                    topic_hits,
                    org_hit,
                )
            )

    candidates.sort(
        key=lambda row: (
            row[0],
            row[1]["word_count"],
        ),
        reverse=True,
    )

    for (
        score,
        segment,
        name_hits,
        topic_hits,
        org_hit,
    ) in candidates[:5]:

        print()
        print(
            f"SCORE: {score}"
        )

        print(
            f"SEGMENT: {segment['segment_id']}"
        )

        print(
            f"TIME: "
            f"{segment['start_seconds']:.1f}s"
        )

        print(
            f"SPEAKER: "
            f"{segment['speaker_index']}"
        )

        print(
            f"NAME HITS: {name_hits}"
        )

        print(
            f"TOPIC HITS: {topic_hits}"
        )

        print(
            f"ORG HIT: {org_hit}"
        )

        print(
            segment["text"][:500]
        )


print()
print("=" * 100)
print("DONE")
print("=" * 100)
