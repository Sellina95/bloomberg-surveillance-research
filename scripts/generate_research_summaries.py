from __future__ import annotations

import json
import os
from pathlib import Path

from openai import OpenAI


DATES = [
    "2026-08-10",
    "2026-08-14",
]

BASE = Path(
    "data/processed/surveillance"
)

MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-5.6-luna",
)

client = OpenAI()


SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "topic": {
            "type": "string"
        },
        "key_views": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "why_it_matters": {
            "type": "string"
        },
        "market_implication": {
            "type": "string"
        },
        "research_tags": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "timestamp_seconds": {
                        "type": "number"
                    },
                    "text": {
                        "type": "string"
                    },
                    "supports": {
                        "type": "string"
                    }
                },
                "required": [
                    "timestamp_seconds",
                    "text",
                    "supports"
                ],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "topic",
        "key_views",
        "why_it_matters",
        "market_implication",
        "research_tags",
        "evidence",
    ],
    "additionalProperties": False,
}


SYSTEM_PROMPT = """
You are a financial research editor.

Your task is to summarize ONE Bloomberg Surveillance guest
interview using ONLY the supplied transcript.

STRICT SOURCE DISCIPLINE:

1. Do not use outside knowledge.
2. Do not invent facts.
3. Do not attribute a view to the guest unless the transcript
   supports it.
4. Preserve uncertainty when the guest is uncertain.
5. Distinguish the guest's stated view from analytical
   interpretation.
6. Every key view must be supported by transcript evidence.
7. Evidence must be copied from the supplied transcript.
8. Evidence timestamps must correspond to the supplied segment.
9. Do not fabricate numbers, forecasts, asset positions,
   organizations, or opinions.
10. Keep the result concise and useful for financial research.

OUTPUT:

topic:
The main subject discussed.

key_views:
1-3 most important views expressed by the guest.

why_it_matters:
Why the guest's view matters from a market/research perspective.
This must be an interpretation of the supplied discussion,
not an external fact.

market_implication:
The market implication suggested by the discussion.
Clearly distinguish interpretation from what the guest explicitly
said.

research_tags:
Short tags such as RATES, FED, INFLATION, USD, CREDIT,
LIQUIDITY, EQUITIES, AI, FISCAL, etc.
Only use tags supported by the transcript.

evidence:
Use the strongest transcript passages supporting the summary.
Do not manufacture quotations.
"""


def build_transcript_text(unit: dict) -> str:

    lines = []

    for segment in unit["transcript_segments"]:

        timestamp = (
            f"{segment['start_seconds']:.2f}s"
        )

        text = segment["text"].strip()

        if text:
            lines.append(
                f"[{timestamp}] {text}"
            )

    return "\n".join(lines)


def summarize_unit(unit: dict) -> dict:

    transcript = build_transcript_text(
        unit
    )

    user_prompt = f"""
GUEST:
{unit.get("guest", "")}

CHAPTER:
{unit.get("title", "")}

TIME RANGE:
{unit["start_seconds"]:.2f}s
to
{unit["end_seconds"]:.2f}s

TRANSCRIPT:
{transcript}
"""

    response = client.responses.create(
        model=MODEL,
        instructions=SYSTEM_PROMPT,
        input=user_prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "research_summary",
                "description":
                    "Structured financial research summary",
                "schema": SUMMARY_SCHEMA,
                "strict": True,
            }
        },
    )

    return json.loads(
        response.output_text
    )


def main() -> None:

    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit(
            "FAIL — OPENAI_API_KEY is not set"
        )

    for date in DATES:

        input_path = (
            BASE
            / date
            / "guest_transcripts.json"
        )

        output_path = (
            BASE
            / date
            / "research_summaries_llm.json"
        )

        data = json.loads(
            input_path.read_text(
                encoding="utf-8"
            )
        )

        results = []

        print("=" * 100)
        print("RESEARCH SUMMARY GENERATION")
        print("DATE:", date)
        print("MODEL:", MODEL)
        print(
            "GUESTS:",
            len(data["units"])
        )
        print("=" * 100)

        for unit in data["units"]:

            print(
                f"PROCESSING UNIT "
                f"{unit['unit_id']:02d}..."
            )

            try:

                summary = summarize_unit(
                    unit
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
                            summary,
                        "source":
                            {
                                "transcript":
                                    "supadata",
                                "chapters":
                                    "serpapi",
                            },
                        "status":
                            "COMPLETE",
                    }
                )

                print("  PASS")

            except Exception as exc:

                print(
                    "  FAIL:",
                    str(exc)
                )

                results.append(
                    {
                        "unit_id":
                            unit["unit_id"],
                        "chapter":
                            unit["chapter"],
                        "guest":
                            unit.get("guest"),
                        "status":
                            "FAILED",
                        "error":
                            str(exc),
                    }
                )

        artifact = {
            "date": date,
            "schema_version":
                "research_summary_v0_2",
            "model": MODEL,
            "guest_count":
                len(results),
            "completed":
                sum(
                    r["status"] == "COMPLETE"
                    for r in results
                ),
            "failed":
                sum(
                    r["status"] == "FAILED"
                    for r in results
                ),
            "summaries":
                results,
        }

        output_path.write_text(
            json.dumps(
                artifact,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        print()
        print(
            "OUTPUT:",
            output_path
        )


if __name__ == "__main__":
    main()
