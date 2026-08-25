from __future__ import annotations

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

INPUT = BASE / "daily_research_report_v0_1.json"
OUTPUT = BASE / "daily_research_report_tv_v0_1.html"


if not INPUT.exists():
    raise SystemExit(
        f"FAIL — input not found: {INPUT}"
    )


report = json.loads(
    INPUT.read_text(
        encoding="utf-8"
    )
)


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

    for item in consensus:

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
        </div>
        """

    conflicts = report.get(
        "cross_guest_conflicts",
        []
    )

    conflicts_html = ""

    for item in conflicts:

        conflicts_html += f"""
        <div class="conflict">
            <strong>
                {e(item.get("topic"))}
            </strong>

            <div>
                <b>VIEW A:</b>
                {e(item.get("view_a"))}
            </div>

            <div>
                <b>VIEW B:</b>
                {e(item.get("view_b"))}
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

    takeaways = list_items(
        report.get(
            "research_takeaways",
            []
        )
    )

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
<html lang="en">

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

body {{
    margin: 0;
    background:
        radial-gradient(
            circle at top,
            #20252b,
            #0c0e10 65%
        );
    color: #e9edf0;
    font-family:
        Inter,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
}}

.page {{
    max-width: 1200px;
    margin: 40px auto;
    padding: 20px;
}}

/* TV */

.tv {{
    background: #17191c;
    border-radius: 34px;
    padding: 24px 24px 34px;
    box-shadow:
        0 30px 80px rgba(0,0,0,.55),
        inset 0 1px 0 rgba(255,255,255,.06);
}}

.tv-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 4px 12px 18px;
}}

.brand {{
    font-weight: 800;
    letter-spacing: 2px;
    font-size: 15px;
}}

.live {{
    font-size: 11px;
    letter-spacing: 1.5px;
    color: #ff6b6b;
}}

.screen {{
    background:
        linear-gradient(
            135deg,
            #111b1d,
            #071011
        );
    border-radius: 18px;
    padding: 34px;
    min-height: 260px;
    border: 1px solid #30383b;
    box-shadow:
        inset 0 0 60px rgba(0,0,0,.55);
}}

.screen-label {{
    color: #7ee2c5;
    font-size: 11px;
    letter-spacing: 3px;
    margin-bottom: 12px;
}}

.screen h1 {{
    font-size: 42px;
    margin: 0 0 8px;
    letter-spacing: -1px;
}}

.date {{
    color: #89949a;
    font-size: 14px;
}}

.controls {{
    display: flex;
    gap: 8px;
    margin-top: 20px;
}}

.knob {{
    width: 11px;
    height: 11px;
    border-radius: 50%;
    background: #737b80;
}}

.status {{
    margin-left: auto;
    color: #7ee2c5;
    font-size: 11px;
    letter-spacing: 1px;
}}

/* Content */

.content {{
    margin-top: 24px;
}}

.card {{
    background: #181b1f;
    border: 1px solid #2a2f34;
    border-radius: 18px;
    padding: 26px;
    margin-bottom: 18px;
}}

.section-title {{
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 2px;
    margin-bottom: 18px;
}}

.executive {{
    font-size: 18px;
    line-height: 1.65;
}}

ul {{
    padding-left: 22px;
}}

li {{
    margin-bottom: 10px;
    line-height: 1.55;
}}

.macro-card,
.market-card {{
    background: #14171a;
    border: 1px solid #282d31;
    border-radius: 14px;
    padding: 20px;
    margin-top: 14px;
}}

.macro-card h3 {{
    margin-top: 0;
}}

.summary {{
    color: #c6cdd1;
    line-height: 1.65;
}}

h4 {{
    font-size: 10px;
    letter-spacing: 2px;
    color: #7ee2c5;
    margin-top: 22px;
}}

.guest-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 7px;
    margin: 16px 0;
}}

.guest {{
    padding: 5px 9px;
    border-radius: 20px;
    background: #242a2e;
    color: #aeb8bd;
    font-size: 11px;
}}

.evidence {{
    border-left: 2px solid #5e7771;
    padding: 9px 12px;
    margin-top: 8px;
    background: #111416;
    font-size: 12px;
    line-height: 1.5;
}}

.timestamp {{
    color: #7ee2c5;
    font-family: monospace;
    margin-right: 10px;
}}

.grid {{
    display: grid;
    grid-template-columns:
        repeat(
            auto-fit,
            minmax(320px, 1fr)
        );
    gap: 18px;
}}

.insight {{
    padding: 16px;
    border-left: 3px solid #7ee2c5;
    background: #121518;
    margin-bottom: 10px;
    line-height: 1.55;
}}

.conflict {{
    padding: 18px;
    background: #171416;
    border-left: 3px solid #d99a68;
    margin-bottom: 12px;
    line-height: 1.6;
}}

.risk {{
    padding: 18px;
    background: #191618;
    border-left: 3px solid #cf7070;
    margin-bottom: 12px;
    line-height: 1.6;
}}

.risk-title {{
    font-weight: 700;
    margin-bottom: 10px;
}}

.small {{
    color: #8e999f;
    font-size: 12px;
    margin-top: 8px;
}}

.action {{
    display: flex;
    gap: 16px;
    padding: 18px;
    background: #101719;
    border: 1px solid #29443e;
    border-radius: 14px;
    margin-bottom: 12px;
}}

.action-number {{
    min-width: 34px;
    height: 34px;
    border-radius: 50%;
    background: #7ee2c5;
    color: #10201c;
    display: grid;
    place-items: center;
    font-weight: 800;
}}

.action p {{
    color: #aeb8bd;
    line-height: 1.5;
}}

.monitor {{
    color: #7ee2c5;
    font-size: 12px;
    letter-spacing: .4px;
}}

.footer {{
    text-align: center;
    color: #697278;
    font-size: 11px;
    padding: 30px;
}}

</style>

</head>

<body>

<div class="page">

<div class="tv">

    <div class="tv-top">
        <div class="brand">
            BLOOMBERG SURVEILLANCE
        </div>

        <div class="live">
            ● RESEARCH
        </div>
    </div>

    <div class="screen">

        <div class="screen-label">
            DAILY MARKET BRIEF
        </div>

        <h1>
            Global Market Research
        </h1>

        <div class="date">
            {e(DATE)}
        </div>

        <div class="controls">
            <span class="knob"></span>
            <span class="knob"></span>
            <span class="knob"></span>

            <span class="status">
                13 GUESTS · EVIDENCE GROUNDED
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

</body>

</html>
"""


OUTPUT.write_text(
    build_html(),
    encoding="utf-8",
)


print("=" * 100)
print("DAILY RESEARCH TV REPORT")
print("=" * 100)
print("DATE:", DATE)
print("OUTPUT:", OUTPUT)
print("=" * 100)
print("HTML BUILD: PASS")
print("=" * 100)
