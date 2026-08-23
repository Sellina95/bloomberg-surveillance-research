from __future__ import annotations

import json
from pathlib import Path


DATES = [
    "2026-08-10",
    "2026-08-14",
]

BASE = Path("data/processed/surveillance")


def build_packet(unit: dict) -> dict:
    segments = unit["transcript_segments"]

    evidence = []

    for segment in segments:
        text = segment["text"].strip()

        if not text:
            continue

        evidence.append(
            {
                "timestamp_seconds":
                    segment["start_seconds"],
                "text": text,
            }
        )

    return {
        "unit_id": unit["unit_id"],
        "chapter": unit["chapter"],
        "guest": unit.get("guest"),
        "title": unit.get("title"),

        "time_range": {
            "start_seconds":
                unit["start_seconds"],
            "end_seconds":
                unit["end_seconds"],
        },

        # ====================================================
        # LLM MUST populate these from evidence only
        # ====================================================

        "research_summary": {
            "topic": None,
            "key_views": [],
            "why_it_matters": None,
            "market_implication": None,
            "research_tags": [],
        },

        # ====================================================
        # Source evidence
        # ====================================================

        "evidence": evidence,

        "instructions": {
            "source_only": True,
            "do_not_invent_facts": True,
            "do_not_add_external_information": True,
            "every_key_view_requires_evidence": True,
            "market_implication_must_be_distinguished_from_guest_view":
                True,
        },

        "status": "READY_FOR_LLM",
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
        / "research_summary_packets.json"
    )

    data = json.loads(
        input_path.read_text(
            encoding="utf-8"
        )
    )

    packets = [
        build_packet(unit)
        for unit in data["units"]
    ]

    artifact = {
        "date": date,
        "schema_version":
            "research_summary_packet_v0_1",
        "guest_count": len(packets),
        "packets": packets,
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
    print("RESEARCH SUMMARY PACKETS")
    print("DATE:", date)
    print("GUESTS:", len(packets))
    print("OUTPUT:", output_path)
    print("=" * 100)


print()
print("=" * 100)
print("PACKET BUILD COMPLETE")
print("=" * 100)
