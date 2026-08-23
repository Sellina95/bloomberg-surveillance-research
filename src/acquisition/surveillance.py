from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

import requests


RSS_URL = (
    "https://omny.fm/shows/"
    "bloomberg-surveillance/playlists/podcast.rss"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
}

RAW_ROOT = Path("data/raw/surveillance")


class AcquisitionError(RuntimeError):
    pass


class EpisodeNotFoundError(AcquisitionError):
    pass


class IntegrityError(AcquisitionError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def discover_episode(
    requested_date: str,
) -> dict[str, str]:
    target_date = datetime.strptime(
        requested_date,
        "%Y-%m-%d",
    ).date()

    response = requests.get(
        RSS_URL,
        headers=HEADERS,
        timeout=60,
    )
    response.raise_for_status()

    root = ET.fromstring(response.content)

    matches: list[dict[str, str]] = []

    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip()
        pub_raw = (item.findtext("pubDate") or "").strip()
        link = (item.findtext("link") or "").strip()
        guid = (item.findtext("guid") or "").strip()

        if not title.lower().startswith(
            "bloomberg surveillance tv"
        ):
            continue

        if not pub_raw or not link or not guid:
            continue

        pub_date = parsedate_to_datetime(pub_raw)

        if pub_date.tzinfo is None:
            pub_date = pub_date.replace(
                tzinfo=timezone.utc
            )

        pub_date_utc = pub_date.astimezone(
            timezone.utc
        )

        if pub_date_utc.date() != target_date:
            continue

        matches.append(
            {
                "requested_date": requested_date,
                "episode_title": title,
                "published_at": (
                    pub_date_utc.isoformat()
                ),
                "episode_guid": guid,
                "canonical_episode_url": link,
            }
        )

    if not matches:
        raise EpisodeNotFoundError(
            f"No Bloomberg Surveillance TV episode "
            f"found for {requested_date}"
        )

    if len(matches) != 1:
        raise AcquisitionError(
            f"Expected exactly one episode for "
            f"{requested_date}; found {len(matches)}"
        )

    return matches[0]


def discover_transcript_url(
    episode_url: str,
) -> str:
    response = requests.get(
        episode_url,
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()

    published_match = re.search(
        r'"HasPublishedTranscript":(true|false)',
        response.text,
        flags=re.IGNORECASE,
    )

    url_match = re.search(
        r'"TranscriptUrl":"([^"]+)"',
        response.text,
    )

    if (
        published_match is None
        or published_match.group(1).lower() != "true"
    ):
        raise AcquisitionError(
            "Episode does not have a published transcript"
        )

    if url_match is None:
        raise AcquisitionError(
            "Published transcript URL was not found"
        )

    return url_match.group(1)


def fetch_raw_transcript(
    transcript_url: str,
) -> bytes:
    response = requests.get(
        transcript_url,
        headers=HEADERS,
        timeout=60,
    )
    response.raise_for_status()

    # Validate that the upstream response is JSON,
    # but preserve the exact received bytes.
    try:
        payload: Any = response.json()
    except requests.JSONDecodeError as exc:
        raise AcquisitionError(
            "Transcript endpoint did not return valid JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise AcquisitionError(
            "Transcript JSON root is not an object"
        )

    if not payload.get("segments"):
        raise AcquisitionError(
            "Transcript contains no segments"
        )

    return response.content


def verify_existing_acquisition(
    transcript_path: Path,
    metadata_path: Path,
) -> None:
    if not transcript_path.exists():
        raise IntegrityError(
            "Metadata/raw acquisition state is incomplete: "
            "transcript.json missing"
        )

    if not metadata_path.exists():
        raise IntegrityError(
            "Metadata/raw acquisition state is incomplete: "
            "metadata.json missing"
        )

    raw_bytes = transcript_path.read_bytes()

    try:
        metadata = json.loads(
            metadata_path.read_text(
                encoding="utf-8"
            )
        )
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise IntegrityError(
            "metadata.json is invalid"
        ) from exc

    expected_hash = metadata.get(
        "transcript_sha256"
    )

    actual_hash = sha256_bytes(raw_bytes)

    if not expected_hash:
        raise IntegrityError(
            "metadata.json has no transcript_sha256"
        )

    if actual_hash != expected_hash:
        raise IntegrityError(
            "Stored transcript integrity check failed: "
            f"expected={expected_hash}, "
            f"actual={actual_hash}"
        )


def acquire(
    requested_date: str,
) -> dict[str, Any]:
    episode = discover_episode(requested_date)

    directory = RAW_ROOT / requested_date
    transcript_path = directory / "transcript.json"
    metadata_path = directory / "metadata.json"

    if transcript_path.exists() or metadata_path.exists():
        verify_existing_acquisition(
            transcript_path,
            metadata_path,
        )

        return {
            "status": "EXISTS_INTEGRITY_PASS",
            "directory": str(directory),
        }

    transcript_url = discover_transcript_url(
        episode["canonical_episode_url"]
    )

    raw_bytes = fetch_raw_transcript(
        transcript_url
    )

    transcript_hash = sha256_bytes(raw_bytes)

    acquired_at = datetime.now(
        timezone.utc
    ).isoformat()

    metadata = {
        "requested_date": requested_date,
        "program": "Bloomberg Surveillance TV",
        "episode_title": episode["episode_title"],
        "published_at": episode["published_at"],
        "episode_guid": episode["episode_guid"],
        "canonical_episode_url": (
            episode["canonical_episode_url"]
        ),
        "transcript_url": transcript_url,
        "acquired_at_utc": acquired_at,
        "transcript_sha256": transcript_hash,
        "transcript_bytes": len(raw_bytes),
    }

    # Build the complete acquisition unit in a temporary
    # sibling directory before publishing it canonically.
    #
    # This prevents a crash between transcript and metadata
    # writes from exposing a partially completed acquisition.
    RAW_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_directory = RAW_ROOT / (
        f".{requested_date}.tmp"
    )
    temp_transcript_path = (
        temp_directory / "transcript.json"
    )
    temp_metadata_path = (
        temp_directory / "metadata.json"
    )

    if temp_directory.exists():
        raise IntegrityError(
            "Temporary acquisition directory already exists: "
            f"{temp_directory}"
        )

    temp_directory.mkdir()

    try:
        temp_transcript_path.write_bytes(
            raw_bytes
        )

        temp_metadata_path.write_text(
            json.dumps(
                metadata,
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        # Verify the complete temporary acquisition before
        # making it visible at the canonical path.
        verify_existing_acquisition(
            temp_transcript_path,
            temp_metadata_path,
        )

        # Atomic directory rename on the same filesystem.
        # The canonical acquisition appears only after both
        # artifacts have been written and verified.
        temp_directory.rename(directory)

    except Exception:
        # Best-effort cleanup of an unpublished partial unit.
        if temp_transcript_path.exists():
            temp_transcript_path.unlink()

        if temp_metadata_path.exists():
            temp_metadata_path.unlink()

        if temp_directory.exists():
            temp_directory.rmdir()

        raise

    return {
        "status": "ACQUIRED",
        "directory": str(directory),
        "metadata": metadata,
    }
