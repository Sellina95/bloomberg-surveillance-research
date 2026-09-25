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


# Descriptive Korean language must not be mistaken for a directive.
safe_ko_descriptive = copy.deepcopy(safe)
safe_ko_descriptive["research_takeaways"] = [
    "주식 시장은 조정을 거치지 않은 장기 상승 국면 이후 "
    "계절적 약세기에 진입하는 가운데 고베타 경기순환주 대비 "
    "대형 가치주와 우량 재무제표에 대한 선호가 관찰되고 있습니다."
]
assert_non_prescriptive(safe_ko_descriptive, "ko")

# Actual Korean imperative forms must still fail closed.
for directive in ("포지션에 진입하세요.", "자산을 축적하세요."):
    candidate = copy.deepcopy(safe)
    candidate["research_takeaways"] = [directive]
    try:
        assert_non_prescriptive(candidate, "ko")
    except ValueError:
        pass
    else:
        raise AssertionError(f"Korean directive must fail closed: {directive}")

print("PUBLIC LANGUAGE POLICY: PASS — SEMANTIC MUTATIONS: 0")
