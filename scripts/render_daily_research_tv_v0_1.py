from __future__ import annotations

import calendar
import json
import os
from html import escape
from pathlib import Path


DATE = os.environ.get(
    "SURVEILLANCE_DATE",
    "2026-08-14",
)

BASE = Path(
    f"data/processed/surveillance/{DATE}"
)

LANG = os.environ.get(
    "SURVEILLANCE_LANG",
    "en",
).strip().lower()

if LANG not in {
    "en",
    "ko",
}:
    raise SystemExit(
        f"FAIL — unsupported SURVEILLANCE_LANG: {LANG}"
    )

REPORT_FILENAME_EN = (
    "daily_research_report_v0_1.json"
)

REPORT_FILENAME_KO = (
    "daily_research_report_ko_v0_1.json"
)

TV_FILENAME_EN = (
    "daily_research_report_tv_v0_1.html"
)

TV_FILENAME_KO = (
    "daily_research_report_tv_ko_v0_1.html"
)

# Deterministic browser-cache identity for Research Desk navigation.
#
# IMPORTANT:
# - Do not use timestamps or random values here.
# - Rendered HTML must remain exact-byte deterministic.
# - Increment only when the public navigation shell contract changes.
NAV_CACHE_TOKEN = "desk=v0_1"

if LANG == "ko":
    INPUT = BASE / REPORT_FILENAME_KO
    OUTPUT = BASE / TV_FILENAME_KO
else:
    INPUT = BASE / REPORT_FILENAME_EN
    OUTPUT = BASE / TV_FILENAME_EN

PROVENANCE_INPUT = (
    BASE / "report_provenance_v0_1.json"
)


if not INPUT.exists():
    raise SystemExit(
        f"FAIL — input not found: {INPUT}"
    )


report = json.loads(
    INPUT.read_text(
        encoding="utf-8"
    )
)

# Korean presentation artifacts wrap the translated canonical
# report under "report". Normalize it here so the renderer uses
# the same input contract for EN and KO.
if LANG == "ko":
    wrapped_report = report.get("report")
    if not isinstance(wrapped_report, dict):
        raise SystemExit(
            "FAIL — Korean presentation missing report object"
        )
    report = wrapped_report


if PROVENANCE_INPUT.exists():
    provenance = json.loads(
        PROVENANCE_INPUT.read_text(
            encoding="utf-8"
        )
    )
else:
    provenance = {
        "mappings": []
    }


provenance_by_target = {
    item.get("target_id"): item
    for item in provenance.get(
        "mappings",
        []
    )
    if item.get("target_id")
}


SURVEILLANCE_ROOT = Path(
    "data/processed/surveillance"
)

def discover_public_tv_dates():

    dates = []

    if not SURVEILLANCE_ROOT.exists():
        return dates

    for date_dir in sorted(
        SURVEILLANCE_ROOT.iterdir()
    ):

        if not date_dir.is_dir():
            continue

        date = date_dir.name

        parts = date.split("-")

        if (
            len(parts) != 3
            or not all(
                part.isdigit()
                for part in parts
            )
        ):
            continue

        en_tv = (
            date_dir / TV_FILENAME_EN
        )

        ko_tv = (
            date_dir / TV_FILENAME_KO
        )

        if LANG == "ko":
            available = (
                ko_tv.exists()
                or en_tv.exists()
            )
        else:
            available = en_tv.exists()

        if available:

            dates.append(date)

    return dates


PUBLICATION_STATUS_INPUT = (
    SURVEILLANCE_ROOT
    / "publication_status_v0_1.json"
)


def load_publication_status():

    if not PUBLICATION_STATUS_INPUT.exists():
        return None

    try:
        payload = json.loads(
            PUBLICATION_STATUS_INPUT.read_text(
                encoding="utf-8"
            )
        )
    except (json.JSONDecodeError, OSError):
        return None

    if (
        payload.get("schema_version")
        != "publication_status_v0_1"
    ):
        return None

    records = payload.get("dates")

    if not isinstance(records, list):
        return None

    return {
        item.get("date"): item
        for item in records
        if isinstance(item, dict)
        and item.get("date")
    }


