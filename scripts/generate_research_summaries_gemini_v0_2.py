from __future__ import annotations
import os

import json
from pathlib import Path

from google import genai


DATE = os.environ.get("SURVEILLANCE_DATE", "2026-08-14")

BASE = Path(
    f"data/processed/surveillance/{DATE}"
)

INPUT = BASE / "guest_transcripts.json"
OUTPUT = BASE / "research_summaries_gemini_v0_2.json"

MODEL = "gemini-3.5-flash-lite"

API_KEY = os.environ["GEMINI_API_KEY"]

client = genai.Client(api_key=API_KEY)


PROMPT = """
You are a financial research editor.

Summarize ONE Bloomberg Surveillance guest interview.

CRITICAL EVIDENCE RULE:

You MUST use ONLY the supplied transcript segments.

For every Key View, you MUST select one or more
EXACT transcript segment IDs that directly support it.

DO NOT write or invent evidence text.

The evidence field must contain ONLY segment IDs
from the supplied transcript.

A Key View without direct supporting transcript
segments must NOT be written.

Separate:

1. What the guest said.
2. Why it matters.
3. Market implication.

The Market Implication may be analytical interpretation,
but it must be clearly an interpretation and must not
be presented as something the guest explicitly said.

Return ONLY valid JSON.

Schema:

{
  "topic": "...",
  "key_views": [
    {
      "claim": "...",
      "evidence_segment_ids": [123, 124]
    }
  ],
  "why_it_matters": "...",
  "market_implication": "...",
  "research_tags": [...]
}

Maximum 3 key views.

Evidence segment IDs must come directly from the transcript.
"""


def build_transcript(unit: dict) -> str:

    lines = []

    for i, segment in enumerate(
        unit["transcript_segments"]
    ):

        lines.append(
            f"""
SEGMENT_ID: {i}
TIMESTAMP: {segment["start_seconds"]:.2f}s
TEXT: {segment["text"]}
""".strip()
        )

    return "\n\n".join(lines)


def generate(unit: dict) -> dict:

    transcript = build_transcript(unit)

    prompt = f"""
{PROMPT}

GUEST:
{unit.get("guest", "")}

CHAPTER:
{unit.get("title", "")}

TRANSCRIPT:

{transcript}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config={
            "temperature": 0.1,
            "response_mime_type":
                "application/json",
        },
    )

    return json.loads(response.text)


def validate_evidence(
    summary: dict,
    unit: dict,
) -> dict:

    segments = unit["transcript_segments"]

    valid_ids = set(
        range(len(segments))
    )

    validated_views = []

    for view in summary.get(
        "key_views",
        [],
    ):

        ids = view.get(
            "evidence_segment_ids",
            [],
        )

        valid = (
            isinstance(ids, list)
            and len(ids) > 0
            and all(
                isinstance(x, int)
                and x in valid_ids
                for x in ids
            )
        )

        evidence = []

        if valid:

            for segment_id in ids:

                segment = segments[
                    segment_id
                ]

                evidence.append(
                    {
                        "segment_id":
                            segment_id,
                        "timestamp_seconds":
                            segment[
                                "start_seconds"
                            ],
                        "text":
                            segment["text"],
                    }
                )

        validated_views.append(
            {
                "claim":
                    view.get("claim", ""),
                "evidence":
                    evidence,
                "grounding_status":
                    (
                        "PASS"
                        if valid
                        else "FAIL"
                    ),
            }
        )

    return {
        **summary,
        "key_views":
            validated_views,
    }


def main():

    data = json.loads(
        INPUT.read_text(
            encoding="utf-8"
        )
    )

    units = data["units"]

    results = []

    print("=" * 100)
    print("GEMINI RESEARCH SUMMARY v0.2")
    print("=" * 100)
    print("DATE:", DATE)
    print("MODEL:", MODEL)
    print("GUESTS:", len(units))
    print("=" * 100)

    for unit in units:

        print(
            f"PROCESSING UNIT "
            f"{unit['unit_id']:02d}..."
        )

        try:

            summary = generate(unit)

            validated = validate_evidence(
                summary,
                unit,
            )

            failed = any(
                view["grounding_status"]
                == "FAIL"
                for view
                in validated["key_views"]
            )

            results.append(
                {
                    "unit_id":
                        unit["unit_id"],
                    "chapter":
                        unit["chapter"],
                    "guest":
                        unit.get("guest"),
                    "title":
                        unit.get("title"),
                    "timestamp":
                        {
                            "start_seconds":
                                unit["start_seconds"],
                            "end_seconds":
                                unit["end_seconds"],
                        },
                    "summary":
                        validated,
                    "status":
                        "REVIEW"
                        if failed
                        else "COMPLETE",
                }
            )

            print(
                "REVIEW"
                if failed
                else "PASS"
            )

        except Exception as exc:

            results.append(
                {
                    "unit_id":
                        unit["unit_id"],
                    "guest":
                        unit.get("guest"),
                    "status":
                        "FAILED",
                    "error":
                        str(exc),
                }
            )

            print(
                "FAIL:",
                str(exc),
            )

    artifact = {
        "date": DATE,
        "schema_version":
            "research_summary_v0_2",
        "model": MODEL,
        "guest_count": len(results),
        "complete":
            sum(
                x["status"] == "COMPLETE"
                for x in results
            ),
        "review":
            sum(
                x["status"] == "REVIEW"
                for x in results
            ),
        "failed":
            sum(
                x["status"] == "FAILED"
                for x in results
            ),
        "summaries":
            results,
    }

    OUTPUT.write_text(
        json.dumps(
            artifact,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 100)
    print("RESULT")
    print("=" * 100)
    print(
        "COMPLETE:",
        artifact["complete"],
    )
    print(
        "REVIEW:",
        artifact["review"],
    )
    print(
        "FAILED:",
        artifact["failed"],
    )
    print(
        "OUTPUT:",
        OUTPUT,
    )
    print("=" * 100)


if __name__ == "__main__":
    main()
