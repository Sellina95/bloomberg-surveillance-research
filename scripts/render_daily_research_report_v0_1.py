from __future__ import annotations

import json
import os
from pathlib import Path


DATE = os.environ.get(
    "SURVEILLANCE_DATE",
    "2026-08-14",
)

BASE = Path(
    f"data/processed/surveillance/{DATE}"
)

INPUT = BASE / "daily_research_report_v0_1.json"
OUTPUT = BASE / "daily_research_report_v0_1.md"


if not INPUT.exists():
    raise SystemExit(
        f"FAIL — input not found: {INPUT}"
    )


report = json.loads(
    INPUT.read_text(
        encoding="utf-8"
    )
)


def text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def bullets(items) -> str:
    if not items:
        return "- None"

    return "\n".join(
        f"- {text(item)}"
        for item in items
    )


def render_market_section(
    title: str,
    section: dict,
) -> str:

    if not isinstance(section, dict):
        return f"## {title}\n\n- No data\n"

    summary = text(
        section.get("summary")
    )

    key_views = section.get(
        "key_views",
        []
    )

    risks = section.get(
        "risks",
        []
    )

    return f"""## {title}

### Summary

{summary or "No summary available."}

### Key Views

{bullets(key_views)}

### Risks

{bullets(risks)}

"""


