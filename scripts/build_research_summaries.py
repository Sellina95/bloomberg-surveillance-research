from __future__ import annotations

import json
from pathlib import Path


DATES = [
    "2026-08-10",
    "2026-08-14",
]

BASE = Path("data/processed/surveillance")


def build_summary(unit: dict) -> dict:
    return {
        "unit_id": unit["unit_id"],
        "chapter": unit["chapter"],
        "guest": unit.get("guest"),
        "organization": None,
        "timestamp": {
            "start_seconds": unit["start_seconds"],
            "end_seconds": unit["end_seconds"],
        },

        # Research fields — populated by summary engine
        "topic": None,
        "key_views": [],
        "why_it_matters": None,
        "market_implication": None,
        "research_tags": [],

        # Evidence must always point back to source transcript
        "evidence": [],

        # Audit
        "source": {
            "transcript": "supadata",
            "chapters": "serpapi",
        },
        "summary_status": "PENDING",
    }


for date in DATES:

    input_path = (
        BASE
        / date
        / "guest_transcripts.json"
    )

    output_path = (
        BASE
        / date
        / "research_summaries.json"
    )

    data = json.loads(
        input_path.read_text(
            encoding="utf-8"
        )
    )

    summaries = [
        build_summary(unit)
        for unit in data["units"]
    ]

    artifact = {
        "date": date,
        "schema_version": "research_summary_v0_1",
        "guest_count": len(summaries),
        "summaries": summaries,
    }

    output_path.write_text(
        json.dumps(
            artifact,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("=" * 100)
    print("RESEARCH SUMMARY SCHEMA")
    print("DATE:", date)
    print("GUESTS:", len(summaries))
    print("OUTPUT:", output_path)
    print("=" * 100)


print()
print("=" * 100)
print("BUILD COMPLETE")
print("=" * 100)
