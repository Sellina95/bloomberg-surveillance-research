from __future__ import annotations

import calendar
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SURVEILLANCE_ROOT = (
    ROOT / "data/processed/surveillance"
)

STATUS_INPUT = (
    SURVEILLANCE_ROOT
    / "publication_status_v0_1.json"
)

EN_TV = "daily_research_report_tv_v0_1.html"
KO_TV = "daily_research_report_tv_ko_v0_1.html"

NAV_CACHE_TOKEN = "desk=v0_2"


def load_status() -> dict:
    if not STATUS_INPUT.exists():
        raise SystemExit(
            "FAIL — publication status manifest missing"
        )

    payload = json.loads(
        STATUS_INPUT.read_text(
            encoding="utf-8"
        )
    )

    if (
        payload.get("schema_version")
        != "publication_status_v0_1"
    ):
        raise SystemExit(
            "FAIL — unsupported publication status schema"
        )

    records = payload.get("dates")

    if not isinstance(records, list):
        raise SystemExit(
            "FAIL — invalid publication status dates"
        )

    return {
        item["date"]: item
        for item in records
        if isinstance(item, dict)
        and item.get("date")
    }


def build_navigation(
    status: dict,
    current_date: str,
    language: str,
) -> str:

    grouped = {}

    for report_date in sorted(status):
        year, month, day = map(
            int,
            report_date.split("-"),
        )

        grouped.setdefault(
            (year, month),
            [],
        ).append(
            (report_date, day)
        )

    month_blocks = []

    for (
        year,
        month,
    ), dates in sorted(
        grouped.items(),
        reverse=True,
    ):

        month_label = (
            f"{calendar.month_abbr[month].upper()} "
            f"{year}"
        )

        links = []

        for report_date, day in dates:

            record = status[report_date]

            ko_available = (
                record.get("ko", {}).get("status")
                == "available"
            )

            if (
                language == "ko"
                and ko_available
            ):
                target = KO_TV
            else:
                target = EN_TV

            current_class = (
                " nav-date-current"
                if report_date == current_date
                else ""
            )

            href = (
                "../"
                f"{report_date}/"
                f"{target}"
                f"?{NAV_CACHE_TOKEN}"
            )

            ko_indicator = (
                ""
                if ko_available
                else """
                    <span
                        class="nav-ko-unavailable"
                        title="Korean report temporarily unavailable"
                        aria-label="Korean report unavailable"
                    >
                        EN only
                    </span>
                """
            )

            links.append(
                f"""
                <div class="nav-date-cell">
                    <a
                        class="nav-date{current_class}"
                        href="{href}"
                        aria-label="{report_date}"
                    >
                        {day:02d}
                    </a>
                    {ko_indicator}
                </div>
                """
            )

        month_blocks.append(
            f"""
            <div class="nav-month">

                <div class="nav-month-label">
                    {month_label}
                </div>

                <div class="nav-date-grid">
                    {''.join(links)}
                </div>

            </div>
            """
        )

    return "".join(month_blocks)


def replace_navigation(
    html: str,
    navigation: str,
) -> str:

    pattern = re.compile(
        r'(<div\s+class="calendar-panel"\s+'
        r'id="calendarPanel"\s*>)'
        r'.*?'
        r'(\s*</div>\s*</div>\s*'
        r'<div\s+class="language-switch")',
        re.DOTALL,
    )

    match = pattern.search(html)

    if not match:
        raise ValueError(
            "calendar navigation block not found"
        )

    replacement = (
        match.group(1)
        + "\n"
        + navigation
        + "\n                </div>\n"
        + "\n            </div>\n"
        + "\n            <div class=\"language-switch\""
    )

    return (
        html[:match.start()]
        + replacement
        + html[match.end():]
    )



STATUS_STYLE = """
<style id="publication-status-nav-style">
.nav-date-cell {
    min-width: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 3px;
}

.nav-date-cell .nav-date {
    width: 100%;
}

.nav-ko-unavailable {
    display: block;
    white-space: nowrap;
    font-family:
        ui-monospace,
        SFMono-Regular,
        Menlo,
        monospace;
    font-size: 7px;
    font-weight: 700;
    line-height: 1;
    letter-spacing: 0.4px;
    color: #777a80;
    opacity: 0.8;
}
</style>
"""


def refresh_status_style(html: str) -> str:
    pattern = re.compile(
        r'<style\s+id="publication-status-nav-style">'
        r'.*?</style>',
        re.DOTALL,
    )

    if pattern.search(html):
        return pattern.sub(
            STATUS_STYLE.strip(),
            html,
            count=1,
        )

    if "</head>" not in html:
        raise ValueError(
            "HTML head closing tag not found"
        )

    return html.replace(
        "</head>",
        STATUS_STYLE + "\n</head>",
        1,
    )


def main() -> None:

    status = load_status()

    refreshed = 0
    skipped = 0

    for report_date in sorted(status):

        date_dir = (
            SURVEILLANCE_ROOT
            / report_date
        )

        targets = [
            ("en", date_dir / EN_TV),
            ("ko", date_dir / KO_TV),
        ]

        for language, html_path in targets:

            if not html_path.exists():
                continue

            html = html_path.read_text(
                encoding="utf-8"
            )

            navigation = build_navigation(
                status,
                report_date,
                language,
            )

            try:
                updated = replace_navigation(
                    html,
                    navigation,
                )

                updated = refresh_status_style(
                    updated
                )
            except ValueError as exc:
                print(
                    "SKIP:",
                    report_date,
                    language.upper(),
                    "—",
                    exc,
                )
                skipped += 1
                continue

            html_path.write_text(
                updated,
                encoding="utf-8",
            )

            print(
                "REFRESHED:",
                report_date,
                language.upper(),
            )

            refreshed += 1

    print("=" * 100)
    print("HISTORICAL NAVIGATION REFRESH")
    print("=" * 100)
    print("REFRESHED:", refreshed)
    print("SKIPPED  :", skipped)
    print("=" * 100)

    if skipped:
        raise SystemExit(
            "FAIL — one or more navigation blocks were not refreshed"
        )

    print("RESULT: PASS")
    print("=" * 100)


if __name__ == "__main__":
    main()
