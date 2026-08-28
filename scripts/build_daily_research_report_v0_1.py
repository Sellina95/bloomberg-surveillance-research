from __future__ import annotations

import json
import os
import time
from pathlib import Path

from google import genai
from google.genai import errors as genai_errors


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
   - Evidence
   - Research Interpretation
4. Evidence must remain grounded in the supplied research
   units.
5. Do not manufacture consensus when guests disagree.
6. Explicitly identify disagreement or uncertainty.
7. The Daily Action section is an analytical interpretation,
   NOT a Bloomberg guest quote.
8. Keep the report concise but institutionally useful.

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
      "supporting_guests": [],
      "evidence": []
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
      "action": "...",
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
            "MODEL OUTPUT WAS NOT VALID JSON:"
        )
        print(text)

        raise SystemExit(
            f"FAIL — invalid JSON: {exc}"
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