PUBLICATION_STATUS = (
    load_publication_status()
)


if PUBLICATION_STATUS is not None:
    PUBLIC_TV_DATES = sorted(
        PUBLICATION_STATUS.keys()
    )
else:
    # Backward-compatible fallback.
    PUBLIC_TV_DATES = (
        discover_public_tv_dates()
    )


def publication_language_status(
    report_date: str,
    language: str,
) -> str:

    if PUBLICATION_STATUS is None:
        target_dir = (
            SURVEILLANCE_ROOT
            / report_date
        )

        if language == "ko":
            available = (
                target_dir
                / TV_FILENAME_KO
            ).exists()
        else:
            available = (
                target_dir
                / TV_FILENAME_EN
            ).exists()

        return (
            "available"
            if available
            else "unavailable"
        )

    record = PUBLICATION_STATUS.get(
        report_date,
        {}
    )

    language_record = record.get(
        language,
        {}
    )

    return language_record.get(
        "status",
        "unavailable",
    )


def language_switch_html() -> str:
    if LANG == "en":
        if (BASE / TV_FILENAME_KO).exists():
            return f"""
            <span
                class="lang-option lang-active"
            >
                EN
            </span>

            <a
                class="lang-option"
                href="{e(TV_FILENAME_KO + '?' + NAV_CACHE_TOKEN)}"
            >
                한국어
            </a>
            """

        return """
        <span
            class="lang-option lang-active"
        >
            EN
        </span>

        <span
            class="lang-option lang-disabled"
            title="Korean presentation not available"
        >
            한국어
        </span>
        """

    return f"""
    <a
        class="lang-option"
        href="{e(TV_FILENAME_EN + '?' + NAV_CACHE_TOKEN)}"
    >
        EN
    </a>

    <span
        class="lang-option lang-active"
    >
        한국어
    </span>
    """


