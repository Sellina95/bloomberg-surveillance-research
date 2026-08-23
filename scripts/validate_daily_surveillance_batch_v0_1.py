from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path


INVENTORY = Path(
    "data/processed/surveillance/"
    "surveillance_video_inventory_august_2026.json"
)

START_DATE = date(2026, 8, 18)
END_DATE = date(2026, 8, 24)

RUNNER = Path(
    "scripts/youtube_daily_runner_v0_3.py"
)

TV_RENDERER = Path(
    "scripts/render_daily_research_tv_v0_1.py"
)

RESULT = Path(
    "data/processed/surveillance/"
    "daily_batch_validation_v0_1.json"
)


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


if not INVENTORY.exists():
    raise SystemExit(
        f"FAIL — inventory not found: {INVENTORY}"
    )

if not RUNNER.exists():
    raise SystemExit(
        f"FAIL — runner not found: {RUNNER}"
    )

if not TV_RENDERER.exists():
    raise SystemExit(
        f"FAIL — TV renderer not found: {TV_RENDERER}"
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

selected = []

for video in videos:

    raw_date = video.get("video_date")

    video_id = (
        video.get("video_id")
        or video.get("id")
    )

    if not raw_date or not video_id:
        continue

    try:
        video_date = parse_date(
            raw_date[:10]
        )
    except ValueError:
        continue

    if START_DATE <= video_date <= END_DATE:

        selected.append(
            {
                "date": video_date.isoformat(),
                "video_id": video_id,
                "title": video.get(
                    "title",
                    "",
                ),
            }
        )


selected.sort(
    key=lambda x: x["date"]
)


print("=" * 100)
print("DAILY SURVEILLANCE BATCH VALIDATION v0.1")
print("=" * 100)
print(
    "RANGE:",
    START_DATE,
    "->",
    END_DATE,
)
print(
    "VIDEOS SELECTED:",
    len(selected),
)
print("=" * 100)

for item in selected:
    print(
        item["date"],
        "|",
        item["video_id"],
        "|",
        item["title"],
    )

if not selected:
    raise SystemExit(
        "FAIL — no videos found in requested range"
    )


results = []


for index, item in enumerate(
    selected,
    start=1,
):

    run_date = item["date"]
    video_id = item["video_id"]

    print()
    print("=" * 100)
    print(
        f"DAY {index}/{len(selected)}"
    )
    print(
        "DATE:",
        run_date,
    )
    print(
        "VIDEO_ID:",
        video_id,
    )
    print("=" * 100)

    env = os.environ.copy()

    env["SURVEILLANCE_DATE"] = run_date
    env["VIDEO_ID"] = video_id

    record = {
        "date": run_date,
        "video_id": video_id,
        "title": item["title"],
        "pipeline": "NOT_RUN",
        "tv_render": "NOT_RUN",
    }

    try:

        pipeline = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
            ],
            env=env,
        )

        if pipeline.returncode != 0:

            record["pipeline"] = "FAIL"

            results.append(record)

            print(
                "PIPELINE: FAIL"
            )

            continue

        record["pipeline"] = "PASS"

        tv = subprocess.run(
            [
                sys.executable,
                str(TV_RENDERER),
            ],
            env=env,
        )

        if tv.returncode != 0:

            record["tv_render"] = "FAIL"

            results.append(record)

            print(
                "TV RENDER: FAIL"
            )

            continue

        record["tv_render"] = "PASS"

        results.append(record)

        print(
            "PIPELINE: PASS"
        )
        print(
            "TV RENDER: PASS"
        )

    except Exception as exc:

        record["pipeline"] = "FAIL"
        record["error"] = str(exc)

        results.append(record)

        print(
            "EXCEPTION:",
            exc,
        )


pass_count = sum(
    1
    for r in results
    if r["pipeline"] == "PASS"
    and r["tv_render"] == "PASS"
)

fail_count = len(results) - pass_count


output = {
    "schema_version":
        "daily_batch_validation_v0_1",
    "range": {
        "start": START_DATE.isoformat(),
        "end": END_DATE.isoformat(),
    },
    "selected_count": len(selected),
    "pass_count": pass_count,
    "fail_count": fail_count,
    "results": results,
}


RESULT.write_text(
    json.dumps(
        output,
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)


print()
print("=" * 100)
print("BATCH VALIDATION RESULT")
print("=" * 100)
print(
    "SELECTED:",
    len(selected),
)
print(
    "PASS:",
    pass_count,
)
print(
    "FAIL:",
    fail_count,
)
print(
    "OUTPUT:",
    RESULT,
)
print("=" * 100)

if fail_count:
    print(
        "BATCH VALIDATION: REVIEW"
    )
    raise SystemExit(1)

print(
    "BATCH VALIDATION: PASS"
)
