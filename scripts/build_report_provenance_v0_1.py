from __future__ import annotations

import json
import os
from pathlib import Path


DATE = os.environ.get(
    "SURVEILLANCE_DATE",
    "2026-08-24",
)

BASE = Path(
    f"data/processed/surveillance/{DATE}"
)

DATASET = BASE / "research_dataset_v0_1.json"

OUTPUT = BASE / "report_provenance_v0_1.json"


# v0.1 is intentionally human-reviewed.
#
# IMPORTANT:
# These references identify grounded research claims.
# No transcript/evidence text enters this public artifact.
#
# This mapping is currently approved for 2026-08-24 only.

APPROVED_MAPPING = {
    "2026-08-24": [
        {
            "target_id": "TAKEAWAY-01",
            "target_type": "research_takeaway",
            "provenance_type": "SUPPORTED_SYNTHESIS",
            "audit_status": "APPROVED",
            "claim_ids": [
                "20260824-U001-C01",
                "20260824-U001-C02",
                "20260824-U001-C03",
            ],
        },
        {
            "target_id": "TAKEAWAY-02",
            "target_type": "research_takeaway",
            "provenance_type": "SUPPORTED_SYNTHESIS",
            "audit_status": "APPROVED",
            "claim_ids": [
                "20260824-U008-C01",
                "20260824-U007-C01",
                "20260824-U007-C02",
            ],
        },
        {
            "target_id": "TAKEAWAY-03",
            "target_type": "research_takeaway",
            "provenance_type": "SUPPORTED_SYNTHESIS",
            "audit_status": "APPROVED",
            "claim_ids": [
                "20260824-U006-C01",
                "20260824-U006-C02",
                "20260824-U006-C03",
            ],
        },
        {
            "target_id": "CONSENSUS-01",
            "target_type": "cross_guest_consensus",
            "provenance_type": "PARTIAL_CONSENSUS",
            "audit_status": "REVIEW",
            "claim_ids": [
                "20260824-U001-C01",
                "20260824-U001-C02",
                "20260824-U004-C02",
            ],
            "declared_guest_support_status":
                "OVER_ATTRIBUTION_DETECTED",
        },
        {
            "target_id": "CONSENSUS-02",
            "target_type": "cross_guest_consensus",
            "provenance_type": "SUPPORTED_CONSENSUS",
            "audit_status": "APPROVED",
            "claim_ids": [
                "20260824-U003-C01",
                "20260824-U007-C01",
                "20260824-U008-C02",
            ],
        },
        {
            "target_id": "CONFLICT-01-VIEW_A",
            "target_type": "cross_guest_conflict_view",
            "provenance_type": "SUPPORTED",
            "audit_status": "APPROVED",
            "claim_ids": [
                "20260824-U007-C01",
                "20260824-U007-C02",
            ],
        },
        {
            "target_id": "CONFLICT-01-VIEW_B",
            "target_type": "cross_guest_conflict_view",
            "provenance_type": "SUPPORTED",
            "audit_status": "APPROVED",
            "claim_ids": [
                "20260824-U008-C01",
            ],
        },
    ],
}


def main() -> None:

    if DATE not in APPROVED_MAPPING:
        raise SystemExit(
            f"FAIL — no human-reviewed provenance mapping for {DATE}"
        )

    if not DATASET.exists():
        raise SystemExit(
            f"FAIL — dataset missing: {DATASET}"
        )

    dataset = json.loads(
        DATASET.read_text(encoding="utf-8")
    )

    claim_registry = {}

    for unit in dataset.get(
        "research_units",
        [],
    ):
        for view in (
            unit.get("research_summary", {})
            .get("key_views", [])
        ):
            claim_id = view.get("claim_id")

            if claim_id:
                claim_registry[claim_id] = True

    mappings = APPROVED_MAPPING[DATE]

    missing = []

    for mapping in mappings:
        for claim_id in mapping["claim_ids"]:
            if claim_id not in claim_registry:
                missing.append(
                    (
                        mapping["target_id"],
                        claim_id,
                    )
                )

    if missing:
        print("FAIL — unresolved claim references")

        for target_id, claim_id in missing:
            print(
                target_id,
                claim_id,
            )

        raise SystemExit(1)

    artifact = {
        "schema_version":
            "report_provenance_v0_1",

        "date":
            DATE,

        "source_dataset":
            str(DATASET),

        "source_summary_sha256":
            dataset.get(
                "source_summary_sha256"
            ),

        "mapping_policy":
            "HUMAN_REVIEWED",

        "public_private_boundary":
            "IDENTIFIERS_ONLY_NO_TRANSCRIPT_EVIDENCE",

        "mappings":
            mappings,
    }

    OUTPUT.write_text(
        json.dumps(
            artifact,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print("=" * 100)
    print("REPORT PROVENANCE v0.1")
    print("=" * 100)
    print("DATE:", DATE)
    print("MAPPINGS:", len(mappings))
    print(
        "CLAIM REFERENCES:",
        sum(
            len(x["claim_ids"])
            for x in mappings
        ),
    )
    print(
        "REVIEW ITEMS:",
        sum(
            x["audit_status"] == "REVIEW"
            for x in mappings
        ),
    )
    print("UNRESOLVED REFERENCES: 0")
    print("OUTPUT:", OUTPUT)
    print("=" * 100)
    print("BUILD: PASS")
    print("=" * 100)


if __name__ == "__main__":
    main()
