from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


RAW_ROOT = Path("data/raw/surveillance")
PROCESSED_ROOT = Path("data/processed/surveillance")


class NormalizationError(RuntimeError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_verified_raw(
    requested_date: str,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    raw_directory = RAW_ROOT / requested_date
    transcript_path = raw_directory / "transcript.json"
    metadata_path = raw_directory / "metadata.json"

    if not transcript_path.exists():
        raise NormalizationError(
            f"Raw transcript missing: {transcript_path}"
        )

    if not metadata_path.exists():
        raise NormalizationError(
            f"Raw metadata missing: {metadata_path}"
        )

    raw_bytes = transcript_path.read_bytes()

    try:
        metadata = json.loads(
            metadata_path.read_text(encoding="utf-8")
        )
        transcript = json.loads(
            raw_bytes.decode("utf-8")
        )
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise NormalizationError(
            "Raw acquisition contains invalid JSON"
        ) from exc

    expected_hash = metadata.get("transcript_sha256")
    actual_hash = sha256_bytes(raw_bytes)

    if not expected_hash:
        raise NormalizationError(
            "Raw metadata has no transcript_sha256"
        )

    if actual_hash != expected_hash:
        raise NormalizationError(
            "Raw transcript integrity verification failed: "
            f"expected={expected_hash}, actual={actual_hash}"
        )

    return transcript, metadata, actual_hash


def normalize_segments(
    requested_date: str,
) -> dict[str, Any]:
    transcript, metadata, raw_sha256 = (
        load_verified_raw(requested_date)
    )

    raw_segments = transcript.get("segments")

    if not isinstance(raw_segments, list):
        raise NormalizationError(
            "Raw transcript has no valid segments list"
        )

    processed_segments: list[dict[str, Any]] = []

    for segment_id, segment in enumerate(raw_segments):
        words = segment.get("words", [])

        if not words:
            continue

        speaker_index = segment.get("speaker")

        try:
            start_seconds = words[0]["start"]
            end_seconds = words[-1]["end"]

            tokens = [
                word["text"]
                for word in words
            ]
        except (KeyError, TypeError) as exc:
            raise NormalizationError(
                f"Invalid raw segment structure: "
                f"segment_id={segment_id}"
            ) from exc

        text = " ".join(tokens)

        processed_segments.append(
            {
                "requested_date": requested_date,
                "segment_id": segment_id,
                "speaker_index": speaker_index,
                "start_seconds": start_seconds,
                "end_seconds": end_seconds,
                "word_count": len(words),
                "text": text,
            }
        )

    return {
        "schema_version": "0.1",
        "requested_date": requested_date,
        "source_episode_guid": metadata.get(
            "episode_guid"
        ),
        "source_transcript_sha256": raw_sha256,
        "segment_count": len(processed_segments),
        "segments": processed_segments,
    }


def serialize_processed(
    payload: dict[str, Any],
) -> bytes:
    return (
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def write_normalized(
    requested_date: str,
) -> dict[str, Any]:
    payload = normalize_segments(requested_date)
    serialized = serialize_processed(payload)

    directory = PROCESSED_ROOT / requested_date
    output_path = directory / "segments.json"

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    if output_path.exists():
        existing = output_path.read_bytes()

        if existing != serialized:
            raise NormalizationError(
                "Existing processed output differs from "
                "deterministic normalization result"
            )

        return {
            "status": "EXISTS_DETERMINISTIC_PASS",
            "path": str(output_path),
            "processed_sha256": sha256_bytes(existing),
        }

    output_path.write_bytes(serialized)

    persisted = output_path.read_bytes()

    if persisted != serialized:
        raise NormalizationError(
            "Persisted processed output does not match "
            "normalization result"
        )

    return {
        "status": "NORMALIZED",
        "path": str(output_path),
        "processed_sha256": sha256_bytes(persisted),
    }
