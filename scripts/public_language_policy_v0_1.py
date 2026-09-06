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

def assert_non_prescriptive(report: dict[str, Any], language: str) -> None:
    """Fail closed; never rewrite model language with lexical substitutions."""
    pattern = EN_DIRECTIVE if language == "en" else KO_DIRECTIVE
    violations = []

    takeaways = report.get("research_takeaways", [])
    if isinstance(takeaways, list):
        for index, value in enumerate(takeaways):
            if not isinstance(value, str):
                continue
            if pattern.search(value):
                violations.append(f"research_takeaways[{index}]")

    actions = report.get("daily_action", [])
    if isinstance(actions, list):
        for row in actions:
            if not isinstance(row, dict):
                continue
            for field in ("action", "why", "what_to_monitor"):
                value = row.get(field)
                if not isinstance(value, str):
                    continue
                if pattern.search(value):
                    violations.append(f"daily_action.{field}")

    if violations:
        raise ValueError(
            "non-prescriptive language contract failed: " + ", ".join(violations)
        )


def directive_locations(report: dict[str, Any], language: str):
    """Return mutable field references for sentence-scoped regeneration."""
    pattern = EN_DIRECTIVE if language == "en" else KO_DIRECTIVE
    found = []
    takeaways = report.get("research_takeaways", [])
    if isinstance(takeaways, list):
        for index, value in enumerate(takeaways):
            if isinstance(value, str) and pattern.search(value):
                found.append((takeaways, index, f"research_takeaways[{index}]"))
    actions = report.get("daily_action", [])
    if isinstance(actions, list):
        for index, row in enumerate(actions):
            if not isinstance(row, dict):
                continue
            for field in ("action", "why", "what_to_monitor"):
                value = row.get(field)
                if isinstance(value, str) and pattern.search(value):
                    found.append((row, field, f"daily_action[{index}].{field}"))
    return found
