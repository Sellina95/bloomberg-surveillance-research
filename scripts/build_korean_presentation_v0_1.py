from __future__ import annotations

import hashlib
import json
import os
import time
import re
from pathlib import Path

from google import genai


DATE = os.environ.get(
    "SURVEILLANCE_DATE",
    "2026-08-24",
)

MODEL = "gemini-3.5-flash-lite"

BASE = Path(
    f"data/processed/surveillance/{DATE}"
)

INPUT = (
    BASE / "daily_research_report_v0_1.json"
)

OUTPUT = (
    BASE / "daily_research_report_ko_v0_1.json"
)

# Private runtime checkpoint.
# Validation candidates must never enter the public artifact
# unless every semantic-preservation gate passes.
CANDIDATE = Path(
    f"/tmp/korean_presentation_candidate_"
    f"{DATE.replace('-', '')}_v0_1.json"
)


API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise SystemExit(
        "FAIL — GEMINI_API_KEY is not set"
    )

if not INPUT.exists():
    raise SystemExit(
        f"FAIL — source report not found: {INPUT}"
    )


# ============================================================
# Source / lineage
# ============================================================

source_bytes = INPUT.read_bytes()

source_sha256 = hashlib.sha256(
    source_bytes
).hexdigest()

source_report = json.loads(
    source_bytes.decode("utf-8")
)


# ============================================================
# Structural helpers
# ============================================================

def structure_signature(value):
    """
    Preserve JSON structure while ignoring human-readable text.
    """

    if isinstance(value, dict):
        return {
            key: structure_signature(child)
            for key, child in value.items()
        }

    if isinstance(value, list):
        return [
            structure_signature(child)
            for child in value
        ]

    if isinstance(value, str):
        return "<STR>"

    if value is None:
        return None

    return type(value).__name__


def extract_numeric_tokens(text):
    """
    Extract semantic numeric expressions for translation
    parity at the same JSON path.

    Explicit numeric tokens preserve textual form, while
    common English month names and ordinal number words are
    normalized to the numeric form naturally used in Korean.

    Examples:
      September -> 9
      December  -> 12
      fifth     -> 5
      50        -> 50
      5%        -> 5%
    """

    tokens = re.findall(
        r"""
        (?<![A-Za-z])
        \$?
        \d+(?:\.\d+)?
        %?
        """,
        text,
        flags=re.VERBOSE,
    )

    semantic_numbers = {
        "january": "1",
        "february": "2",
        "march": "3",
        "april": "4",
        # "may" intentionally excluded:
        # ambiguous between calendar month and modal verb.
        "june": "6",
        "july": "7",
        "august": "8",
        "september": "9",
        "october": "10",
        "november": "11",
        "december": "12",
        "one": "1",
        "two": "2",
        "three": "3",
        "four": "4",
        "five": "5",
        "six": "6",
        "seven": "7",
        "eight": "8",
        "nine": "9",
        "ten": "10",
        "first": "1",
        "second": "2",
        "third": "3",
        "fourth": "4",
        "fifth": "5",
        "sixth": "6",
        "seventh": "7",
        "eighth": "8",
        "ninth": "9",
        "tenth": "10",
    }

    words = re.findall(
        r"\b[A-Za-z]+\b",
        text.lower(),
    )

    for word in words:
        normalized = semantic_numbers.get(word)
        if normalized is not None:
            tokens.append(normalized)

    return tokens


def numeric_inventory(value, path="$"):
    """
    Return numeric tokens keyed by exact JSON path.

    Only string leaves containing numeric expressions
    enter the contract.
    """

    inventory = {}

    if isinstance(value, dict):

        for key, child in value.items():

            inventory.update(
                numeric_inventory(
                    child,
                    f"{path}.{key}",
                )
            )

    elif isinstance(value, list):

        for index, child in enumerate(value):

            inventory.update(
                numeric_inventory(
                    child,
                    f"{path}[{index}]",
                )
            )

    elif isinstance(value, str):

        tokens = extract_numeric_tokens(
            value
        )

        if tokens:
            inventory[path] = tokens

    return inventory