def render():

    lines = []

    lines.append(
        f"# Bloomberg Surveillance — Daily Research"
    )
    lines.append("")
    lines.append(
        f"**Date:** {DATE}"
    )
    lines.append("")

    # ------------------------------------------------------------
    # Executive Summary
    # ------------------------------------------------------------

    lines.append("## Executive Summary")
    lines.append("")
    lines.append(
        bullets(
            report.get(
                "executive_summary",
                []
            )
        )
    )
    lines.append("")

    # ------------------------------------------------------------
    # Macro Themes
    # ------------------------------------------------------------

    lines.append("## Macro Themes")
    lines.append("")

    themes = report.get(
        "macro_themes",
        []
    )

    if themes:

        for theme in themes:

            if not isinstance(theme, dict):
                continue

            lines.append(
                f"### {text(theme.get('theme'))}"
            )
            lines.append("")
            lines.append(
                text(
                    theme.get(
                        "summary"
                    )
                )
            )
            lines.append("")

            guests = theme.get(
                "supporting_guests",
                []
            )

            if guests:
                lines.append(
                    "**Supporting Guests**"
                )
                lines.append("")
                lines.append(
                    bullets(guests)
                )
                lines.append("")

            evidence = theme.get(
                "evidence",
                []
            )

            if evidence:
                lines.append(
                    "**Evidence**"
                )
                lines.append("")
                for ev in evidence:
                    if isinstance(ev, dict):
                        ts = ev.get("timestamp_seconds")
                        segment_id = ev.get("segment_id")
                        ev_text = text(ev.get("text"))

                        if ts is not None:
                            minutes = int(ts // 60)
                            seconds = int(ts % 60)
                            stamp = f"{minutes:02d}:{seconds:02d}"
                        else:
                            stamp = "N/A"

                        lines.append(
                            f'- **[{stamp}] Segment {segment_id}** — "{ev_text}"'
                        )
                    else:
                        lines.append(
                            f"- {text(ev)}"
                        )
                lines.append("")

    else:
        lines.append("- No macro themes.")
        lines.append("")

    # ------------------------------------------------------------
    # Markets
    # ------------------------------------------------------------

    lines.append(
        render_market_section(
            "Rates / Bonds",
            report.get(
                "rates_bonds",
                {}
            ),
        )
    )

    lines.append(
        render_market_section(
            "USD / FX",
            report.get(
                "usd_fx",
                {}
            ),
        )
    )

    lines.append(
        render_market_section(
            "Equities",
            report.get(
                "equities",
                {}
            ),
        )
    )

    lines.append(
        render_market_section(
            "Credit",
            report.get(
                "credit",
                {}
            ),
        )
    )

    lines.append(
        render_market_section(
            "AI / Technology",
            report.get(
                "ai_technology",
                {}
            ),
        )
    )

    lines.append(
        render_market_section(
            "Commodities",
            report.get(
                "commodities",
                {}
            ),
        )
    )

    # ------------------------------------------------------------
    # Consensus
    # ------------------------------------------------------------

    lines.append(
        "## Cross-Guest Consensus"
    )
    lines.append("")

    consensus = report.get(
        "cross_guest_consensus",
        []
    )

    if consensus:

        for item in consensus:

            if not isinstance(item, dict):
                continue

            lines.append(
                f"### {text(item.get('view'))}"
            )
            lines.append("")

            guests = item.get(
                "guests",
                []
            )

            if guests:
                lines.append(
                    "**Guests:** "
                    + ", ".join(
                        text(g)
                        for g in guests
                    )
                )
                lines.append("")

    else:
        lines.append(
            "- No clear consensus identified."
        )
        lines.append("")

    # ------------------------------------------------------------
    # Conflicts
    # ------------------------------------------------------------

    lines.append(
        "## Cross-Guest Conflicts"
    )
    lines.append("")

    conflicts = report.get(
        "cross_guest_conflicts",
        []
    )

    if conflicts:

        for item in conflicts:

            if not isinstance(item, dict):
                continue

            lines.append(
                f"### {text(item.get('topic'))}"
            )
            lines.append("")

            lines.append(
                f"**View A:** "
                f"{text(item.get('view_a'))}"
            )
            lines.append("")

            lines.append(
                f"**View B:** "
                f"{text(item.get('view_b'))}"
            )
            lines.append("")

            lines.append(
                f"**Why It Matters:** "
                f"{text(item.get('why_it_matters'))}"
            )
            lines.append("")

    else:
        lines.append(
            "- No material conflicts identified."
        )
        lines.append("")

    # ------------------------------------------------------------
    # Risks
    # ------------------------------------------------------------

    lines.append("## Key Risks")
    lines.append("")

    risks = report.get(
        "key_risks",
        []
    )

    if risks:

        for risk in risks:

            if not isinstance(risk, dict):
                continue

            lines.append(
                f"### {text(risk.get('risk'))}"
            )
            lines.append("")

            lines.append(
                f"- **Trigger:** "
                f"{text(risk.get('trigger'))}"
            )

            lines.append(
                f"- **Market Impact:** "
                f"{text(risk.get('market_impact'))}"
            )

            lines.append("")

    else:
        lines.append("- No key risks.")
        lines.append("")

    # ------------------------------------------------------------
    # Research Takeaways
    # ------------------------------------------------------------

    lines.append(
        "## Research Takeaways"
    )
    lines.append("")

    lines.append(
        bullets(
            report.get(
                "research_takeaways",
                []
            )
        )
    )
    lines.append("")

    # ------------------------------------------------------------
    # Daily Action
    # ------------------------------------------------------------

    lines.append(
        "## Daily Action"
    )
    lines.append("")

    lines.append(
        "> **Analytical interpretation — not a Bloomberg guest quote.**"
    )
    lines.append("")

    actions = report.get(
        "daily_action",
        []
    )

    if actions:

        for index, action in enumerate(
            actions,
            start=1,
        ):

            if not isinstance(action, dict):
                continue

            lines.append(
                f"### {index}. "
                f"{text(action.get('action'))}"
            )
            lines.append("")

            lines.append(
                f"**Why:** "
                f"{text(action.get('why'))}"
            )
            lines.append("")

            lines.append(
                f"**What to Monitor:** "
                f"{text(action.get('what_to_monitor'))}"
            )
            lines.append("")

    else:
        lines.append(
            "- No daily actions generated."
        )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


OUTPUT.write_text(
    render(),
    encoding="utf-8",
)


print("=" * 100)
print("DAILY RESEARCH REPORT RENDER")
print("=" * 100)
print("DATE:", DATE)
print("INPUT:", INPUT)
print("OUTPUT:", OUTPUT)
print("=" * 100)
print("RENDER: PASS")
print("=" * 100)
