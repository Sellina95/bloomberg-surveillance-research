from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from public_language_policy_v0_1 import assert_non_prescriptive


safe = {
    "research_takeaways": ["Policy uncertainty remains a variable to monitor."],
    "daily_action": [{
        "action": "Monitor the rate path.",
        "why": "Volatility remains elevated.",
        "what_to_monitor": "Employment revisions.",
    }],
}
before = copy.deepcopy(safe)
assert_non_prescriptive(safe, "en")
assert safe == before

unsafe = copy.deepcopy(safe)
unsafe["daily_action"][0]["action"] = "Buy bonds."
try:
    assert_non_prescriptive(unsafe, "en")
except ValueError:
    pass
else:
    raise AssertionError("directive must fail closed")
assert unsafe["daily_action"][0]["action"] == "Buy bonds."

unsafe_ko = copy.deepcopy(safe)
unsafe_ko["research_takeaways"] = ["채권을 매수하세요."]
try:
    assert_non_prescriptive(unsafe_ko, "ko")
except ValueError:
    pass
else:
    raise AssertionError("Korean directive must fail closed")
assert unsafe_ko["research_takeaways"][0] == "채권을 매수하세요."

print("PUBLIC LANGUAGE POLICY: PASS — SEMANTIC MUTATIONS: 0")