def value_at_json_path(
    root,
    path,
):
    """
    Resolve a path emitted by numeric_inventory() back to
    its exact JSON leaf value.

    Supported grammar:
        $
        $.key
        $.key[index]
        $.key[index].child
    """

    if path == "$":
        return root

    if not path.startswith("$"):
        raise ValueError(
            f"invalid JSON path: {path}"
        )

    current = root
    i = 1

    while i < len(path):

        if path[i] == ".":

            i += 1
            start = i

            while (
                i < len(path)
                and path[i] not in ".["
            ):
                i += 1

            key = path[start:i]

            if not isinstance(current, dict):
                raise KeyError(path)

            current = current[key]

        elif path[i] == "[":

            end = path.find("]", i)

            if end == -1:
                raise ValueError(
                    f"invalid JSON path: {path}"
                )

            index_text = path[
                i + 1:end
            ]

            if not index_text.isdigit():
                raise ValueError(
                    f"invalid list index in path: {path}"
                )

            if not isinstance(current, list):
                raise KeyError(path)

            current = current[
                int(index_text)
            ]

            i = end + 1

        else:
            raise ValueError(
                f"invalid JSON path: {path}"
            )

    return current



def semantic_numeric_allowance(
    source_text,
    translated_text,
):
    """
    Return numeric tokens that are semantically licensed by
    explicit source-language expressions.

    This is deliberately narrow.

    Human-reviewed equivalences frozen from the 2026-08-24
    Korean presentation candidate:

        two-year   -> 2년
        secondary  -> 2차

    The function does NOT approve arbitrary added numbers.
    """

    allowances = []

    source_lower = source_text.lower()

    if (
        "two-year" in source_lower
        and "2년" in translated_text
    ):
        allowances.append("2")

    if (
        "secondary" in source_lower
        and "2차" in translated_text
    ):
        allowances.append("2")

    return allowances



def compare_numeric_inventory(
    source,
    translated,
):
    """
    Exact path-level numeric invariant comparison.

    A translation passes only when every source path
    containing numbers contains the exact same ordered
    numeric token sequence in Korean, and Korean adds no
    new numeric-bearing path.
    """

    source_inv = numeric_inventory(
        source
    )

    translated_inv = numeric_inventory(
        translated
    )

    all_paths = sorted(
        set(source_inv)
        | set(translated_inv)
    )

    differences = []

    for path in all_paths:

        source_tokens = source_inv.get(
            path,
            []
        )

        translated_tokens = translated_inv.get(
            path,
            []
        )

        # Numeric meaning is path-local, but token order is
        # not semantically invariant under translation.
        #
        # Example:
        #   "30-year reaches 6% before 10-year reaches 5%"
        # may legitimately become
        #   "10년물 5%보다 30년물 6%..."
        #
        # Therefore compare the multiset of numeric tokens
        # at the SAME JSON path. Counts remain significant:
        # ['2'] != ['2', '2'].

        source_value = value_at_json_path(
            source,
            path,
        )

        translated_value = value_at_json_path(
            translated,
            path,
        )

        source_text = (
            source_value
            if isinstance(source_value, str)
            else ""
        )

        translated_text = (
            translated_value
            if isinstance(translated_value, str)
            else ""
        )

        allowances = semantic_numeric_allowance(
            source_text,
            translated_text,
        )

        adjusted_translated_tokens = list(
            translated_tokens
        )

        for token in allowances:
            if token in adjusted_translated_tokens:
                adjusted_translated_tokens.remove(
                    token
                )

        if (
            sorted(source_tokens)
            == sorted(adjusted_translated_tokens)
        ):
            status = (
                "SEMANTIC_EQUIVALENT"
                if allowances
                else "EXACT"
            )

        elif (
            source_tokens
            and not adjusted_translated_tokens
        ):
            status = "REMOVED"

        elif (
            adjusted_translated_tokens
            and not source_tokens
        ):
            status = "ADDED"

        else:
            status = "CHANGED"

        if status not in {
            "EXACT",
            "SEMANTIC_EQUIVALENT",
        }:

            differences.append(
                {
                    "path":
                        path,

                    "status":
                        status,

                    "source_tokens":
                        source_tokens,

                    "translated_tokens":
                        translated_tokens,
                }
            )

    return {
        "source_inventory":
            source_inv,

        "translated_inventory":
            translated_inv,

        "differences":
            differences,

        "pass":
            len(differences) == 0,
    }


def list_counts(report):
    """
    High-value synthesis cardinality contract.
    """

    return {
        "executive_summary":
            len(
                report.get(
                    "executive_summary",
                    []
                )
            ),

        "macro_themes":
            len(
                report.get(
                    "macro_themes",
                    []
                )
            ),

        "cross_guest_consensus":
            len(
                report.get(
                    "cross_guest_consensus",
                    []
                )
            ),

        "cross_guest_conflicts":
            len(
                report.get(
                    "cross_guest_conflicts",
                    []
                )
            ),

        "key_risks":
            len(
                report.get(
                    "key_risks",
                    []
                )
            ),

        "research_takeaways":
            len(
                report.get(
                    "research_takeaways",
                    []
                )
            ),

        "daily_action":
            len(
                report.get(
                    "daily_action",
                    []
                )
            ),
    }


