from __future__ import annotations

import json
import re
from pathlib import Path


DATE = "2026-08-14"

BASE = Path(
    f"data/processed/surveillance/{DATE}"
)

SUMMARY = BASE / "research_summaries_gemini.json"
CANONICAL = BASE / "youtube_canonical.json"
OUTPUT = BASE / "research_summary_evidence_audit_v0_2.json"

WINDOW_SECONDS = 10.0


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def build_window(
    segments: list[dict],
    timestamp: float,
) -> str:

    rows = [
        s
        for s in segments
        if abs(
            float(s["start_seconds"]) - timestamp
        ) <= WINDOW_SECONDS
    ]

    rows.sort(
        key=lambda x: float(x["start_seconds"])
    )

    return normalize(
        " ".join(
            s["text"]
            for s in rows
        )
    )


summaries = json.loads(
    SUMMARY.read_text(encoding="utf-8")
)

canonical = json.loads(
    CANONICAL.read_text(encoding="utf-8")
)

segments = canonical["segments"]

total = 0
matched = 0
failed = 0

units = []

print("=" * 100)
print("RESEARCH SUMMARY EVIDENCE AUDIT v0.2")
print("=" * 100)
print("DATE:", DATE)
print("WINDOW:", f"+/- {WINDOW_SECONDS:.0f}s")
print("SUMMARY UNITS:", len(summaries["summaries"]))
print("CANONICAL SEGMENTS:", len(segments))
print("=" * 100)


for unit in summaries["summaries"]:

    if unit["status"] != "COMPLETE":
        continue

    evidence_results = []

    for evidence in unit["summary"].get(
        "evidence", []
    ):

        total += 1

        timestamp = float(
            evidence["timestamp_seconds"]
        )

        target = normalize(
            evidence["text"]
        )

        window = build_window(
            segments,
            timestamp,
        )

        is_match = (
            bool(target)
            and (
                target in window
                or window in target
            )
        )

        if is_match:
            matched += 1
            status = "PASS"
        else:
            failed += 1
            status = "FAIL"

        evidence_results.append(
            {
                "timestamp_seconds": timestamp,
                "status": status,
                "evidence_text":
                    evidence["text"],
            }
        )

    unit_pass = all(
        x["status"] == "PASS"
        for x in evidence_results
    )

    units.append(
        {
            "unit_id": unit["unit_id"],
            "guest": unit.get("guest"),
            "evidence_count":
                len(evidence_results),
            "matched":
                sum(
                    x["status"] == "PASS"
                    for x in evidence_results
                ),
            "failed":
                sum(
                    x["status"] == "FAIL"
                    for x in evidence_results
                ),
            "status":
                "PASS" if unit_pass else "REVIEW",
            "evidence":
                evidence_results,
        }
    )


match_rate = (
    matched / total * 100
    if total
    else 0.0
)

overall = (
    "PASS"
    if failed == 0
    else "REVIEW"
)

artifact = {
    "date": DATE,
    "audit_version":
        "research_summary_evidence_v0_2",
    "window_seconds":
        WINDOW_SECONDS,
    "total_evidence":
        total,
    "matched_evidence":
        matched,
    "failed_evidence":
        failed,
    "match_rate_percent":
        match_rate,
    "overall":
        overall,
    "units":
        units,
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
print("TOTAL EVIDENCE:", total)
print("MATCHED:", matched)
print("FAILED:", failed)
print(
    f"EVIDENCE MATCH RATE: {match_rate:.2f}%"
)
print()
print("AUDIT RESULT:", overall)
print("OUTPUT:", OUTPUT)
print("=" * 100)
