from __future__ import annotations

import copy
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from public_language_policy_v0_1 import (  # noqa: E402
    EN_DIRECTIVE,
    KO_DIRECTIVE,
    neutralize_report,
)


NUMBER = re.compile(r"[-+]?\d+(?:\.\d+)?%?")

report = {
    "research_takeaways": [
        "Investors should buy bonds and reduce equity exposure at 5%.",
    ],
    "daily_action": [
        {
            "action": "Scale into credit and go short volatility.",
            "why": "Do not sell after a 10% decline.",
            "what_to_monitor": "Enter only if yields exit the range.",
        }
    ],
}

before = copy.deepcopy(report)
changed = neutralize_report(report, "en")

assert changed == 4
assert not EN_DIRECTIVE.search(str(report))
assert NUMBER.findall(str(before)) == NUMBER.findall(str(report))

report = {
    "research_takeaways": [
        "금리 5%에서는 채권을 매수하고 주식 비중을 축소하세요.",
    ],
    "daily_action": [
        {
            "action": "분할 매수로 진입하십시오.",
            "why": "롱 포지션을 유지하세요.",
            "what_to_monitor": "기술주를 오버웨이트하십시오.",
        }
    ],
}

before = copy.deepcopy(report)
changed = neutralize_report(report, "ko")

assert changed == 4
assert not KO_DIRECTIVE.search(str(report))
assert NUMBER.findall(str(before)) == NUMBER.findall(str(report))
assert report["research_takeaways"][0] == (
    "모니터링 초점: 금리 5%에서는 채권 수요와 "
    "주식 비중 변화하는 흐름."
)

print("PUBLIC LANGUAGE POLICY: PASS")
