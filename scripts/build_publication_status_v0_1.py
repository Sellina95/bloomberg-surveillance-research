from __future__ import annotations

import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SURVEILLANCE_ROOT = (
    ROOT / "data/processed/surveillance"
)

OUTPUT = (
    SURVEILLANCE_ROOT
    / "publication_status_v0_1.json"
)

EN_REPORT = "daily_research_report_v0_1.json"
EN_TV = "daily_research_report_tv_v0_1.html"

KO_REPORT = "daily_research_report_ko_v0_1.json"
KO_TV = "daily_research_report_tv_ko_v0_1.html"


def valid_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def publication_state(
    report_exists: bool,
    tv_exists: bool,
) -> str:
    if report_exists and tv_exists:
        return "available"

    if report_exists or tv_exists:
        return "incomplete"

    return "unavailable"


def main() -> None:
    records = []

    if not SURVEILLANCE_ROOT.exists():
        raise SystemExit(
            f"FAIL — surveillance root missing: "
            f"{SURVEILLANCE_ROOT}"
        )

    for date_dir in sorted(
        SURVEILLANCE_ROOT.iterdir()
    ):
        if not date_dir.is_dir():
            continue

        report_date = date_dir.name

        if not valid_date(report_date):
            continue

        en_report = (
            date_dir / EN_REPORT
        ).exists()

        en_tv = (
            date_dir / EN_TV
        ).exists()

        ko_report = (
            date_dir / KO_REPORT
        ).exists()

        ko_tv = (
            date_dir / KO_TV
        ).exists()

        en_status = publication_state(
            en_report,
            en_tv,
        )

        ko_status = publication_state(
            ko_report,
            ko_tv,
        )

        # A date belongs to the public calendar only
        # when an English TV publication exists.
        if en_status == "unavailable":
            continue

        records.append(
            {
                "date": report_date,
                "en": {
                    "status": en_status,
                    "report": en_report,
                    "tv": en_tv,
                },
                "ko": {
                    "status": ko_status,
                    "report": ko_report,
                    "tv": ko_tv,
                },
            }
        )

    payload = {
        "schema_version": "publication_status_v0_1",
        "dates": records,
    }

    OUTPUT.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print("=" * 100)
    print("PUBLICATION STATUS MANIFEST")
    print("=" * 100)
    print("OUTPUT:", OUTPUT.relative_to(ROOT))
    print("DATES :", len(records))

    for record in records:
        print(
            record["date"],
            "| EN:",
            record["en"]["status"],
            "| KO:",
            record["ko"]["status"],
        )

    print("=" * 100)
    print("RESULT: PASS")
    print("=" * 100)


if __name__ == "__main__":
    main()