def navigation_html():

    grouped = {}

    for date in PUBLIC_TV_DATES:

        year, month, day = map(
            int,
            date.split("-")
        )

        grouped.setdefault(
            (year, month),
            [],
        ).append(
            (date, day)
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

        for date, day in dates:

            current_class = (
                " nav-date-current"
                if date == DATE
                else ""
            )

            target_dir = (
                SURVEILLANCE_ROOT
                / date
            )

            ko_status = (
                publication_language_status(
                    date,
                    "ko",
                )
            )

            if (
                LANG == "ko"
                and ko_status == "available"
            ):
                target_filename = (
                    TV_FILENAME_KO
                )
            else:
                target_filename = (
                    TV_FILENAME_EN
                )

            href = (
                "../"
                f"{date}/"
                f"{target_filename}"
                f"?{NAV_CACHE_TOKEN}"
            )

            ko_available = (
                publication_language_status(
                    date,
                    "ko",
                )
                == "available"
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
                    KO —
                </span>
                """
            )

            links.append(
                f'''
                <div class="nav-date-cell">
                    <a
                        class="nav-date{current_class}"
                        href="{e(href)}"
                        aria-label="{e(date)}"
                    >
                        {day:02d}
                    </a>
                    {ko_indicator}
                </div>
                '''
            )

        month_blocks.append(
            f'''
            <div class="nav-month">

                <div class="nav-month-label">
                    {e(month_label)}
                </div>

                <div class="nav-date-grid">
                    {"".join(links)}
                </div>

            </div>
            '''
        )

    return "".join(month_blocks)


def e(value):
    if value is None:
        return ""
    return escape(str(value))


def list_items(items):
    if not items:
        return "<div class='empty'>No data</div>"

    return "".join(
        f"<li>{e(item)}</li>"
        for item in items
    )


def provenance_badge(mapping):
    if not mapping:
        return ""

    audit_status = mapping.get(
        "audit_status",
        ""
    )

    provenance_type = mapping.get(
        "provenance_type",
        ""
    )

    status_class = (
        "prov-review"
        if audit_status == "REVIEW"
        else "prov-approved"
    )

    return f"""
    <div class="prov-badges">
        <span class="prov-badge {status_class}">
            {e(audit_status)}
        </span>

        <span class="prov-badge prov-type">
            {e(
                provenance_type.replace(
                    "_",
                    " "
                )
            )}
        </span>
    </div>
    """


def provenance_details(target_id):
    mapping = provenance_by_target.get(
        target_id
    )

    if not mapping:
        return ""

    claim_ids = mapping.get(
        "claim_ids",
        []
    )

    claim_html = "".join(
        f"<span class='claim-id'>{e(cid)}</span>"
        for cid in claim_ids
    )

    over_attribution = (
        mapping.get(
            "declared_guest_support_status"
        )
        == "OVER_ATTRIBUTION_DETECTED"
    )

    warning = ""

    if over_attribution:
        warning = """
        <div class="prov-warning">
            OVER-ATTRIBUTION DETECTED
        </div>
        """

    return f"""
    <div class="provenance-block">

        {provenance_badge(mapping)}

        {warning}

        <details class="provenance-details">

            <summary>
                PROVENANCE ·
                {len(claim_ids)}
                GROUNDED CLAIMS
            </summary>

            <div class="claim-list">
                {claim_html}
            </div>

            <div class="prov-note">
                Source references only.
                Transcript and evidence text remain private.
            </div>

        </details>

    </div>
    """


def market_section(title, key):
    section = report.get(key, {})

    summary = e(
        section.get("summary", "")
    )

    views = section.get(
        "key_views",
        []
    )

    risks = section.get(
        "risks",
        []
    )

    return f"""
    <section class="market-card">
        <div class="section-title">
            {e(title)}
        </div>

        <p class="summary">
            {summary}
        </p>

        <h4>KEY VIEWS</h4>
        <ul>
            {list_items(views)}
        </ul>

        <h4>RISKS</h4>
        <ul>
            {list_items(risks)}
        </ul>
    </section>
    """


def build_html():

    executive = list_items(
        report.get(
            "executive_summary",
            []
        )
    )

    macro = report.get(
        "macro_themes",
        []
    )

    macro_html = ""

    for theme in macro:

        evidence_html = ""

        for ev in theme.get(
            "evidence",
            []
        ):

            if isinstance(ev, dict):

                ts = ev.get(
                    "timestamp_seconds"
                )

                if ts is not None:
                    minutes = int(ts // 60)
                    seconds = int(ts % 60)
                    stamp = (
                        f"{minutes:02d}:{seconds:02d}"
                    )
                else:
                    stamp = "N/A"

                evidence_html += f"""
                <div class="evidence">
                    <span class="timestamp">
                        {e(stamp)}
                    </span>
                    <span>
                        {e(ev.get("text"))}
                    </span>
                </div>
                """

        macro_html += f"""
        <div class="macro-card">
            <h3>{e(theme.get("theme"))}</h3>

            <p>
                {e(theme.get("summary"))}
            </p>

            <div class="guest-row">
                {" ".join(
                    f'<span class="guest">{e(g)}</span>'
                    for g in theme.get(
                        "supporting_guests",
                        []
                    )
                )}
            </div>

            {evidence_html}
        </div>
        """

    consensus = report.get(
        "cross_guest_consensus",
        []
    )

    consensus_html = ""

    for i, item in enumerate(
        consensus,
        1,
    ):

        target_id = (
            f"CONSENSUS-{i:02d}"
        )

        consensus_html += f"""
        <div class="insight">
            <strong>
                {e(item.get("view"))}
            </strong>

            <div class="small">
                Guests:
                {", ".join(
                    e(g)
                    for g in item.get(
                        "guests",
                        []
                    )
                )}
            </div>

            {provenance_details(target_id)}
        </div>
        """

    conflicts = report.get(
        "cross_guest_conflicts",
        []
    )

    conflicts_html = ""

    for i, item in enumerate(
        conflicts,
        1,
    ):

        view_a_id = (
            f"CONFLICT-{i:02d}-VIEW_A"
        )

        view_b_id = (
            f"CONFLICT-{i:02d}-VIEW_B"
        )

        conflicts_html += f"""
        <div class="conflict">
            <strong>
                {e(item.get("topic"))}
            </strong>

            <div class="conflict-view">
                <b>VIEW A:</b>
                {e(item.get("view_a"))}

                {provenance_details(view_a_id)}
            </div>

            <div class="conflict-view">
                <b>VIEW B:</b>
                {e(item.get("view_b"))}

                {provenance_details(view_b_id)}
            </div>

            <div class="small">
                {e(item.get("why_it_matters"))}
            </div>
        </div>
        """

    risks = report.get(
        "key_risks",
        []
    )

    risks_html = ""

    for risk in risks:

        risks_html += f"""
        <div class="risk">
            <div class="risk-title">
                {e(risk.get("risk"))}
            </div>

            <div>
                <b>TRIGGER</b>
                {e(risk.get("trigger"))}
            </div>

            <div>
                <b>IMPACT</b>
                {e(risk.get("market_impact"))}
            </div>
        </div>
        """

    takeaway_items = report.get(
        "research_takeaways",
        []
    )

    takeaways = ""

    for i, takeaway in enumerate(
        takeaway_items,
        1,
    ):

        target_id = (
            f"TAKEAWAY-{i:02d}"
        )

        takeaways += f"""
        <li class="takeaway-item">
            <div>
                {e(takeaway)}
            </div>

            {provenance_details(target_id)}
        </li>
        """

    actions = report.get(
        "daily_action",
        []
    )

    actions_html = ""

    for i, action in enumerate(
        actions,
        1,
    ):

        actions_html += f"""
        <div class="action">
            <div class="action-number">
                {i}
            </div>

            <div>
                <strong>
                    {e(action.get("action"))}
                </strong>

                <p>
                    {e(action.get("why"))}
                </p>

                <div class="monitor">
                    MONITOR →
                    {e(action.get("what_to_monitor"))}
                </div>
            </div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="{e(LANG)}">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width,
               initial-scale=1.0">

<title>
Bloomberg Surveillance —
{e(DATE)}
</title>


<style>

* {{
    box-sizing: border-box;
}}

:root {{
    --bg: #111214;
    --panel: #191a1d;
    --panel-2: #151619;
    --panel-3: #202125;
    --line: #303136;
    --text: #f1f1ee;
    --muted: #96979b;
    --amber: #f2a23a;
    --amber-soft: #c9852c;
    --green: #72c7a7;
    --red: #e46f6f;
    --blue: #7fa9d8;
}}

body {{
    margin: 0;
    background:
        radial-gradient(
            circle at 50% -10%,
            #292b2f 0%,
            #151619 35%,
            #0d0e10 100%
        );
    color: var(--text);
    font-family:
        Inter,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
    font-size: 14px;
}}

.page {{
    max-width: 1420px;
    margin: 0 auto;
    padding: 28px 24px 60px;
}}

.tv {{
    background: #17181b;
    border: 1px solid #303136;
    border-radius: 12px;
    padding: 0;
    box-shadow:
        0 22px 60px rgba(0,0,0,.45),
        inset 0 1px 0 rgba(255,255,255,.04);
    overflow: hidden;
}}

.tv-top {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    min-height: 48px;
    padding: 0 18px;
    background: linear-gradient(180deg,#222327,#18191c);
    border-bottom: 1px solid #333438;
}}

.brand {{
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 1.8px;
    color: #f4f4f1;
}}

.live {{
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.4px;
    color: var(--amber);
}}

.top-actions {{
    display: flex;
    align-items: center;
    gap: 8px;
}}

.language-switch {{
    display: flex;
    align-items: center;
    padding: 3px;
    background: #111214;
    border: 1px solid #34353a;
    border-radius: 6px;
}}

.lang-option {{
    padding: 5px 8px;
    border-radius: 4px;
    font-family:
        ui-monospace,
        SFMono-Regular,
        Menlo,
        monospace;
    font-size: 9px;
    font-weight: 800;
    letter-spacing: .6px;
}}

.lang-active {{
    background: var(--amber);
    color: #111214;
}}

.lang-disabled {{
    color: #626368;
    cursor: not-allowed;
}}

.calendar-control {{
    position: relative;
}}

.calendar-button {{
    display: inline-flex;
    align-items: center;
    gap: 7px;
    min-height: 29px;
    padding: 5px 9px;
    background: #17181b;
    border: 1px solid #3a3b40;
    border-radius: 6px;
    color: #dededb;
    font-family:
        ui-monospace,
        SFMono-Regular,
        Menlo,
        monospace;
    font-size: 9px;
    font-weight: 800;
    letter-spacing: .5px;
    cursor: pointer;
}}

.calendar-button:hover {{
    border-color: var(--amber-soft);
    color: var(--amber);
}}

.calendar-icon {{
    font-size: 13px;
}}

.calendar-panel {{
    display: none;
    position: absolute;
    top: calc(100% + 9px);
    right: 0;
    z-index: 100;
    width: 270px;
    padding: 14px;
    background: #151619;
    border: 1px solid #3a3b40;
    border-radius: 8px;
    box-shadow:
        0 18px 45px rgba(0,0,0,.55);
}}

.calendar-control.open
.calendar-panel {{
    display: block;
}}

.nav-month + .nav-month {{
    margin-top: 14px;
    padding-top: 13px;
    border-top: 1px solid #303136;
}}

.nav-month-label {{
    margin-bottom: 10px;
    color: var(--amber);
    font-family:
        ui-monospace,
        SFMono-Regular,
        Menlo,
        monospace;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1.3px;
}}

.nav-date-grid {{
    display: grid;
    grid-template-columns:
        repeat(7,1fr);
    gap: 5px;
}}

.nav-date {{
    display: flex;
    align-items: center;
    justify-content: center;
    aspect-ratio: 1;
    border: 1px solid #303136;
    border-radius: 5px;
    background: #1d1e22;
    color: #bdbec1;
    font-family:
        ui-monospace,
        SFMono-Regular,
        Menlo,
        monospace;
    font-size: 9px;
    font-weight: 700;
    text-decoration: none;
}}

.nav-date:hover {{
    border-color: var(--amber-soft);
    color: var(--amber);
    background: #24211c;
}}

.nav-date-current {{
    background: var(--amber);
    border-color: var(--amber);
    color: #111214;
}}

.nav-date-current:hover {{
    color: #111214;
}}

.screen {{
    position: relative;
    background: linear-gradient(135deg,#17191b,#101113);
    min-height: 220px;
    padding: 30px 34px;
    border-bottom: 1px solid #303136;
}}

.screen-label {{
    color: var(--amber);
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 2.6px;
    margin-bottom: 12px;
}}

.screen h1 {{
    margin: 0;
    font-size: 38px;
    line-height: 1.05;
    letter-spacing: -1.5px;
}}

.date {{
    margin-top: 10px;
    color: var(--muted);
    font-family: ui-monospace,SFMono-Regular,Menlo,monospace;
    font-size: 12px;
}}

.controls {{
    display: flex;
    align-items: center;
    gap: 7px;
    margin-top: 28px;
}}

.knob {{
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #67686b;
}}

.status {{
    margin-left: 12px;
    color: var(--green);
    font-family: ui-monospace,SFMono-Regular,Menlo,monospace;
    font-size: 10px;
    letter-spacing: 1px;
}}

.content {{
    margin-top: 18px;
}}

.card {{
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 14px;
    box-shadow: 0 8px 24px rgba(0,0,0,.16);
}}

.section-title {{
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1.8px;
    color: #e8e8e5;
    margin-bottom: 16px;
}}

.section-title::before {{
    content: "";
    width: 3px;
    height: 14px;
    background: var(--amber);
    border-radius: 2px;
}}

.executive {{
    font-size: 15px;
    line-height: 1.65;
}}

.executive ul {{
    margin: 0;
    padding-left: 20px;
}}

.executive li {{
    margin-bottom: 9px;
}}

.grid {{
    display: grid;
    grid-template-columns: repeat(3,minmax(0,1fr));
    gap: 12px;
    margin-bottom: 14px;
}}

.market-card {{
    position: relative;
    background: var(--panel-2);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 17px;
    min-height: 190px;
}}

.market-card::before {{
    content: "";
    position: absolute;
    left: 0;
    top: 12px;
    bottom: 12px;
    width: 2px;
    background: var(--amber-soft);
    opacity: .75;
}}

.market-card .section-title {{
    padding-left: 8px;
}}

.summary {{
    color: #c8c9cb;
    line-height: 1.55;
    margin: 0 0 14px;
}}

h4 {{
    margin: 16px 0 7px;
    font-size: 9px;
    font-weight: 800;
    letter-spacing: 1.7px;
    color: var(--amber);
}}

.market-card ul {{
    margin: 0;
    padding-left: 18px;
}}

.market-card li {{
    margin-bottom: 7px;
    color: #d9d9d7;
    line-height: 1.45;
}}

.macro-card {{
    background: var(--panel-2);
    border: 1px solid #292a2e;
    border-radius: 8px;
    padding: 17px;
    margin-top: 10px;
}}

.macro-card h3 {{
    margin: 0 0 8px;
    font-size: 16px;
    color: #f0f0ed;
}}

.macro-card p {{
    color: #c6c7c9;
    line-height: 1.55;
}}

.guest-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    margin: 12px 0;
}}

.guest {{
    display: inline-block;
    padding: 4px 8px;
    border: 1px solid #3a3b3f;
    border-radius: 4px;
    background: #222327;
    color: #c5c6c8;
    font-family: ui-monospace,SFMono-Regular,Menlo,monospace;
    font-size: 10px;
}}

.evidence {{
    display: flex;
    gap: 10px;
    padding: 9px 10px;
    margin-top: 6px;
    background: #111214;
    border: 1px solid #292a2d;
    border-left: 2px solid var(--green);
    font-size: 11px;
    line-height: 1.5;
}}

.timestamp {{
    flex: 0 0 auto;
    color: var(--green);
    font-family: ui-monospace,SFMono-Regular,Menlo,monospace;
    font-size: 10px;
}}

.insight,
.conflict,
.risk {{
    border-radius: 7px;
    padding: 14px 16px;
    margin-bottom: 8px;
    line-height: 1.55;
}}

.insight {{
    background: #151c19;
    border: 1px solid #293a34;
    border-left: 3px solid var(--green);
}}

.conflict {{
    background: #1b1815;
    border: 1px solid #3c3025;
    border-left: 3px solid var(--amber);
}}

.risk {{
    background: #1c1617;
    border: 1px solid #40292b;
    border-left: 3px solid var(--red);
}}

.small {{
    margin-top: 6px;
    color: var(--muted);
    font-size: 11px;
}}

.provenance-block {{
    margin-top: 11px;
    padding-top: 9px;
    border-top: 1px solid #2c2d31;
}}

.prov-badges {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 7px;
}}

