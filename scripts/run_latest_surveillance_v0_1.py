from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

INVENTORY = (
    ROOT
    / "data/processed/surveillance/"
    / "surveillance_video_inventory_august_2026.json"
)

RUNNER = (
    ROOT
    / "scripts/youtube_daily_runner_v0_3.py"
)

KOREAN_BUILDER = (
    ROOT
    / "scripts/build_korean_presentation_v0_1.py"
)

TV_RENDERER = (
    ROOT
    / "scripts/render_daily_research_tv_v0_1.py"
)

HOME_BUILDER = (
    ROOT
    / "scripts/build_research_desk_home_v0_1.py"
)


def main() -> None:

    if not INVENTORY.exists():
        raise SystemExit(
            f"FAIL — inventory not found: {INVENTORY}"
        )

    if not RUNNER.exists():
        raise SystemExit(
            f"FAIL — daily runner not found: {RUNNER}"
        )

    if not KOREAN_BUILDER.exists():
        raise SystemExit(
            f"FAIL — Korean builder not found: {KOREAN_BUILDER}"
        )

    if not TV_RENDERER.exists():
        raise SystemExit(
            f"FAIL — TV renderer not found: {TV_RENDERER}"
        )

    if not HOME_BUILDER.exists():
        raise SystemExit(
            f"FAIL — Home builder not found: {HOME_BUILDER}"
        )

    inventory = json.loads(
        INVENTORY.read_text(
            encoding="utf-8"
        )
    )

    videos = inventory.get(
        "videos",
        []
    )

    candidates = []

    for video in videos:

        video_date = video.get(
            "video_date"
        )

        video_id = video.get(
            "video_id"
        )

        if not video_date or not video_id:
            continue

        try:
            parsed_date = date.fromisoformat(
                video_date[:10]
            )
        except ValueError:
            continue

        candidates.append(
            {
                "date":
                    parsed_date.isoformat(),
                "video_id":
                    video_id,
                "title":
                    video.get("title", ""),
            }
        )

    if not candidates:
        raise SystemExit(
            "FAIL — no valid videos in inventory"
        )

    selected = max(
        candidates,
        key=lambda x: x["date"]
    )

    run_date = selected["date"]
    video_id = selected["video_id"]

    print("=" * 100)
    print("LATEST BLOOMBERG SURVEILLANCE RUNNER v0.1")
    print("=" * 100)
    print("DATE:", run_date)
    print("VIDEO_ID:", video_id)
    print("TITLE:", selected["title"])
    print("=" * 100)

    env = os.environ.copy()

    env["SURVEILLANCE_DATE"] = run_date
    env["VIDEO_ID"] = video_id

    print()
    print("=" * 100)
    print("RUN DAILY PIPELINE")
    print("=" * 100)

    pipeline = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
        ],
        cwd=ROOT,
        env=env,
    )

    if pipeline.returncode != 0:
        raise SystemExit(
            "FAIL — daily pipeline failed"
        )

    print()
    print("=" * 100)
    print("BUILD KOREAN PRESENTATION")
    print("=" * 100)

    korean = subprocess.run(
        [
            sys.executable,
            str(KOREAN_BUILDER),
        ],
        cwd=ROOT,
        env=env,
    )

    korean_available = korean.returncode == 0

    if not korean_available:
        print(
            "WARNING — Korean presentation build failed. "
            "English publication will continue."
        )

    print()
    print("=" * 100)
    print("RUN TV RENDER")
    print("=" * 100)

    # English publication is mandatory.
    # Korean publication is rendered only after its validation passes.
    render_languages = ["en"]

    if korean_available:
        render_languages.append("ko")

    for lang in render_languages:
        render_env = env.copy()
        render_env["SURVEILLANCE_LANG"] = lang

        print()
        print(f"RENDER LANGUAGE: {lang.upper()}")

        tv = subprocess.run(
            [
                sys.executable,
                str(TV_RENDERER),
            ],
            cwd=ROOT,
            env=render_env,
        )

        if tv.returncode != 0:
            raise SystemExit(
                f"FAIL — TV render failed ({lang})"
            )

    print()
    print("=" * 100)
    print("BUILD PUBLICATION STATUS")
    print("=" * 100)

    publication_status_builder = subprocess.run(
        [
            sys.executable,
            str(
                ROOT
                / "scripts"
                / "build_publication_status_v0_1.py"
            ),
        ],
        cwd=ROOT,
        env=env,
    )

    if publication_status_builder.returncode != 0:
        raise SystemExit(
            "FAIL — publication status build failed"
        )

    print()
    print("=" * 100)
    print("REFRESH HISTORICAL TV NAVIGATION")
    print("=" * 100)

    navigation_refresh = subprocess.run(
        [
            sys.executable,
            str(
                ROOT
                / "scripts"
                / "refresh_historical_navigation_v0_1.py"
            ),
        ],
        cwd=ROOT,
        env=env,
    )

    if navigation_refresh.returncode != 0:
        raise SystemExit(
            "FAIL — historical navigation refresh failed"
        )

    print()
    print("=" * 100)
    print("REFRESH RESEARCH DESK HOME")
    print("=" * 100)

    home = subprocess.run(
        [
            sys.executable,
            str(HOME_BUILDER),
        ],
        cwd=ROOT,
        env=env,
    )

    if home.returncode != 0:
        raise SystemExit(
            "FAIL — Research Desk Home refresh failed"
        )

    output = (
        ROOT
        / f"data/processed/surveillance/"
        f"{run_date}/"
        f"daily_research_report_tv_v0_1.html"
    )

    print()
    print("=" * 100)
    print("LATEST SURVEILLANCE RUN COMPLETE")
    print("=" * 100)
    print("DATE:", run_date)
    print("VIDEO_ID:", video_id)
    print("TV:", output)
    print("STATUS: PASS")
    print("=" * 100)


if __name__ == "__main__":
    main()
