from __future__ import annotations

import re
from typing import Any


EN_DIRECTIVE = re.compile(
    r"\b("
    r"buy|sell|accumulate|reduce|overweight|underweight|"
    r"enter|exit|go long|go short|scale into"
    r")\b",
    re.I,
)

KO_DIRECTIVE = re.compile(
    r"매수|매도|분할\s*매수|"
    r"비중(?:을)?\s*확대|비중(?:을)?\s*축소|"
    r"오버웨이트|언더웨이트|축적하|진입하|"
    r"롱\s*포지션을\s*유지|선호하십시오"
)

EN_REPLACEMENTS = (
    (re.compile(r"\bscale into\b", re.I), "phased positioning in"),
    (re.compile(r"\bgo long\b", re.I), "upside positioning in"),
    (re.compile(r"\bgo short\b", re.I), "downside positioning in"),
    (re.compile(r"\boverweight\b", re.I), "relative-strength positioning in"),
    (re.compile(r"\bunderweight\b", re.I), "relative-weakness positioning in"),
    (re.compile(r"\baccumulate\b", re.I), "positioning build-up in"),
    (re.compile(r"\breduce\b", re.I), "reduction in"),
    (re.compile(r"\benter\b", re.I), "participation in"),
    (re.compile(r"\bexit\b", re.I), "withdrawal from"),
    (re.compile(r"\bbuy\b", re.I), "demand for"),
    (re.compile(r"\bsell\b", re.I), "supply of"),
)

KO_REPLACEMENTS = (
    (
        re.compile(
            r"([가-힣A-Za-z0-9.%]+)[을를]\s*매수하고"
        ),
        r"\1 수요와",
    ),
    (
        re.compile(
            r"([가-힣A-Za-z0-9.%]+)[을를]\s*매도하고"
        ),
        r"\1 공급과",
    ),
    (re.compile(r"분할\s*매수"), "단계적 수요"),
    (re.compile(r"비중(?:을)?\s*확대"), "비중 변화"),
    (re.compile(r"비중(?:을)?\s*축소"), "비중 변화"),
    (re.compile(r"롱\s*포지션을\s*유지"), "상방 포지셔닝 지속"),
    (re.compile(r"선호하십시오"), "상대 선호도"),
    (re.compile(r"오버웨이트"), "상대 강세 포지셔닝"),
    (re.compile(r"언더웨이트"), "상대 약세 포지셔닝"),
    (re.compile(r"매수"), "수요"),
    (re.compile(r"매도"), "공급"),
    (re.compile(r"축적하"), "누적되"),
    (re.compile(r"진입하"), "참여하"),
)


def neutralize_text(value: str, language: str) -> tuple[str, bool]:
    pattern = EN_DIRECTIVE if language == "en" else KO_DIRECTIVE

    if not pattern.search(value):
        return value, False

    result = value

    if language == "en":
        result = re.sub(
            r"\b(?:investors?|traders?|portfolios?)\s+"
            r"(?:should|must|need to|consider)\s+",
            "",
            result,
            flags=re.I,
        )
        for target, replacement in EN_REPLACEMENTS:
            result = target.sub(replacement, result)
        prefix = "Monitoring focus: "
    else:
        for target, replacement in KO_REPLACEMENTS:
            result = target.sub(replacement, result)
        result = re.sub(r"하십시오|하세요", "하는 흐름", result)
        result = re.sub(
            r"해야\s*합니다",
            "필요성이 관찰됩니다",
            result,
        )
        prefix = "모니터링 초점: "

    if pattern.search(result):
        raise ValueError(
            f"directive normalization incomplete ({language}): {result}"
        )

    if not result.startswith(prefix):
        result = prefix + result

    return result, True


def neutralize_report(report: dict[str, Any], language: str) -> int:
    changed = 0

    takeaways = report.get("research_takeaways", [])
    if isinstance(takeaways, list):
        for index, value in enumerate(takeaways):
            if not isinstance(value, str):
                continue
            takeaways[index], updated = neutralize_text(value, language)
            changed += int(updated)

    actions = report.get("daily_action", [])
    if isinstance(actions, list):
        for row in actions:
            if not isinstance(row, dict):
                continue
            for field in ("action", "why", "what_to_monitor"):
                value = row.get(field)
                if not isinstance(value, str):
                    continue
                row[field], updated = neutralize_text(value, language)
                changed += int(updated)

    return changed
