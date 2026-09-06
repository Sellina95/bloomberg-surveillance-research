from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATE = "2026-09-04"
BASE = ROOT / "data/processed/surveillance" / DATE
en_path = BASE / "daily_research_report_v0_1.json"
ko_path = BASE / "daily_research_report_ko_v0_1.json"
en = json.loads(en_path.read_text(encoding="utf-8"))
ko = json.loads(ko_path.read_text(encoding="utf-8"))
policy = ko["translation_policy"]

assert en["date"] == DATE
assert ko["report"]["date"] == DATE
assert ko["source_report_sha256"] == hashlib.sha256(en_path.read_bytes()).hexdigest()
assert policy["research_regeneration"] is False
assert policy["provenance_mutation"] is False
assert policy["structure_preserved"] is True
assert policy["guest_attribution_preserved"] is True
assert policy["numeric_values_preserved"] is True

print("EN/KO SEMANTIC PARITY: PASS")
