from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATE = os.environ.get("SURVEILLANCE_DATE", "")
if not DATE:
    raise SystemExit("PROVENANCE CONTRACT: FAIL — SURVEILLANCE_DATE missing")

BASE = ROOT / "data/processed/surveillance" / DATE
DATASET = BASE / "research_dataset_v0_1.json"
REPORT = BASE / "daily_research_report_v0_1.json"
OUTPUT = BASE / "report_provenance_v0_1.json"


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"PROVENANCE CONTRACT: FAIL — {name} missing")
    return value


def main() -> None:
    if not DATASET.exists() or not REPORT.exists():
        raise SystemExit("PROVENANCE CONTRACT: FAIL — private dataset or public report missing")
    dataset = json.loads(DATASET.read_text(encoding="utf-8"))
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    if dataset.get("date") != DATE or report.get("date") != DATE:
        raise SystemExit("PROVENANCE CONTRACT: FAIL — report/dataset date mismatch")

    claims = []
    for unit in dataset.get("research_units", []):
        for view in unit.get("research_summary", {}).get("key_views", []):
            claim_id = view.get("claim_id")
            evidence = view.get("evidence", [])
            references = []
            for row in evidence:
                if row.get("segment_id") is None or row.get("timestamp_seconds") is None:
                    raise SystemExit(
                        f"PROVENANCE CONTRACT: FAIL — incomplete reference for {claim_id}"
                    )
                references.append({
                    "segment_id": row["segment_id"],
                    "timestamp_seconds": row["timestamp_seconds"],
                })
            if not claim_id or not references:
                raise SystemExit("PROVENANCE CONTRACT: FAIL — ungrounded claim")
            claims.append({
                "claim_id": claim_id,
                "unit_id": unit.get("unit_id"),
                "references": references,
            })
    if not claims:
        raise SystemExit("PROVENANCE CONTRACT: FAIL — no grounded claims")

    broadcast_date = required_env("SOURCE_BROADCAST_DATE")
    if broadcast_date != DATE:
        raise SystemExit("PROVENANCE CONTRACT: FAIL — source/report date mismatch")

    artifact = {
        "schema_version": "report_provenance_v0_1",
        "report_date": DATE,
        "source": {
            "broadcast_title": required_env("SOURCE_BROADCAST_TITLE"),
            "broadcast_date": broadcast_date,
            "upload_date": required_env("SOURCE_UPLOAD_DATE"),
            "video_url": required_env("SOURCE_VIDEO_URL"),
            "provider": "Supadata",
            "transcript_type": "timestamped_youtube_transcript",
            "collected_at": os.environ.get(
                "SOURCE_COLLECTED_AT", datetime.now(timezone.utc).isoformat()
            ),
            "source_mode": report.get("source_mode", "chapter_attributed"),
        },
        "boundary": "IDENTIFIERS_AND_TIMESTAMPS_ONLY_NO_SOURCE_TEXT",
        "claims": claims,
    }
    OUTPUT.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("PROVENANCE CONTRACT: PASS")
    print("CLAIMS:", len(claims))
    print("OUTPUT:", OUTPUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