.prov-badge {{
    display: inline-flex;
    align-items: center;
    min-height: 20px;
    padding: 3px 7px;
    border-radius: 4px;
    font-family:
        ui-monospace,
        SFMono-Regular,
        Menlo,
        monospace;
    font-size: 9px;
    font-weight: 800;
    letter-spacing: .5px;
}}

.prov-approved {{
    color: var(--green);
    background: #14231e;
    border: 1px solid #2e5547;
}}

.prov-review {{
    color: var(--amber);
    background: #261e14;
    border: 1px solid #634826;
}}

.prov-type {{
    color: #b9c9dc;
    background: #171d24;
    border: 1px solid #344252;
}}

.prov-warning {{
    margin: 7px 0;
    padding: 7px 9px;
    border-left: 2px solid var(--amber);
    background: #211b14;
    color: var(--amber);
    font-family:
        ui-monospace,
        SFMono-Regular,
        Menlo,
        monospace;
    font-size: 9px;
    font-weight: 800;
    letter-spacing: .6px;
}}

.provenance-details {{
    margin-top: 6px;
}}

.provenance-details summary {{
    cursor: pointer;
    color: #9fa8b4;
    font-family:
        ui-monospace,
        SFMono-Regular,
        Menlo,
        monospace;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: .5px;
    user-select: none;
}}

