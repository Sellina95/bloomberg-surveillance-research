from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


DATE = os.environ.get("SURVEILLANCE_DATE")
VIDEO_ID = os.environ.get("VIDEO_ID")

if not DATE:
    raise SystemExit("FAIL — SURVEILLANCE_DATE is not set")

if not VIDEO_ID:
    raise SystemExit("FAIL — VIDEO_ID is not set")


BASE = Path(
    f"data/processed/surveillance/{DATE}"
)


def run(script: str) -> None:

    print()
    print("=" * 100)
    print("RUN:", script)
    print("=" * 100)

    result = subprocess.run(
        [sys.executable, script],
        env=os.environ.copy(),
    )

    if result.returncode != 0:
        raise SystemExit(
            f"FAIL — {script}"
        )


print("=" * 100)
print("BLOOMBERG SURVEILLANCE DAILY RUNNER v0.3")
print("=" * 100)
print("DATE:", DATE)
print("VIDEO_ID:", VIDEO_ID)
print("=" * 100)


# 1. Raw transcript ingestion
run(
    "tests/run_youtube_daily_ingestion_v0_1.py"
)


# 2. Canonical transcript / chapter build
run(
    "tests/build_youtube_canonical_v0_2.py"
)


# 3. Guest unit construction
run(
    "tests/build_guest_units_v0_3.py"
)


# 4. Guest-level evidence-grounded research summaries
run(
    "scripts/generate_research_summaries_gemini_v0_2.py"
)


# 5. Structured research dataset
run(
    "scripts/build_research_dataset_v0_1.py"
)


# 6. Daily cross-guest research synthesis
run(
    "scripts/build_daily_research_report_v0_1.py"
)


# 7. Human-readable Markdown report
run(
    "scripts/render_daily_research_report_v0_1.py"
)


# 8. Final artifact verification
expected = [
    BASE / "youtube_canonical.json",
    BASE / "guest_units.json",
    BASE / "research_summaries_gemini_v0_2.json",
    BASE / "research_dataset_v0_1.json",
    BASE / "daily_research_report_v0_1.json",
    BASE / "daily_research_report_v0_1.md",
]


missing = [
    str(path)
    for path in expected
    if not path.exists()
]


print()
print("=" * 100)
print("DAILY PIPELINE RESULT")
print("=" * 100)


if missing:

    print("STATUS: FAIL")

    print()
    print("MISSING ARTIFACTS:")

    for path in missing:
        print(" -", path)

    raise SystemExit(1)


print("STATUS: PASS")
print("DATE:", DATE)
print("VIDEO_ID:", VIDEO_ID)

print()
print("ARTIFACTS:")

for path in expected:
    print("PASS:", path)


print()
print("=" * 100)
print("BLOOMBERG SURVEILLANCE DAILY REPORT COMPLETE")
print("=" * 100)