# ============================================================
# Translation prompt
# ============================================================

PROMPT = """
You are a translation layer for an institutional
financial research presentation.

Translate the supplied English daily research report
into professional Korean.

THIS IS TRANSLATION ONLY.

You are NOT performing new research.
You are NOT allowed to improve, reinterpret, summarize,
expand, weaken, strengthen, reconcile, or correct the
research.

STRICT RULES:

1. Preserve the JSON structure EXACTLY.
2. Preserve every dictionary key EXACTLY.
3. Preserve list ordering EXACTLY.
4. Preserve list lengths EXACTLY.
5. Preserve the date EXACTLY.
6. Preserve all numerical values exactly.
7. Preserve percentages and yield levels exactly.
8. NEVER introduce any numeric token that does not exist
   in the corresponding source JSON value.
   This includes years, months, dates, maturities, counts,
   rankings, quantities, percentages, and inferred numbers.
   Do NOT turn words into digits.
   Do NOT add explanatory numbers in parentheses.
   At each JSON path, the translated string must contain
   exactly the same numeric tokens as the source string,
   with the same textual form and multiplicity.
   Example: if the source path contains only "50", the
   translated value may contain "50" but MUST NOT introduce
   "5", "50%", "5-year", or any other numeric token.
   If the source path contains no numeric token, the
   translated value MUST contain no numeric token.
9. Preserve ticker symbols exactly.
9. Preserve proper names of guests and institutions
   in their original English form.
10. Preserve guest lists exactly.
11. Do NOT create or remove consensus.
12. Do NOT create or remove conflicts.
13. Do NOT alter certainty or uncertainty.
14. Do NOT convert a conditional statement into
    a definitive statement.
15. Do NOT convert analytical interpretation into
    a guest quotation.
16. Do NOT introduce transcript text or evidence
    that is not already present.
17. Translate only human-readable presentation prose.

FINANCIAL TERMINOLOGY:

Use concise institutional Korean terminology.
Do not over-explain standard market terminology.

Examples:
Treasury -> 미 국채
yield -> 금리 or 수익률 according to context
duration risk -> 듀레이션 리스크
term premium -> 기간 프리미엄
credit spread -> 신용 스프레드
free cash flow -> 잉여현금흐름
capital expenditure -> 자본지출
earnings revisions -> 이익 추정치 조정
financial conditions -> 금융여건

IMPORTANT:

The translated report must preserve the exact analytical
meaning of the English source.

Return ONLY valid JSON.
Do not wrap the JSON in markdown.
"""



def generate_with_transient_retry(
    client,
    prompt,
    *,
    label,
):
    max_attempts = 5

    for attempt in range(1, max_attempts + 1):
        try:
            return client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config={
                    "temperature": 0.0,
                    "response_mime_type":
                        "application/json",
                },
            )

        except Exception as exc:
            message = str(exc)

            is_transient = (
                "429" in message
                or "RESOURCE_EXHAUSTED" in message
                or "quota" in message.lower()
                or "500" in message
                or "502" in message
                or "503" in message
                or "504" in message
                or "UNAVAILABLE" in message
            )

            if not is_transient:
                raise

            if attempt >= max_attempts:
                raise

            retry_seconds = 40 * attempt

            print(
                "TRANSIENT GEMINI RETRY — "
                f"{label} "
                f"attempt {attempt}/{max_attempts - 1} "
                f"in {retry_seconds}s"
            )

            time.sleep(retry_seconds)


def translate(report):
    client = genai.Client(
        api_key=API_KEY
    )

    prompt = (
        PROMPT
        + "\n\nSOURCE REPORT:\n\n"
        + json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        )
    )

    response = generate_with_transient_retry(
        client,
        prompt,
        label="KOREAN TRANSLATION",
    )

    try:
        return json.loads(
            response.text
        )

    except json.JSONDecodeError as exc:
        raise SystemExit(
            "FAIL — translation model "
            "returned invalid JSON"
        ) from exc