.provenance-details summary:hover {{
    color: var(--text);
}}

.claim-list {{
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    margin-top: 9px;
}}

.claim-id {{
    display: inline-block;
    padding: 4px 7px;
    border: 1px solid #353b43;
    border-radius: 4px;
    background: #121519;
    color: #aeb8c4;
    font-family:
        ui-monospace,
        SFMono-Regular,
        Menlo,
        monospace;
    font-size: 9px;
}}

.prov-note {{
    margin-top: 8px;
    color: #73777e;
    font-size: 9px;
    line-height: 1.4;
}}

.conflict-view {{
    margin-top: 10px;
}}

.takeaway-item {{
    margin-bottom: 12px;
}}

.action {{
    display: flex;
    gap: 14px;
    padding: 15px;
    background: #171a18;
    border: 1px solid #304238;
    border-radius: 8px;
    margin-bottom: 9px;
}}

.action-number {{
    flex: 0 0 auto;
    width: 28px;
    height: 28px;
    display: grid;
    place-items: center;
    border-radius: 5px;
    background: var(--amber);
    color: #17120b;
    font-size: 12px;
    font-weight: 900;
}}

.action p {{
    margin: 7px 0;
    color: #b9babd;
    line-height: 1.5;
}}

.monitor {{
    color: var(--green);
    font-family: ui-monospace,SFMono-Regular,Menlo,monospace;
    font-size: 10px;
    letter-spacing: .4px;
}}

