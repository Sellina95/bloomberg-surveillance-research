from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def validate(payload: dict, expected_date: str) -> None:
    assert payload["schema_version"] == "report_provenance_v0_1"
    assert payload["report_date"] == expected_date
    source = payload["source"]
    assert source["broadcast_date"] == expected_date
    for key in (
        "broadcast_title", "upload_date", "video_url", "provider",
        "transcript_type", "collected_at", "source_mode",
    ):
        assert source[key]
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    assert "transcript_text" not in serialized
    assert '"text"' not in serialized
    assert payload["claims"]
    for claim in payload["claims"]:
        assert claim["claim_id"] and claim["references"]
        for ref in claim["references"]:
            assert set(ref) == {"segment_id", "timestamp_seconds"}


fixture = {
    "schema_version": "report_provenance_v0_1",
    "report_date": "2026-09-05",
    "source": {
        "broadcast_title": "Rates Reset",
        "broadcast_date": "2026-09-05",
        "upload_date": "2026-09-05",
        "video_url": "https://www.youtube.com/watch?v=test",
        "provider": "Supadata",
        "transcript_type": "timestamped_youtube_transcript",
        "collected_at": "2026-09-05T23:00:00+00:00",
        "source_mode": "program_level_unattributed",
    },
    "boundary": "IDENTIFIERS_AND_TIMESTAMPS_ONLY_NO_SOURCE_TEXT",
    "claims": [{
        "claim_id": "20260905-U001-C01",
        "unit_id": 1,
        "references": [{"segment_id": 10, "timestamp_seconds": 42.5}],
    }],
}
validate(fixture, "2026-09-05")
print("PROVENANCE CONTRACT: PASS")
