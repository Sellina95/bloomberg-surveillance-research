from __future__ import annotations

import ast
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts" / "build_korean_presentation_v0_1.py"

FUNCTIONS = {
    "extract_numeric_tokens",
    "numeric_inventory",
    "value_at_json_path",
    "semantic_numeric_allowance",
    "compare_numeric_inventory",
}


# Load the exact production validator functions without executing
# the live Gemini/publication pipeline at module import time.
tree = ast.parse(
    SOURCE.read_text(encoding="utf-8"),
    filename=str(SOURCE),
)

body = [
    node
    for node in tree.body
    if isinstance(node, ast.FunctionDef)
    and node.name in FUNCTIONS
]

namespace = {"re": re}

exec(
    compile(
        ast.Module(body=body, type_ignores=[]),
        str(SOURCE),
        "exec",
    ),
    namespace,
)

compare_numeric_inventory = namespace[
    "compare_numeric_inventory"
]


def assert_pass(en: str, ko: str) -> None:
    result = compare_numeric_inventory(
        {"text": en},
        {"text": ko},
    )

    assert result["pass"], result["differences"]


def assert_fail(en: str, ko: str) -> None:
    result = compare_numeric_inventory(
        {"text": en},
        {"text": ko},
    )

    assert not result["pass"]


# English lexical numbers may translate naturally without
# becoming literal digits in Korean.
assert_pass(
    "Two risks remain around a 5% yield.",
    "5% 금리 주변에는 두 가지 리스크가 남아 있다.",
)

assert_pass(
    "Second-half conditions remain uncertain.",
    "하반기 여건은 여전히 불확실하다.",
)

# Literal financial numbers remain hard invariants.
assert_pass(
    "Yields range between 5% and 5.5%.",
    "금리는 5%에서 5.5% 사이에 있다.",
)

# Duplicate numeric claims must still fail.
assert_fail(
    "Yields range between 5% and 5.5%.",
    "금리는 5%, 5%, 5.5% 수준이다.",
)

# Changed numeric claims must still fail.
assert_fail(
    "Yields range between 5% and 5.5%.",
    "금리는 5%에서 6% 사이에 있다.",
)

print("KOREAN NUMERIC TRANSLATION CONTRACT: PASS")

# Conventional Korean numeric renderings that are explicitly
# licensed by the semantic allowance must remain valid.
assert_pass(
    "September inflation remains in focus.",
    "9월 인플레이션이 계속 주목된다.",
)

assert_pass(
    "Two-year Treasury yields remain elevated.",
    "2년물 미 국채 금리는 높은 수준을 유지한다.",
)

assert_pass(
    "Secondary effects remain uncertain.",
    "2차 효과는 여전히 불확실하다.",
)
