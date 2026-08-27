from __future__ import annotations
import os

import hashlib
import json
from pathlib import Path


DATE = os.environ.get("SURVEILLANCE_DATE", "2026-08-14")

BASE = Path(
    f"data/processed/surveillance/{DATE}"
)

INPUT = (
    BASE
    / "research_summaries_gemini_v0_2.json"
)

OUTPUT = (
    BASE
    / "research_dataset_v0_1.json"
)


source_summary_bytes = INPUT.read_bytes()

source_summary_sha256 = hashlib.sha256(
    source_summary_bytes
).hexdigest()

data = json.loads(
    source_summary_bytes.decode("utf-8")
)


research_units = []

for item in data["summaries"]:

    if item["status"] != "COMPLETE":
        continue

    summary = item["summary"]

    key_views = []

    for source_ordinal, view in enumerate(
        summary.get(
            "key_views",
            []
        ),
        start=1,
    ):

        claim_id = (
            f"{DATE.replace('-', '')}-"
            f"U{item['unit_id']:03d}-"
            f"C{source_ordinal:02d}"
        )

        if view["grounding_status"] != "PASS":
            continue

        evidence = []

        for e in view["evidence"]:

            evidence.append(
                {
                    "segment_id":
                        e["segment_id"],
                    "timestamp_seconds":
                        e["timestamp_seconds"],
                    "text":
                        e["text"],
                }
            )

        key_views.append(
            {
                "claim_id":
                    claim_id,

                "claim":
                    view["claim"],

                "evidence":
                    evidence,
            }
        )

    research_units.append(
        {
            "unit_id":
                item["unit_id"],

            "guest":
                item.get("guest"),

            "organization":
                item.get("title"),

            "chapter":
                item["chapter"],

            "timestamp":
                item["timestamp"],

            "research_summary":
                {
                    "topic":
                        summary.get("topic"),

                    "key_views":
                        key_views,

                    "why_it_matters":
                        summary.get(
                            "why_it_matters"
                        ),

                    "market_implication":
                        summary.get(
                            "market_implication"
                        ),

                    "research_tags":
                        summary.get(
                            "research_tags",
                            [],
                        ),
                },

            "provenance":
                {
                    "transcript_source":
                        "supadata",

                    "chapter_source":
                        "serpapi",

                    "llm_model":
                        data["model"],

                    "evidence_policy":
                        "segment_id_grounded",
                },
        }
    )


artifact = {
    "date": DATE,

    "schema_version":
        "research_dataset_v0_1",

    "source_summary":
        str(INPUT),

    "source_summary_sha256":
        source_summary_sha256,

    "guest_count":
        len(research_units),

    "research_units":
        research_units,
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
print("RESEARCH DATASET BUILD v0.1")
print("=" * 100)
print("DATE:", DATE)
print(
    "INPUT UNITS:",
    len(data["summaries"]),
)
print(
    "VALID RESEARCH UNITS:",
    len(research_units),
)
print(
    "OUTPUT:",
    OUTPUT,
)
print("=" * 100)

if (
    len(research_units)
    == len(data["summaries"])
    and len(research_units) > 0
):
    print("BUILD: PASS")
else:
    print("BUILD: REVIEW")

print("=" * 100)