.footer {{
    text-align: center;
    color: #66686d;
    font-size: 10px;
    padding: 26px;
}}

@media (max-width: 1000px) {{
    .grid {{
        grid-template-columns: repeat(2,minmax(0,1fr));
    }}
}}

@media (max-width: 680px) {{
    .page {{
        padding: 12px;
    }}

    .tv-top {{
        align-items: flex-start;
        gap: 12px;
        padding-top: 12px;
        padding-bottom: 12px;
    }}

    .top-actions {{
        flex-wrap: wrap;
        justify-content: flex-end;
    }}

    .calendar-panel {{
        position: fixed;
        top: 70px;
        left: 12px;
        right: 12px;
        width: auto;
    }}

    .screen {{
        padding: 24px;
    }}

    .screen h1 {{
        font-size: 30px;
    }}

    .grid {{
        grid-template-columns: 1fr;
    }}
}}

</style>


</head>

<body>

<div class="page">


<div class="tv">

    <div class="tv-top">

        <div class="brand">
            BLOOMBERG SURVEILLANCE · RESEARCH DESK
        </div>

        <div class="top-actions">

            <div class="live">
                ● DAILY RESEARCH
            </div>

            <div
                class="calendar-control"
                id="calendarControl"
            >

                <button
                    class="calendar-button"
                    id="calendarButton"
                    type="button"
                    aria-expanded="false"
                    aria-controls="calendarPanel"
                >
                    <span class="calendar-icon">
                        ▦
                    </span>

                    <span>
                        {e(DATE)}
                    </span>
                </button>

                <div
                    class="calendar-panel"
                    id="calendarPanel"
                >
                    {navigation_html()}
                </div>

            </div>

            <div
                class="language-switch"
                aria-label="Report language"
            >
                {language_switch_html()}
            </div>

        </div>

    </div>

    <div class="screen">

        <div class="screen-label">
            GLOBAL MARKET RESEARCH
        </div>

        <h1>
            Daily Market Brief
        </h1>

        <div class="date">
            {e(DATE)}
        </div>

        <div class="controls">

            <span class="knob"></span>
            <span class="knob"></span>
            <span class="knob"></span>

            <span class="status">
                EVIDENCE GROUNDED · RESEARCH ONLY
            </span>

        </div>

    </div>