def repair_numeric_translation(
    source_report,
    translated,
    numeric_differences,
):
    """
    One-shot repair for path-level numeric preservation
    failures. The model may edit only the Korean translation
    necessary to restore the reported numeric invariants.
    """

    client = genai.Client(
        api_key=API_KEY
    )

    repair_prompt = """
You are repairing an existing Korean translation of a
financial research report.

STRICT RULES:

1. Return ONLY valid JSON.
2. Preserve the JSON structure exactly.
3. Do NOT regenerate or summarize the research.
4. Do NOT change guest attribution.
5. Do NOT change dates.
6. Fix ONLY the translation errors identified in
   NUMERIC DIFFERENCES.
7. NUMERIC REPAIR IS STRICTLY PATH-LOCKED.
   A numeric token missing from one JSON path MUST be
   restored at that EXACT SAME JSON path.
   NEVER move, copy, relocate, or compensate for a numeric
   token by placing it at another JSON path.
8. For every path listed in NUMERIC DIFFERENCES, compare
   the English SOURCE REPORT value and the CURRENT KOREAN
   TRANSLATION value at that exact path.
   The repaired Korean value at that path MUST contain
   exactly the same numeric tokens as the English value,
   with the same textual form and multiplicity.
9. If a difference is REMOVED, restore the missing numeric
   token ONLY at the reported path.
10. If a difference is ADDED, remove the extra numeric
    token ONLY from the reported path.
11. If a difference is CHANGED, repair the numeric tokens
    ONLY at the reported path.
12. A path not listed in NUMERIC DIFFERENCES MUST NOT gain,
    lose, or change any numeric token.
13. Do not add numeric meanings that are absent from the
    corresponding English source.
14. Preserve all other Korean translation content unless
    a minimal edit at the reported path is required.

SOURCE REPORT:

""" + json.dumps(
        source_report,
        ensure_ascii=False,
        indent=2,
    ) + """

CURRENT KOREAN TRANSLATION:

""" + json.dumps(
        translated,
        ensure_ascii=False,
        indent=2,
    ) + """

NUMERIC DIFFERENCES:

""" + json.dumps(
        numeric_differences,
        ensure_ascii=False,
        indent=2,
    )

    response = generate_with_transient_retry(
        client,
        repair_prompt,
        label="KOREAN NUMERIC REPAIR",
    )

    try:
        return json.loads(
            response.text
        )

    except json.JSONDecodeError as exc:
        raise SystemExit(
            "FAIL — numeric repair model "
            "returned invalid JSON"
        ) from exc


# ============================================================
# Build
# ============================================================

print("=" * 100)
print("KOREAN PRESENTATION v0.1")
print("=" * 100)
print("DATE:", DATE)
print("MODEL:", MODEL)
print(
    "SOURCE SHA256:",
    source_sha256,
)

translated = translate(
    source_report
)

# Gemini may occasionally return valid JSON whose structure
# differs from the source. Do not weaken the structural gate:
# discard that candidate and perform one fresh translation
# before running the full validation suite.
if structure_signature(translated) != structure_signature(source_report):
    print()
    print(
        "STRUCTURAL PARITY FAILED — "
        "ATTEMPTING ONE FRESH TRANSLATION"
    )

    translated = translate(
        source_report
    )

candidate_serialized = (
    json.dumps(
        translated,
        ensure_ascii=False,
        indent=2,
    )
    + "\n"
)

CANDIDATE.write_text(
    candidate_serialized,
    encoding="utf-8",
)

print(
    "PRIVATE VALIDATION CANDIDATE:",
    CANDIDATE,
)


# ============================================================
# Mechanical semantic-preservation gates
# ============================================================

errors = []


# Gate A — structure

source_structure = structure_signature(
    source_report
)

translated_structure = structure_signature(
    translated
)

structure_pass = (
    source_structure
    == translated_structure
)

if not structure_pass:
    errors.append(
        "JSON structure changed"
    )


# Gate B — date

date_pass = (
    translated.get("date")
    == source_report.get("date")
    == DATE
)

if not date_pass:
    errors.append(
        "date changed"
    )


# Gate C — synthesis cardinality

source_counts = list_counts(
    source_report
)

translated_counts = list_counts(
    translated
)

count_pass = (
    source_counts
    == translated_counts
)

if not count_pass:
    errors.append(
        "high-value list cardinality changed"
    )


# Gate D — guest attribution lists

source_consensus = source_report.get(
    "cross_guest_consensus",
    []
)

translated_consensus = translated.get(
    "cross_guest_consensus",
    []
)

guest_pass = True

if (
    len(source_consensus)
    != len(translated_consensus)
):
    guest_pass = False

else:

    for source_item, ko_item in zip(
        source_consensus,
        translated_consensus,
    ):

        if (
            source_item.get("guests")
            != ko_item.get("guests")
        ):
            guest_pass = False
            break

if not guest_pass:
    errors.append(
        "consensus guest attribution changed"
    )


# Gate E — path-aware numeric preservation

