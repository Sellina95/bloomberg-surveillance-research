from __future__ import annotations

import json
import os
import time
from pathlib import Path

from google import genai
from google.genai import errors as genai_errors

from public_language_policy_v0_1 import neutralize_report


DATE = os.environ.get(
    "SURVEILLANCE_DATE",
    "2026-08-14",
)

MODEL = "gemini-3.5-flash-lite"

MAX_GENERATION_ATTEMPTS = 4
RETRY_DELAYS_SECONDS = (15, 30, 60)

BASE = Path(
    f"data/processed/surveillance/{DATE}"
)

INPUT = BASE / "research_dataset_v0_1.json"
OUTPUT = BASE / "daily_research_report_v0_1.json"

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise SystemExit(
        "FAIL — GEMINI_API_KEY is not set"
    )

if not INPUT.exists():
    raise SystemExit(
        f"FAIL — input not found: {INPUT}"
    )


def load_dataset() -> dict:

    return json.loads(
        INPUT.read_text(
            encoding="utf-8"
        )
    )


def build_prompt(dataset: dict) -> str:

    units = dataset.get(
        "research_units",
        []
    )

    return f"""
You are a financial research synthesis engine.

Your task is to synthesize the Bloomberg Surveillance
guest research units into ONE DAILY RESEARCH REPORT.

DATE:
{DATE}

IMPORTANT RULES:

1. Do NOT invent facts.
2. Do NOT attribute views to guests unless the supplied
   research unit supports the attribution.
3. Preserve the distinction between:
   - Guest View
   - Private Evidence
   - Research Interpretation
4. Use supplied evidence internally for grounding, but NEVER
   reproduce transcript text, evidence text, quotations, or
   excerpts in the public report.
5. Public output may contain paraphrased synthesis and
   supporting guest attribution only.
6. Do not manufacture consensus when guests disagree.
7. Explicitly identify disagreement or uncertainty.
8. The daily_action field represents SYSTEM-GENERATED
   MONITORING IMPLICATIONS, not investment recommendations.
   Write observations, conditions, risks, and variables to monitor.
   Do NOT instruct the reader to buy, sell, accumulate, reduce,
   increase, overweight, underweight, enter, exit, go long, go short,
   or otherwise change a portfolio position.
9. Keep the report concise but institutionally useful.
10. If any research unit has attribution_status="unavailable",
    treat it as program-level synthesis: keep supporting_guests,
    cross_guest_consensus, and cross_guest_conflicts empty, and
    do not name or infer speakers.

OUTPUT JSON ONLY.

Required schema:

{{
  "date": "{DATE}",

  "executive_summary": [
    "...",
    "...",
    "..."
  ],

  "macro_themes": [
    {{
      "theme": "...",
      "summary": "...",
      "supporting_guests": []
    }}
  ],

  "rates_bonds": {{
    "summary": "...",
    "key_views": [],
    "risks": []
  }},

  "usd_fx": {{
    "summary": "...",
    "key_views": [],
    "risks": []
  }},

  "equities": {{
    "summary": "...",
    "key_views": [],
    "risks": []
  }},

  "credit": {{
    "summary": "...",
    "key_views": [],
    "risks": []
  }},

  "ai_technology": {{
    "summary": "...",
    "key_views": [],
    "risks": []
  }},

  "commodities": {{
    "summary": "...",
    "key_views": [],
    "risks": []
  }},

  "cross_guest_consensus": [
    {{
      "view": "...",
      "guests": []
    }}
  ],

  "cross_guest_conflicts": [
    {{
      "topic": "...",
      "view_a": "...",
      "view_b": "...",
      "why_it_matters": "..."
    }}
  ],

  "key_risks": [
    {{
      "risk": "...",
      "trigger": "...",
      "market_impact": "..."
    }}
  ],

  "research_takeaways": [
    "..."
  ],

  "daily_action": [
    {{
      "action": "Non-prescriptive monitoring implication only.",
      "why": "...",
      "what_to_monitor": "..."
    }}
  ]
}}

RESEARCH UNITS:

{json.dumps(
    units,
    ensure_ascii=False,
    indent=2
)}
"""



