from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.run_atomic_publication_v0_1 import validate_daily_source_date


validate_daily_source_date(
    "2026-09-08",
    newest_date="2026-09-04",
    today=date(2026, 9, 9),
)

try:
    validate_daily_source_date(
        "2023-02-15",
        newest_date="2026-09-04",
        today=date(2026, 9, 9),
    )
except SystemExit as exc:
    assert "SOURCE FRESHNESS CONTRACT: FAIL" in str(exc)
else:
    raise AssertionError("daily mode must reject an archive source")

validate_daily_source_date(
    "2023-02-15",
    newest_date="2026-09-04",
    today=date(2026, 9, 9),
    allow_historical=True,
)

print("DAILY SOURCE FRESHNESS CONTRACT: PASS")
