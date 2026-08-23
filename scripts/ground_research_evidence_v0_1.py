from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from pathlib import Path


DATE = "2026-08-14"

BASE = Path(
    f"data/processed/surveillance/{DATE}"
)

SUMMARY = BASE / "research_summaries_gemini.json"
CANONICAL = BASE / "youtube_canonical.json"

OUTPUT = BASE / "research_summaries_grounded.json"


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(
        None,
        normalize(a),
        normalize(b),
    ).ratio()


def find_evidence(
    claim: str,
    segments: list[dict],
    top_n: int = 2,
) -> list[dict]:

    scored = []

    claim_norm = normalize(claim)

    if not claim_norm:
        return []

    for segment in segments:

        text = segment["text"].strip()

        if not text:
            continue

        text_norm = normalize(text)

        # Strong lexical overlap
        claim_words = set(
            claim_norm.split()
        )

        text_words = set(
            text_norm.split()
        )

        overlap = (
            len(claim_words & text_words)
            / max(len(claim_words), 1)
        )

        # Sequence similarity
        seq = similarity(
            claim,
            text,
        )

        score = (
            overlap * 0.65
            + seq * 0.35
        )

        scored.append(
            (
                score,
                segment,
            )
        )

    scored.sort(
        key=lambda x: x[0],
        reverse=True,
    )

    results = []

    for score, segment in scored[:top_n]:

        # Do not attach weak evidence.
        if score < 0.25:
            continue

        results.append(
            {
                "timestamp_seconds":
                    segment["start_seconds"],
                "text":
                    segment["text"],
                "match_score":
                    round(score, 4),
                "source":
                    "youtube_canonical",
            }
        )

    return results


summaries = json.loads(
    SUMMARY.read_text(
        encoding="utf-8"
    )
)

canonical = json.loads(
    CANONICAL.read_text(
        encoding="utf-8"
    )
)

segments = canonical["segments"]

grounded_units = []

print("=" * 100)
print("RESEARCH EVIDENCE GROUNDING v0.1")
print("=" * 100)
print("DATE:", DATE)
print(
    "SUMMARY UNITS:",
    len(summaries["summaries"]),
)
print(
    "CANONICAL SEGMENTS:",
    len(segments),
)
print("=" * 100)


for unit in summaries["summaries"]:

    if unit["status"] != "COMPLETE":
        continue

    summary = unit["summary"]

    grounded_key_views = []

    for claim in summary.get(
        "key_views",
        [],
    ):

        evidence = find_evidence(
            claim,
            segments,
            top_n=2,
        )

        grounded_key_views.append(
            {
                "claim": claim,
                "evidence": evidence,
                "grounding_status":
                    (
                        "GROUNDED"
                        if evidence
                        else "UNSUPPORTED"
                    ),
            }
        )

    # Market implication is kept separate.
    # We do NOT pretend it is a direct quote.
    market_implication = {
        "text":
            summary.get(
                "market_implication",
                "",
            ),
        "type":
            "MODEL_INTERPRETATION",
    }

    grounded_units.append(
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
                unit["timestamp"],

            "topic":
                summary.get("topic"),

            "key_views":
                grounded_key_views,

            "why_it_matters":
                {
                    "text":
                        summary.get(
                            "why_it_matters",
                            "",
                        ),
                    "type":
                        "MODEL_INTERPRETATION",
                },

            "market_implication":
                market_implication,

            "research_tags":
                summary.get(
                    "research_tags",
                    [],
                ),

            "original_llm_evidence":
                summary.get(
                    "evidence",
                    [],
                ),
        }
    )


total_claims = 0
grounded_claims = 0

for unit in grounded_units:

    for claim in unit["key_views"]:

        total_claims += 1

        if (
            claim["grounding_status"]
            == "GROUNDED"
        ):
            grounded_claims += 1


grounding_rate = (
    grounded_claims
    / total_claims
    * 100
    if total_claims
    else 0
)


artifact = {
    "date": DATE,
    "schema_version":
        "research_summary_grounded_v0_1",
    "source_summary":
        str(SUMMARY),
    "source_transcript":
        str(CANONICAL),
    "total_key_views":
        total_claims,
    "grounded_key_views":
        grounded_claims,
    "unsupported_key_views":
        total_claims - grounded_claims,
    "grounding_rate_percent":
        grounding_rate,
    "units":
        grounded_units,
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
print("SUMMARY")
print("=" * 100)
print(
    "KEY VIEWS:",
    total_claims,
)
print(
    "GROUNDED:",
    grounded_claims,
)
print(
    "UNSUPPORTED:",
    total_claims - grounded_claims,
)
print(
    f"GROUNDING RATE: {grounding_rate:.2f}%"
)

print()
print("OUTPUT:", OUTPUT)
print("=" * 100)