</div>

<div class="content">

<section class="card">

    <div class="section-title">
        EXECUTIVE SUMMARY
    </div>

    <div class="executive">
        <ul>
            {executive}
        </ul>
    </div>

</section>


<section class="card">

    <div class="section-title">
        MACRO THEMES
    </div>

    {macro_html}

</section>


<div class="grid">

{market_section("RATES / BONDS", "rates_bonds")}

{market_section("USD / FX", "usd_fx")}

{market_section("EQUITIES", "equities")}

{market_section("CREDIT", "credit")}

{market_section("AI / TECHNOLOGY", "ai_technology")}

{market_section("COMMODITIES", "commodities")}

</div>


<section class="card">

    <div class="section-title">
        CROSS-GUEST CONSENSUS
    </div>

    {consensus_html}

</section>


<section class="card">

    <div class="section-title">
        CROSS-GUEST CONFLICTS
    </div>

    {conflicts_html}

</section>


<section class="card">

    <div class="section-title">
        KEY RISKS
    </div>

    {risks_html}

</section>


<section class="card">

    <div class="section-title">
        RESEARCH TAKEAWAYS
    </div>

    <ul>
        {takeaways}
    </ul>

</section>


<section class="card">

    <div class="section-title">
        DAILY ACTION
    </div>

    <div class="small">
        Analytical interpretation —
        not a Bloomberg guest quote.
    </div>

    <br>

    {actions_html}