numeric_result = compare_numeric_inventory(
    source_report,
    translated,
)

# Gemini translation is non-deterministic. If the first
# translation changes numeric meaning, attempt one constrained
# repair and then re-run the numeric gate.
if not numeric_result["pass"]:

    print()
    print(
        "NUMERIC VALIDATION FAILED — "
        "ATTEMPTING ONE REPAIR"
    )

    translated = repair_numeric_translation(
        source_report,
        translated,
        numeric_result["differences"],
    )

    # Preserve the repaired private candidate for audit.
    candidate_serialized = (
        json.dumps(
            translated,
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )

    CANDIDATE.write_text(
        candidate_serialized,
        encoding="utf-8",
    )

    numeric_result = compare_numeric_inventory(
        source_report,
        translated,
    )

    # If constrained numeric repair still fails, discard the
    # repaired candidate and perform one fresh translation.
    # This avoids publishing a translation whose numeric
    # meaning remains inconsistent with the English source.
    if not numeric_result["pass"]:
        print()
        print(
            "NUMERIC REPAIR FAILED — "
            "ATTEMPTING ONE FRESH TRANSLATION"
        )

        translated = translate(
            source_report
        )

        candidate_serialized = (
            json.dumps(
                translated,
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )

        CANDIDATE.write_text(
            candidate_serialized,
            encoding="utf-8",
        )

        numeric_result = compare_numeric_inventory(
            source_report,
            translated,
        )

numbers_pass = numeric_result[
    "pass"
]

numeric_differences = numeric_result[
    "differences"
]

source_numeric_paths = len(
    numeric_result[
        "source_inventory"
    ]
)

translated_numeric_paths = len(
    numeric_result[
        "translated_inventory"
    ]
)

if not numbers_pass:
    errors.append(
        "path-level numeric invariants changed"
    )



# ============================================================
# Artifact
# ============================================================

artifact = {
    "date":
        DATE,

    "schema_version":
        "daily_research_report_ko_v0_1",

    "language":
        "ko",

    "source_report":
        str(INPUT),

    "source_report_sha256":
        source_sha256,

    "translation_model":
        MODEL,

    "translation_policy": {
        "research_regeneration":
            False,

        "provenance_mutation":
            False,

        "structure_preserved":
            structure_pass,

        "guest_attribution_preserved":
            guest_pass,

        "numeric_values_preserved":
            numbers_pass,
    },

    "report":
        translated,
}


print()
print("[1] STRUCTURAL PARITY")
print(
    "PASS"
    if structure_pass
    else "FAIL"
)

print()
print("[2] DATE IMMUTABILITY")
print(
    "PASS"
    if date_pass
    else "FAIL"
)

print()
print("[3] SYNTHESIS CARDINALITY")
print(
    "SOURCE:",
    source_counts,
)
print(
    "KO    :",
    translated_counts,
)
print(
    "PASS"
    if count_pass
    else "FAIL"
)

print()
print("[4] GUEST ATTRIBUTION")
print(
    "PASS"
    if guest_pass
    else "FAIL"
)

print()
print("[5] PATH-AWARE NUMERIC PRESERVATION")

print(
    "SOURCE NUMERIC PATHS:",
    source_numeric_paths,
)

print(
    "KO NUMERIC PATHS    :",
    translated_numeric_paths,
)

print(
    "DIFFERENCES         :",
    len(numeric_differences),
)

print(
    "PASS"
    if numbers_pass
    else "FAIL"
)

if numeric_differences:

    print()
    print(
        "NUMERIC DIFFERENCE METADATA"
    )

    for diff in numeric_differences:

        print(
            diff["status"],
            "|",
            diff["path"],
            "| EN:",
            diff["source_tokens"],
            "| KO:",
            diff["translated_tokens"],
        )



if errors:

    print()
    print("=" * 100)
    print("RESULT: FAIL")

    for error in errors:
        print(
            " -",
            error,
        )

    print()
    print(
        "PUBLIC OUTPUT NOT WRITTEN"
    )
    print(
        "PRIVATE CANDIDATE PRESERVED:",
        CANDIDATE,
    )
    print("=" * 100)

    raise SystemExit(1)


serialized = (
    json.dumps(
        artifact,
        ensure_ascii=False,
        indent=2,
    )
    + "\n"
)

OUTPUT.write_text(
    serialized,
    encoding="utf-8",
)


print()
print("[6] OUTPUT")
print(
    OUTPUT
)

print()
print("=" * 100)
print("RESULT: PASS")
print(
    "Korean presentation artifact created."
)
print(
    "Canonical English research was not modified."
)
print("=" * 100)
