from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


VIDEO_ID = os.environ.get("VIDEO_ID")
DATE = os.environ.get("SURVEILLANCE_DATE")

if not VIDEO_ID or not DATE:
    raise SystemExit(
        "ERROR: set VIDEO_ID and SURVEILLANCE_DATE"
    )


BASE = Path(
    f"data/processed/surveillance/{DATE}"
)

BASE.mkdir(
    parents=True,
    exist_ok=True
)


VIDEO_URL = (
    f"https://www.youtube.com/watch?v={VIDEO_ID}"
)


def run(
    script: str,
    extra_env: dict | None = None,
):
    env = os.environ.copy()

    if extra_env:
        env.update(extra_env)

    print()
    print("=" * 100)
    print("RUN:", script)
    print("=" * 100)

    result = subprocess.run(
        [
            sys.executable,
            script,
        ],
        env=env,
    )

    if result.returncode != 0:
        raise SystemExit(
            f"FAILED: {script}"
        )


print("=" * 100)
print("BLOOMBERG SURVEILLANCE DAILY RUNNER v0.1")
print("=" * 100)
print("DATE:", DATE)
print("VIDEO:", VIDEO_URL)
print("=" * 100)


# ------------------------------------------------------------------
# 1. Existing ingestion / canonical build
# ------------------------------------------------------------------

run(
    "tests/build_youtube_canonical_v0_2.py",
    {
        "VIDEO_ID": VIDEO_ID,
        "SURVEILLANCE_DATE": DATE,
    },
)


# ------------------------------------------------------------------
# 2. Guest unit construction
# ------------------------------------------------------------------

run(
    "tests/build_guest_units_v0_3.py",
    {
        "SURVEILLANCE_DATE": DATE,
    },
)


# ------------------------------------------------------------------
# 3. Evidence-grounded Gemini research summary
# ------------------------------------------------------------------

run(
    "scripts/generate_research_summaries_gemini_v0_2.py",
    {
        "SURVEILLANCE_DATE": DATE,
    },
)


# ------------------------------------------------------------------
# 4. Final research dataset
# ------------------------------------------------------------------

run(
    "scripts/build_research_dataset_v0_1.py",
    {
        "SURVEILLANCE_DATE": DATE,
    },
)


# ------------------------------------------------------------------
# 5. Human-readable dashboard
# ------------------------------------------------------------------

run(
    "scripts/build_research_dashboard_v0_1.py",
    {
        "SURVEILLANCE_DATE": DATE,
    },
)


# ------------------------------------------------------------------
# 6. Verify expected artifacts
# ------------------------------------------------------------------

expected = [
    BASE / "youtube_canonical.json",
    BASE / "guest_units.json",
    BASE / "research_summaries_gemini_v0_2.json",
    BASE / "research_dataset_v0_1.json",
    BASE / "research_dashboard.html",
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
    print(" -", path)

print("=" * 100)