</section>

</div>


<div class="footer">
    Bloomberg Surveillance Research Engine · {e(DATE)}
</div>

</div>

<script>
(function () {{
    const control =
        document.getElementById(
            "calendarControl"
        );

    const button =
        document.getElementById(
            "calendarButton"
        );

    if (!control || !button) {{
        return;
    }}

    button.addEventListener(
        "click",
        function (event) {{
            event.stopPropagation();

            const open =
                control.classList.toggle(
                    "open"
                );

            button.setAttribute(
                "aria-expanded",
                open ? "true" : "false"
            );
        }}
    );

    document.addEventListener(
        "click",
        function (event) {{
            if (
                !control.contains(
                    event.target
                )
            ) {{
                control.classList.remove(
                    "open"
                );

                button.setAttribute(
                    "aria-expanded",
                    "false"
                );
            }}
        }}
    );

    document.addEventListener(
        "keydown",
        function (event) {{
            if (event.key === "Escape") {{
                control.classList.remove(
                    "open"
                );

                button.setAttribute(
                    "aria-expanded",
                    "false"
                );
            }}
        }}
    );
}})();
</script>

</body>

</html>
"""


html = build_html()

# Serialization hygiene:
# remove trailing whitespace generated when optional
# HTML fragments expand to empty/indented lines.
html = "\n".join(
    line.rstrip()
    for line in html.splitlines()
) + "\n"

OUTPUT.write_text(
    html,
    encoding="utf-8",
)


print("=" * 100)
print("DAILY RESEARCH TV REPORT")
print("=" * 100)
print("DATE:", DATE)
print("LANG:", LANG)
print("OUTPUT:", OUTPUT)
print("=" * 100)
print("HTML BUILD: PASS")
print("=" * 100)
