from __future__ import annotations

import json
import os
import re
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]

INVENTORY = (
    ROOT
    / "data/processed/surveillance"
    / "surveillance_video_inventory_august_2026.json"
)


def extract_video_id(url: str) -> str:
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower()

    if host.startswith("www."):
        host = host[4:]

    video_id = ""

    if host in {"youtube.com", "m.youtube.com"} and parsed.path == "/watch":
        values = parse_qs(parsed.query).get("v", [])
        if values:
            video_id = values[0]

    elif host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]

    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise ValueError("invalid YouTube video URL")

    return video_id


def build_source(report_date: str, source_url: str) -> dict:
    parsed_date = date.fromisoformat(report_date)

    if parsed_date > date.today():
        raise ValueError("manual source date cannot be in the future")

    video_id = extract_video_id(source_url)

    return {
        "video_id": video_id,
        "title": f"Bloomberg Surveillance manual source {report_date}",
        "link": f"https://www.youtube.com/watch?v={video_id}",
        "video_date": report_date,
        "broadcast_date": report_date,
        "broadcast_date_basis": "manual_verified_url",
        "published_date": "unknown_manual_override",
    }


def main() -> None:
    report_date = os.environ.get("MANUAL_SOURCE_DATE", "").strip()
    source_url = os.environ.get("MANUAL_SOURCE_URL", "").strip()

    if not report_date or not source_url:
        raise SystemExit(
            "MANUAL SOURCE OVERRIDE: FAIL — "
            "both date and URL are required"
        )

    try:
        source = build_source(report_date, source_url)
    except ValueError as exc:
        raise SystemExit(
            f"MANUAL SOURCE OVERRIDE: FAIL — {exc}"
        ) from exc

    INVENTORY.parent.mkdir(parents=True, exist_ok=True)
    INVENTORY.write_text(
        json.dumps(
            {
                "schema_version": "manual_source_override_v0_1",
                "videos": [source],
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print("MANUAL SOURCE OVERRIDE: PASS")
    print("DATE:", report_date)
    print("VIDEO_ID:", source["video_id"])


if __name__ == "__main__":
    main()
