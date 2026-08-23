from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.processing.normalize_transcript import (
    normalize_segments,
    serialize_processed,
    write_normalized,
)


DATES = [
    "2026-08-13",
    "2026-08-14",
]

RAW_ROOT = Path("data/raw/surveillance")


def validate_date(date: str) -> bool:
    raw_path = (
        RAW_ROOT / date / "transcript.json"
    )
    metadata_path = (
        RAW_ROOT / date / "metadata.json"
    )

    raw_bytes = raw_path.read_bytes()

    raw = json.loads(
        raw_bytes.decode("utf-8")
    )

    metadata = json.loads(
        metadata_path.read_text(
            encoding="utf-8"
        )
    )

    raw_sha256 = hashlib.sha256(
        raw_bytes
    ).hexdigest()

    normalized = normalize_segments(date)

    raw_segments = raw["segments"]
    processed_segments = normalized["segments"]

    nonempty_raw = [
        (segment_id, segment)
        for segment_id, segment
        in enumerate(raw_segments)
        if segment.get("words")
    ]

    failures = []

    if len(nonempty_raw) != len(processed_segments):
        failures.append(
            "segment count mismatch"
        )

    for (
        raw_id,
        raw_segment,
    ), processed in zip(
        nonempty_raw,
        processed_segments,
    ):
        words = raw_segment["words"]

        expected_text = " ".join(
            word["text"]
            for word in words
        )

        checks = {
            "segment_id": (
                processed["segment_id"]
                == raw_id
            ),
            "speaker_index": (
                processed["speaker_index"]
                == raw_segment.get("speaker")
            ),
            "start_seconds": (
                processed["start_seconds"]
                == words[0]["start"]
            ),
            "end_seconds": (
                processed["end_seconds"]
                == words[-1]["end"]
            ),
            "word_count": (
                processed["word_count"]
                == len(words)
            ),
            "text": (
                processed["text"]
                == expected_text
            ),
        }

        failed_fields = [
            name
            for name, passed in checks.items()
            if not passed
        ]

        if failed_fields:
            failures.append(
                f"segment {raw_id}: "
                + ", ".join(failed_fields)
            )

    expected_ids = [
        segment_id
        for segment_id, _
        in nonempty_raw
    ]

    actual_ids = [
        segment["segment_id"]
        for segment in processed_segments
    ]

    ordering_pass = (
        actual_ids == expected_ids
    )

    raw_lineage_pass = (
        normalized[
            "source_transcript_sha256"
        ]
        == raw_sha256
        == metadata["transcript_sha256"]
    )

    episode_lineage_pass = (
        normalized["source_episode_guid"]
        == metadata["episode_guid"]
    )

    # Normalize independently a second time.
    normalized_again = normalize_segments(
        date
    )

    first_bytes = serialize_processed(
        normalized
    )
    second_bytes = serialize_processed(
        normalized_again
    )

    deterministic_pass = (
        first_bytes == second_bytes
    )

    print("=" * 72)
    print("DATE:", date)
    print("RAW SEGMENTS:", len(raw_segments))
    print(
        "NONEMPTY RAW SEGMENTS:",
        len(nonempty_raw),
    )
    print(
        "PROCESSED SEGMENTS:",
        len(processed_segments),
    )
    print()

    print(
        "ALL SEGMENTS REPRESENTED:",
        len(nonempty_raw)
        == len(processed_segments),
    )
    print(
        "RAW ORDER PRESERVED:",
        ordering_pass,
    )
    print(
        "RAW SHA256 LINEAGE:",
        raw_lineage_pass,
    )
    print(
        "EPISODE GUID LINEAGE:",
        episode_lineage_pass,
    )
    print(
        "SEGMENT FIELD FAILURES:",
        len(failures),
    )
    print(
        "IN-MEMORY DETERMINISM:",
        deterministic_pass,
    )

    if failures:
        for failure in failures[:10]:
            print(
                " FAILURE:",
                failure,
            )

    core_pass = (
        not failures
        and ordering_pass
        and raw_lineage_pass
        and episode_lineage_pass
        and deterministic_pass
    )

    if not core_pass:
        print("DATE RESULT: FAIL")
        return False

    result = write_normalized(date)

    persisted = Path(
        result["path"]
    ).read_bytes()

    persisted_match = (
        persisted == first_bytes
    )

    rerun = write_normalized(date)

    rerun_pass = (
        rerun["status"]
        == "EXISTS_DETERMINISTIC_PASS"
        and rerun["processed_sha256"]
        == result["processed_sha256"]
    )

    print(
        "WRITE STATUS:",
        result["status"],
    )
    print(
        "PROCESSED SHA256:",
        result["processed_sha256"],
    )
    print(
        "PERSISTED OUTPUT MATCH:",
        persisted_match,
    )
    print(
        "DETERMINISTIC RERUN:",
        rerun_pass,
    )

    final_pass = (
        persisted_match
        and rerun_pass
    )

    print(
        "DATE RESULT:",
        "PASS" if final_pass else "FAIL",
    )

    return final_pass


results = {
    date: validate_date(date)
    for date in DATES
}

print("=" * 72)
print("CROSS-DATE RESULTS")
print("=" * 72)

for date, passed in results.items():
    print(
        f"{date}:",
        "PASS" if passed else "FAIL",
    )

if not all(results.values()):
    raise SystemExit(
        "CROSS-DATE NORMALIZATION CHECK: FAIL"
    )

print()
print(
    "CROSS-DATE NORMALIZATION CHECK: PASS"
)