def generate_with_retry(client, prompt: str):

    for attempt in range(1, MAX_GENERATION_ATTEMPTS + 1):

        try:
            return client.models.generate_content(
                model=MODEL,
                contents=prompt,
            )

        except genai_errors.ServerError as exc:

            status_code = getattr(
                exc,
                "status_code",
                None,
            )

            if (
                status_code not in (500, 502, 503, 504)
                or attempt == MAX_GENERATION_ATTEMPTS
            ):
                raise

            delay = RETRY_DELAYS_SECONDS[
                attempt - 1
            ]

            print()
            print(
                "WARNING — transient Gemini server error "
                f"({status_code}). "
                f"Retrying in {delay}s."
            )

            time.sleep(delay)



def repair_invalid_json(client, text: str) -> str:

    prompt = f"""
You are a strict JSON syntax repair engine.

The following text was intended to be valid JSON but contains
one or more JSON syntax errors.

RULES:
1. Repair JSON SYNTAX ONLY.
2. Do NOT add, remove, summarize, rewrite, or reinterpret content.
3. Preserve all facts, numbers, strings, arrays, objects, and attribution.
4. Preserve the intended schema and nesting.
5. Return ONLY valid JSON.
6. Do NOT use markdown fences.

BROKEN JSON:

{text}
"""

    response = generate_with_retry(
        client,
        prompt,
    )

    repaired = response.text.strip()

    if repaired.startswith("```"):
        repaired = repaired.replace(
            "```json",
            "",
            1,
        )
        repaired = repaired.rsplit(
            "```",
            1,
        )[0].strip()

    return repaired


def main():

    print("=" * 100)
    print("DAILY RESEARCH REPORT")
    print("=" * 100)
    print("DATE:", DATE)
    print("MODEL:", MODEL)

    dataset = load_dataset()

    units = dataset.get(
        "research_units",
        []
    )

    print(
        "RESEARCH UNITS:",
        len(units)
    )

    if not units:
        raise SystemExit(
            "FAIL — no research units"
        )

    client = genai.Client(
        api_key=API_KEY
    )

    response = generate_with_retry(
        client,
        build_prompt(dataset),
    )

    text = response.text.strip()

    # Remove accidental markdown fences
    if text.startswith("```"):
        text = text.replace(
            "```json",
            "",
            1,
        )
        text = text.rsplit(
            "```",
            1,
        )[0].strip()

    try:
        report = json.loads(text)

    except json.JSONDecodeError as exc:

        print()
        print(
            "WARNING — model output was not valid JSON."
        )
        print(
            f"INITIAL JSON ERROR: {exc}"
        )
        print(
            "ATTEMPTING JSON SYNTAX REPAIR"
        )

        repaired_text = repair_invalid_json(
            client,
            text,
        )

        try:
            report = json.loads(
                repaired_text
            )

        except json.JSONDecodeError as repair_exc:

            print()
            print(
                "JSON REPAIR FAILED:"
            )
            print(repaired_text)

            raise SystemExit(
                "FAIL — repaired output is still "
                f"invalid JSON: {repair_exc}"
            )

        print(
            "JSON SYNTAX REPAIR: PASS"
        )

    # PUBLICATION BOUNDARY:
    # Evidence is used upstream for grounding but must never
    # be serialized into the public daily report.
    for theme in report.get("macro_themes", []):
        if isinstance(theme, dict):
            theme.pop("evidence", None)

    unattributed_mode = any(
        unit.get("attribution_status") == "unavailable"
        for unit in units
    )

    if unattributed_mode:
        for theme in report.get("macro_themes", []):
            if isinstance(theme, dict):
                theme["supporting_guests"] = []

        report["cross_guest_consensus"] = []
        report["cross_guest_conflicts"] = []
        report["source_mode"] = "program_level_unattributed"

    directive_normalizations = neutralize_report(
        report,
        "en",
    )

    print(
        "EN DIRECTIVE NORMALIZATIONS:",
        directive_normalizations,
    )

    OUTPUT.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 100)
    print("RESULT")
    print("=" * 100)
    print("REPORT: PASS")
    print("OUTPUT:", OUTPUT)
    print("=" * 100)


if __name__ == "__main__":
    main()
