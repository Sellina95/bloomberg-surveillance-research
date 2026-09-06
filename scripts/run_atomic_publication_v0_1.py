from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.publication.atomic_release import promote_date, promote_file

INVENTORY = ROOT / "data/processed/surveillance/surveillance_video_inventory_august_2026.json"
PUBLIC_ROOT = ROOT / "data/processed/surveillance"


def latest_source() -> dict:
    if not INVENTORY.exists():
        raise SystemExit("SOURCE DISCOVERY CONTRACT: FAIL — inventory missing")
    videos = json.loads(INVENTORY.read_text(encoding="utf-8")).get("videos", [])
    valid = [row for row in videos if row.get("video_date") and row.get("video_id")]
    if not valid:
        raise SystemExit("SOURCE DISCOVERY CONTRACT: FAIL — inventory empty")
    return max(valid, key=lambda row: row["video_date"])


def main() -> None:
    source = latest_source()
    report_date = source["video_date"]
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
