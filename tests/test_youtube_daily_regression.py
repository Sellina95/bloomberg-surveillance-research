from __future__ import annotations

import json
import subprocess
from pathlib import Path


CASES = [
    {
        "date": "2026-08-10",
        "video_id": "8j3SSyrHU2Y",
        "expected_chapters": 13,
        "expected_transcript": 2284,
        "expected_guests": 11,
    },
    {
        "date": "2026-08-14",
        "video_id": "qWYTenEUdFc",
        "expected_chapters": 14,
        "expected_transcript": 2316,
        "expected_guests": 13,
    },
]


RUNNER = Path(
    "scripts/youtube_daily_runner.py"
)

BASE = Path(
    "data/processed/surveillance"
)


def run_case(case: dict) -> bool:

    date = case["date"]
    video_id = case["video_id"]

    print("-" * 100)
    print(
        f"REGRESSION | {date} | {video_id}"
    )

    result = subprocess.run(
        [
            "python",
            str(RUNNER),
            "--date",
            date,
            "--video-id",
            video_id,
        ],
        text=True,
        capture_output=True,
    )

    print(result.stdout)

    if result.returncode != 0:
        print(result.stderr)
        print("RESULT: FAIL — runner error")
        return False

    artifact = (
        BASE
        / date
        / "youtube_canonical.json"
    )

    guest_artifact = (
        BASE
        / date
        / "guest_units.json"
    )

    if not artifact.exists():
        print(
            "RESULT: FAIL — canonical artifact missing"
        )
        return False

    if not guest_artifact.exists():
        print(
            "RESULT: FAIL — guest artifact missing"
        )
        return False

    canonical = json.loads(
        artifact.read_text(
            encoding="utf-8"
        )
    )

    guests = json.loads(
        guest_artifact.read_text(
            encoding="utf-8"
        )
    )

    checks = {
        "chapters":
            canonical["chapter_count"]
            == case["expected_chapters"],

        "transcript":
            canonical["transcript_segment_count"]
            == case["expected_transcript"],

        "coverage":
            canonical["coverage_minutes"]
            > 120,

        "guests":
            guests["guest_count"]
            == case["expected_guests"],

        "video_id":
            canonical["video_id"]
            == video_id,
    }

    for name, passed in checks.items():
        print(
            f"{name.upper():12s}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

    passed = all(checks.values())

    print(
        "REGRESSION RESULT:",
        "PASS" if passed else "FAIL",
    )

    return passed


def main() -> None:

    print("=" * 100)
    print("YOUTUBE DAILY INGESTION REGRESSION")
    print("=" * 100)

    results = [
        run_case(case)
        for case in CASES
    ]

    print()
    print("=" * 100)

    if all(results):
        print(
            "REGRESSION: PASS"
        )
        print(
            "CASES: "
            f"{len(results)}/{len(results)}"
        )
    else:
        print(
            "REGRESSION: FAIL"
        )

    print("=" * 100)

    raise SystemExit(
        0 if all(results) else 1
    )


if __name__ == "__main__":
    main()
