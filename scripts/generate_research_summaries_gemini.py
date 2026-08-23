from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.request import Request, urlopen


DATE = "2026-08-14"

INPUT = Path(
    f"data/processed/surveillance/{DATE}/"
    "guest_transcripts.json"
)

OUTPUT = Path(
    f"data/processed/surveillance/{DATE}/"
    "research_summaries_gemini.json"
)

MODEL = "gemini-3.5-flash-lite"

API_KEY = os.environ.get("GEMINI_API_KEY")


SYSTEM_PROMPT = """
You are a financial research editor.

Summarize ONE Bloomberg Surveillance guest interview.

Use ONLY the supplied transcript.

STRICT RULES:

1. Do not use outside knowledge.
2. Do not invent facts.
3. Do not attribute views that are not supported by the transcript.
4. Preserve uncertainty.
5. Separate the guest's stated view from your interpretation.
6. Every key view must have supporting evidence.
7. Evidence must come directly from the supplied transcript.
8. Evidence timestamps must come from the supplied transcript.
9. Do not invent numbers, forecasts, positions, organizations,
   or opinions.
10. Keep the summary concise.

Return ONLY valid JSON with this structure:

{
  "topic": "...",
  "key_views": [
    "...",
    "..."
  ],
  "why_it_matters": "...",
  "market_implication": "...",
  "research_tags": [
    "RATES",
    "FED"
  ],
  "evidence": [
    {
      "timestamp_seconds": 0,
      "text": "...",
      "supports": "..."
    }
  ]
}
"""


def call_gemini(transcript: str, guest: str, title: str) -> dict:

    prompt = f"""
{SYSTEM_PROMPT}

GUEST:
{guest}

CHAPTER:
{title}

TRANSCRIPT:
{transcript}
"""

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{MODEL}:generateContent"
    )

    body = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
        },
    }

    request = Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": API_KEY,
        },
        method="POST",
    )

    with urlopen(
        request,
        timeout=180,
    ) as response:

        result = json.loads(
            response.read().decode("utf-8")
        )

    try:
        text = (
            result["candidates"][0]
            ["content"]["parts"][0]["text"]
        )
    except (KeyError, IndexError):
        raise RuntimeError(
            f"Gemini returned unexpected response: "
            f"{json.dumps(result)[:2000]}"
        )

    return json.loads(text)


def build_transcript(unit: dict) -> str:

    lines = []

    for segment in unit["transcript_segments"]:

        text = segment["text"].strip()

        if not text:
            continue

        lines.append(
            f"[{segment['start_seconds']:.2f}s] {text}"
        )

    return "\n".join(lines)


def main():

    if not API_KEY:
        raise SystemExit(
            "FAIL — GEMINI_API_KEY is not set"
        )

    data = json.loads(
        INPUT.read_text(
            encoding="utf-8"
        )
    )

    results = []

    print("=" * 100)
    print("GEMINI RESEARCH SUMMARY")
    print("=" * 100)
    print("DATE:", DATE)
    print("MODEL:", MODEL)
    print(
        "GUESTS:",
        len(data["units"])
    )
    print("=" * 100)

    # --------------------------------------------------------
    # FIRST RUN: only one guest
    # --------------------------------------------------------

    units = data["units"]

    for unit in units:

        print(
            f"PROCESSING UNIT "
            f"{unit['unit_id']:02d}..."
        )

        transcript = build_transcript(
            unit
        )

        try:

            summary = call_gemini(
                transcript=transcript,
                guest=unit.get("guest", ""),
                title=unit.get("title", ""),
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

            print("PASS")

        except Exception as exc:

            print(
                "FAIL:",
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
        "date": DATE,
        "model": MODEL,
        "requested_units": len(units),
        "completed": sum(
            x["status"] == "COMPLETE"
            for x in results
        ),
        "failed": sum(
            x["status"] == "FAILED"
            for x in results
        ),
        "summaries": results,
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
        "COMPLETED:",
        artifact["completed"],
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
