from __future__ import annotations
import os

import html
import json
from pathlib import Path


DATE = os.environ.get("SURVEILLANCE_DATE", "2026-08-14")

BASE = Path(
    f"data/processed/surveillance/{DATE}"
)

INPUT = BASE / "research_dataset_v0_1.json"
OUTPUT = BASE / "research_dashboard.html"


data = json.loads(
    INPUT.read_text(
        encoding="utf-8"
    )
)


def esc(value) -> str:
    return html.escape(
        str(value or "")
    )


cards = []


for unit in data["research_units"]:

    summary = unit["research_summary"]

    views_html = []

    for i, view in enumerate(
        summary["key_views"],
        start=1,
    ):

        evidence_html = []

        for evidence in view["evidence"]:

            timestamp = float(
                evidence[
                    "timestamp_seconds"
                ]
            )

            minutes = int(
                timestamp // 60
            )

            seconds = int(
                timestamp % 60
            )

            evidence_html.append(
                f"""
                <div class="evidence">
                    <div class="timestamp">
                        {minutes:02d}:{seconds:02d}
                    </div>
                    <div class="quote">
                        {esc(evidence["text"])}
                    </div>
                </div>
                """
            )

        views_html.append(
            f"""
            <div class="view">
                <div class="view-title">
                    {i}. {esc(view["claim"])}
                </div>

                <details>
                    <summary>
                        Evidence
                    </summary>

                    {''.join(evidence_html)}
                </details>
            </div>
            """
        )

    tags = " ".join(
        f"<span class='tag'>{esc(tag)}</span>"
        for tag in summary[
            "research_tags"
        ]
    )

    start = int(
        unit["timestamp"]["start_seconds"]
    )

    end = int(
        unit["timestamp"]["end_seconds"]
    )

    start_text = (
        f"{start // 60:02d}:{start % 60:02d}"
    )

    end_text = (
        f"{end // 60:02d}:{end % 60:02d}"
    )

    cards.append(
        f"""
        <article class="card">

            <header>
                <div class="guest">
                    {esc(unit["guest"])}
                </div>

                <div class="chapter">
                    {esc(unit.get("organization"))}
                </div>

                <div class="time">
                    {start_text} – {end_text}
                </div>
            </header>

            <section>
                <h3>Topic</h3>
                <p>{esc(summary["topic"])}</p>
            </section>

            <section>
                <h3>Key Views</h3>
                {''.join(views_html)}
            </section>

            <section>
                <h3>Why It Matters</h3>
                <p>
                    {esc(summary["why_it_matters"])}
                </p>
            </section>

            <section>
                <h3>Market Implication</h3>
                <p>
                    {esc(
                        summary[
                            "market_implication"
                        ]
                    )}
                </p>
            </section>

            <section>
                <h3>Research Tags</h3>
                <div class="tags">
                    {tags}
                </div>
            </section>

        </article>
        """
    )


document = f"""
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="utf-8">

<meta name="robots" content="noindex, nofollow">

<meta name="viewport"
      content="width=device-width, initial-scale=1">

<title>
Independent Market Research — {DATE}
</title>

<style>

body {{
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;

    max-width: 1100px;
    margin: 40px auto;
    padding: 0 20px;
    background: #f5f6f8;
    color: #1f2937;
}}

h1 {{
    margin-bottom: 6px;
}}

.subtitle {{
    color: #6b7280;
    margin-bottom: 30px;
}}

.card {{
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 24px;
}}

.guest {{
    font-size: 22px;
    font-weight: 700;
}}

.chapter {{
    margin-top: 5px;
    color: #4b5563;
}}

.time {{
    margin-top: 5px;
    color: #9ca3af;
    font-size: 13px;
}}

section {{
    margin-top: 22px;
}}

h3 {{
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: .05em;
    color: #6b7280;
}}

.view {{
    border-top: 1px solid #eee;
    padding: 14px 0;
}}

.view-title {{
    font-weight: 600;
}}

details {{
    margin-top: 10px;
}}

summary {{
    cursor: pointer;
    color: #2563eb;
    font-size: 14px;
}}

.evidence {{
    margin-top: 10px;
    padding: 12px;
    background: #f8fafc;
    border-left: 3px solid #cbd5e1;
}}

.timestamp {{
    font-family: monospace;
    font-size: 12px;
    color: #64748b;
    margin-bottom: 5px;
}}

.quote {{
    line-height: 1.5;
}}

.tags {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}}

.tag {{
    background: #eef2ff;
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 12px;
}}

</style>

</head>

<body>

<h1>
Bloomberg Surveillance Research
</h1>

<div class="subtitle">
{DATE} · {data["guest_count"]} Guest Units
</div>

{''.join(cards)}

</body>

</html>
"""


OUTPUT.write_text(
    document,
    encoding="utf-8"
)


print("=" * 100)
print("RESEARCH DASHBOARD BUILD")
print("=" * 100)
print("DATE:", DATE)
print(
    "GUESTS:",
    data["guest_count"]
)
print("OUTPUT:", OUTPUT)
print("=" * 100)
print("BUILD: PASS")
print("=" * 100)
