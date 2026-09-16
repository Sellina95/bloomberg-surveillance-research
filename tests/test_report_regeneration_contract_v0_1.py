from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS))

spec = importlib.util.spec_from_file_location(
    "daily_report_builder_under_test",
    SCRIPTS / "build_daily_research_report_v0_1.py",
)
builder = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(builder)


def test_no_directive_does_not_regenerate():
    calls = []

    def fake_generate(client, prompt):
        calls.append(prompt)
        raise AssertionError(
            "regeneration API must not be called for non-directive prose"
        )

    original_generate = builder.generate_with_retry
    builder.generate_with_retry = fake_generate

    try:
        report = {
            "research_takeaways": [
                "USD liquidity conditions remain an important monitoring variable."
            ]
        }

        builder.regenerate_problem_sentences(object(), report)

        assert calls == []
        print("REPORT REGENERATION NO-DIRECTIVE: PASS")
    finally:
        builder.generate_with_retry = original_generate


def test_directive_regenerates_and_preserves_numeric_tokens():
    calls = []

    def fake_generate(client, prompt):
        calls.append(prompt)
        return SimpleNamespace(
            text=(
                "A 5% allocation remains a scenario to monitor "
                "rather than a portfolio instruction."
            )
        )

    original_generate = builder.generate_with_retry
    builder.generate_with_retry = fake_generate

    try:
        report = {
            "research_takeaways": [
                "Buy the position at a 5% allocation."
            ]
        }

        builder.regenerate_problem_sentences(object(), report)

        assert len(calls) == 1
        assert "5%" in report["research_takeaways"][0]
        assert "Buy" not in report["research_takeaways"][0]

        builder.assert_non_prescriptive(report, "en")

        print("REPORT REGENERATION DIRECTIVE: PASS")
        print("NUMERIC PRESERVATION: PASS")
    finally:
        builder.generate_with_retry = original_generate


def test_changed_numeric_value_fails_closed():
    calls = []

    def fake_generate(client, prompt):
        calls.append(prompt)
        return SimpleNamespace(
            text="A 7% allocation remains a scenario to monitor."
        )

    original_generate = builder.generate_with_retry
    builder.generate_with_retry = fake_generate

    try:
        report = {
            "research_takeaways": [
                "Buy the position at a 5% allocation."
            ]
        }

        try:
            builder.regenerate_problem_sentences(object(), report)
        except Exception:
            pass
        else:
            raise AssertionError(
                "numeric-changing regeneration must fail closed"
            )

        # The original directive must not have been silently replaced
        # by prose containing a different numeric value.
        assert "7%" not in report["research_takeaways"][0]

        print("FAIL-CLOSED REGENERATION (NUMERIC CHANGE): PASS")
    finally:
        builder.generate_with_retry = original_generate


def test_still_directive_fails_closed():
    calls = []

    def fake_generate(client, prompt):
        calls.append(prompt)
        return SimpleNamespace(
            text="Buy the position at a 5% allocation."
        )

    original_generate = builder.generate_with_retry
    builder.generate_with_retry = fake_generate

    try:
        report = {
            "research_takeaways": [
                "Buy the position at a 5% allocation."
            ]
        }

        try:
            builder.regenerate_problem_sentences(object(), report)
        except Exception:
            print("FAIL-CLOSED REGENERATION (STILL DIRECTIVE): PASS")
        else:
            raise AssertionError(
                "still-prescriptive regeneration must fail closed"
            )
    finally:
        builder.generate_with_retry = original_generate


if __name__ == "__main__":
    test_no_directive_does_not_regenerate()
    test_directive_regenerates_and_preserves_numeric_tokens()
    test_changed_numeric_value_fails_closed()
    test_still_directive_fails_closed()
    print("REPORT REGENERATION CONTRACT: PASS")
