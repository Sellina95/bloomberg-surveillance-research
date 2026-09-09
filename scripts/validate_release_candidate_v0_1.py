from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.processing.verbatim_gate import exposure_failures, strings


DATE = os.environ.get("SURVEILLANCE_DATE", "")
if not DATE:
    raise SystemExit("PUBLIC SURFACE GATE: FAIL — SURVEILLANCE_DATE missing")
BASE = ROOT / "data/processed/surveillance" / DATE
RAW = ROOT / "data/raw/youtube" / DATE / "transcript.json"

FILES = (
    "daily_research_report_v0_1.json",
    "daily_research_report_v0_1.md",
    "daily_research_report_ko_v0_1.json",
    "daily_research_report_tv_v0_1.html",
    "daily_research_report_tv_ko_v0_1.html",
    "report_provenance_v0_1.json",
)


def main() -> None:
    missing = [name for name in FILES if not (BASE / name).exists()]
    if missing:
        raise SystemExit("PUBLIC SURFACE GATE: FAIL — missing " + ", ".join(missing))

    en_path = BASE / FILES[0]
    en = json.loads(en_path.read_text(encoding="utf-8"))
    ko = json.loads((BASE / FILES[2]).read_text(encoding="utf-8"))
    provenance = json.loads((BASE / FILES[5]).read_text(encoding="utf-8"))
    ko_report = ko.get("report", ko)
    if en.get("date") != DATE or ko_report.get("date") != DATE:
        raise SystemExit("EN/KO SEMANTIC PARITY: FAIL — date mismatch")

    policy = ko.get("translation_policy", {})
    invariants = (
        "structure_preserved", "guest_attribution_preserved", "numeric_values_preserved"
    )
    if not all(policy.get(name) is True for name in invariants):
        raise SystemExit("EN/KO SEMANTIC PARITY: FAIL — translation invariant")
    expected_sha = hashlib.sha256(en_path.read_bytes()).hexdigest()
    if ko.get("source_report_sha256") != expected_sha:
        raise SystemExit("EN/KO SEMANTIC PARITY: FAIL — source hash mismatch")

    source = provenance.get("source", {})
    if provenance.get("report_date") != DATE or source.get("broadcast_date") != DATE:
        raise SystemExit("PROVENANCE CONTRACT: FAIL — date mismatch")
    if source.get("broadcast_date_basis") not in {
        "provider_broadcast_date",
        "title_or_description",
        "official_full_show_upload_date",
    }:
        raise SystemExit("PROVENANCE CONTRACT: FAIL — broadcast date basis missing")
    if not provenance.get("claims"):
        raise SystemExit("PROVENANCE CONTRACT: FAIL — claims missing")
    if '"text"' in json.dumps(provenance, ensure_ascii=False).lower():
        raise SystemExit("PROVENANCE CONTRACT: FAIL — source text present")

    if not RAW.exists():
        raise SystemExit("VERBATIM EXPOSURE: FAIL — private source unavailable")
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    private_values = [
        str(row.get("text", ""))
        for row in raw.get("content", [])
        if isinstance(row, dict)
    ]
    failures = exposure_failures(strings(en), private_values)
    if failures:
        raise SystemExit("VERBATIM EXPOSURE: FAIL — " + failures[0])

    for name in (FILES[3], FILES[4]):
        html = (BASE / name).read_text(encoding="utf-8", errors="replace").lower()
        if "not affiliated with or" not in html or "endorsed by bloomberg" not in html:
            raise SystemExit("PUBLIC SURFACE GATE: FAIL — non-affiliation disclosure")
        if "research material, not a trading signal" not in html:
            raise SystemExit("PUBLIC SURFACE GATE: FAIL — research-use disclosure")

    print("PROVENANCE CONTRACT: PASS")
    print("EN/KO SEMANTIC PARITY: PASS")
    print("VERBATIM EXPOSURE: 0")
    print("PUBLIC SURFACE GATE: PASS")


if __name__ == "__main__":
    main()
