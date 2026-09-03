from __future__ import annotations

import json
import os
import runpy
import tempfile
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
DATE = "2099-01-02"
VIDEO_ID = "canonical-path-test-video"


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def run_case(chapters: list[dict]) -> tuple[dict, dict]:
    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)
        raw = work / f"data/raw/youtube/{DATE}"
        raw.mkdir(parents=True)

        transcript = {
            "content": [
                {
                    "offset": 0,
                    "duration": 600_000,
                    "text": "First source-grounded segment.",
                    "lang": "en",
                },
                {
                    "offset": 600_000,
                    "duration": 600_000,
                    "text": "Second source-grounded segment.",
                    "lang": "en",
                },
            ]
        }
        (raw / "transcript.json").write_text(
            json.dumps(transcript),
            encoding="utf-8",
        )

        previous = Path.cwd()
        os.chdir(work)
        try:
            with patch.dict(
                os.environ,
                {
                    "SURVEILLANCE_DATE": DATE,
                    "VIDEO_ID": VIDEO_ID,
                    "SERPAPI_API_KEY": "test-key",
                },
                clear=False,
            ), patch(
                "urllib.request.urlopen",
                return_value=FakeResponse({"chapters": chapters}),
            ):
                runpy.run_path(
                    str(ROOT / "tests/build_youtube_canonical_v0_2.py")
                )
                runpy.run_path(
                    str(ROOT / "tests/build_guest_units_v0_3.py")
                )
        finally:
            os.chdir(previous)

        base = work / f"data/processed/surveillance/{DATE}"
        canonical = json.loads(
            (base / "youtube_canonical_v0_2.json").read_text(
                encoding="utf-8"
            )
        )
        units = json.loads(
            (base / "guest_units_v0_3.json").read_text(
                encoding="utf-8"
            )
        )

        return canonical, units


canonical, units = run_case([])

assert canonical["chapter_mode"] == "full_program_fallback"
assert canonical["chapter_count"] == 1
assert canonical["unassigned_segments"] == 0
assert units["guest_chapter_count"] == 0
assert len(units["guest_units"]) == 1
assert units["guest_units"][0]["guest"] is None
assert units["guest_units"][0]["attribution_status"] == "unavailable"


canonical, units = run_case(
    [
        {
            "title": "Market outlook — Jane Doe, Example",
            "time_start": 0,
        },
        {
            "title": "Rates outlook — John Roe, Example",
            "time_start": 600,
        },
    ]
)

assert canonical["chapter_mode"] == "source_chapters"
assert canonical["chapter_count"] == 2
assert canonical["unassigned_segments"] == 0
assert units["guest_chapter_count"] == 2
assert len(units["guest_units"]) == 2
assert all(
    unit["attribution_status"] == "source_chapter"
    for unit in units["guest_units"]
)

print("CANONICAL CHAPTER MODES: PASS")
