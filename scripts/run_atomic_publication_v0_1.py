from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.publication.atomic_release import promote_date, promote_file

INVENTORY = ROOT / "data/processed/surveillance/surveillance_video_inventory_august_2026.json"
PUBLIC_ROOT = ROOT / "data/processed/surveillance"
MAX_DAILY_SOURCE_AGE_DAYS = 7


def latest_source() -> dict:
    if not INVENTORY.exists():
        raise SystemExit("SOURCE DISCOVERY CONTRACT: FAIL — inventory missing")
    videos = json.loads(INVENTORY.read_text(encoding="utf-8")).get("videos", [])
    valid = [row for row in videos if row.get("video_date") and row.get("video_id")]
    if not valid:
        raise SystemExit("SOURCE DISCOVERY CONTRACT: FAIL — inventory empty")
    return max(valid, key=lambda row: row["video_date"])


def newest_public_date() -> str:
    dates = [
        path.name
        for path in PUBLIC_ROOT.iterdir()
        if path.is_dir()
        and len(path.name) == 10
        and (path / "daily_research_report_v0_1.json").exists()
    ]
    return max(dates, default="")


def validate_daily_source_date(
    report_date: str,
    *,
    newest_date: str,
    today: date | None = None,
    allow_historical: bool = False,
) -> None:
    if allow_historical:
        return
    try:
        selected = date.fromisoformat(report_date)
    except ValueError as exc:
        raise SystemExit("SOURCE FRESHNESS CONTRACT: FAIL — invalid source date") from exc
    anchor = today or date.today()
    age_days = (anchor - selected).days
    if age_days < 0 or age_days > MAX_DAILY_SOURCE_AGE_DAYS:
        raise SystemExit(
            "SOURCE FRESHNESS CONTRACT: FAIL — selected source is outside "
            f"the daily window: {report_date}"
        )
    if newest_date and report_date < newest_date:
        raise SystemExit(
            "SOURCE FRESHNESS CONTRACT: FAIL — daily discovery regressed "
            f"from {newest_date} to {report_date}"
        )


def main() -> None:
    source = latest_source()
    report_date = source["video_date"]
    validate_daily_source_date(
        report_date,
        newest_date=newest_public_date(),
        allow_historical=os.environ.get("ALLOW_HISTORICAL_BACKFILL") == "1",
    )
    existing = PUBLIC_ROOT / report_date
    legacy_required = (
        "daily_research_report_v0_1.json",
        "daily_research_report_v0_1.md",
        "daily_research_report_ko_v0_1.json",
        "daily_research_report_tv_v0_1.html",
        "daily_research_report_tv_ko_v0_1.html",
    )
    if all((existing / name).exists() for name in legacy_required):
        print("PUBLICATION ALREADY COMPLETE — SKIP REGENERATION")
        print("DATE:", report_date)
        return
    if existing.exists():
        raise SystemExit("ATOMIC PUBLICATION CONTRACT: FAIL — partial canonical date exists")

    with tempfile.TemporaryDirectory(prefix="surveillance-release-") as temporary:
        stage_repo = Path(temporary) / "repo"
        shutil.copytree(ROOT, stage_repo, ignore=shutil.ignore_patterns(".git", "_site", "__pycache__"))
        env = os.environ.copy()
        env.update({
            "SURVEILLANCE_DATE": report_date,
            "VIDEO_ID": source["video_id"],
            "SOURCE_BROADCAST_TITLE": source.get("title", ""),
            "SOURCE_BROADCAST_DATE": source.get("broadcast_date", report_date),
            "SOURCE_BROADCAST_DATE_BASIS": source.get(
                "broadcast_date_basis", "provider_broadcast_date"
            ),
            "SOURCE_UPLOAD_DATE": source.get("published_date", ""),
            "SOURCE_VIDEO_URL": source.get("link", ""),
        })
        subprocess.run(
            [sys.executable, "scripts/run_latest_surveillance_v0_1.py"],
            cwd=stage_repo,
            env=env,
            check=True,
        )
        subprocess.run(
            [sys.executable, "scripts/validate_release_candidate_v0_1.py"],
            cwd=stage_repo,
            env=env,
            check=True,
        )

        staged_public = stage_repo / "data/processed/surveillance"
        promote_date(
            staged_public,
            PUBLIC_ROOT,
            report_date,
            validate=lambda: None,
        )
        for name in ("publication_status_v0_1.json", "index.html"):
            promote_file(staged_public / name, PUBLIC_ROOT / name)

    print("ATOMIC PUBLICATION CONTRACT: PASS")


if __name__ == "__main__":
    main()
