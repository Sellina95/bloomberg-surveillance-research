from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SURVEILLANCE = ROOT / "data" / "processed" / "surveillance"

# ---------------------------------------------------------------------------
# Public Release Gate v0.1
# ---------------------------------------------------------------------------

PRIVATE_BASENAMES = {
    "guest_transcripts.json",
    "guest_units_v0_3.json",
    "youtube_canonical_v0_2.json",
    "research_dataset_v0_1.json",
    "research_summaries_gemini_v0_2.json",
}

PRIVATE_NAME_PATTERNS = (
    re.compile(r".*_transcript\.txt$", re.I),
)

OLD_PUBLIC_BRANDING = (
    "BLOOMBERG SURVEILLANCE · RESEARCH DESK",
    "Bloomberg Surveillance Research Engine",
)

EN_DIRECTIVE = re.compile(
    r"\b("
    r"buy|sell|accumulate|reduce|overweight|underweight|"
    r"enter|exit|go long|go short|scale into"
    r")\b",
    re.I,
)

KO_DIRECTIVE = re.compile(
    r"매수|매도|분할\s*매수|비중\s*확대|비중\s*축소|"
    r"오버웨이트|언더웨이트|축적하|진입하|"
    r"롱\s*포지션을\s*유지|선호하십시오"
)

failures: list[str] = []


def fail(message: str) -> None:
    failures.append(message)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"INVALID JSON: {path.relative_to(ROOT)} — {exc}")
        return None


def contains_key(obj: Any, target: str) -> bool:
    if isinstance(obj, dict):
        if target in obj:
            return True
        return any(contains_key(v, target) for v in obj.values())
    if isinstance(obj, list):
        return any(contains_key(v, target) for v in obj)
    return False


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    return [
        ROOT / line
        for line in result.stdout.splitlines()
        if line.strip()
    ]


# ===========================================================================
# GATE 1 — PRIVATE ARTIFACTS MUST NEVER BE TRACKED
# ===========================================================================

tracked = tracked_files()

for path in tracked:
    if path.name in PRIVATE_BASENAMES:
        fail(f"TRACKED PRIVATE ARTIFACT: {path.relative_to(ROOT)}")

    for pattern in PRIVATE_NAME_PATTERNS:
        if pattern.fullmatch(path.name):
            fail(f"TRACKED PRIVATE TRANSCRIPT: {path.relative_to(ROOT)}")


# ===========================================================================
# GATE 2 — PUBLIC DAILY JSON MUST NOT SERIALIZE EVIDENCE
# ===========================================================================

if not SURVEILLANCE.exists():
    fail("SURVEILLANCE DIRECTORY MISSING")

en_jsons = sorted(SURVEILLANCE.glob("*/daily_research_report_v0_1.json"))
ko_jsons = sorted(SURVEILLANCE.glob("*/daily_research_report_ko_v0_1.json"))

if not en_jsons:
    fail("NO PUBLIC EN DAILY REPORTS FOUND")

for path in en_jsons + ko_jsons:
    obj = load_json(path)

    if obj is None:
        continue

    if contains_key(obj, "evidence"):
        fail(f"PUBLIC EVIDENCE KEY: {path.relative_to(ROOT)}")

    if contains_key(obj, "transcript_text"):
        fail(f"PUBLIC TRANSCRIPT BODY: {path.relative_to(ROOT)}")


# ===========================================================================
# GATE 3 — PUBLIC MARKDOWN / HTML MUST NOT EXPOSE EVIDENCE UI
# ===========================================================================

public_rendered = (
    sorted(SURVEILLANCE.glob("*/daily_research_report_v0_1.md"))
    + sorted(SURVEILLANCE.glob("*/daily_research_report_tv_v0_1.html"))
    + sorted(SURVEILLANCE.glob("*/daily_research_report_tv_ko_v0_1.html"))
)

for path in public_rendered:
    text = path.read_text(encoding="utf-8", errors="replace")

    if "**Evidence**" in text:
        fail(f"PUBLIC EVIDENCE SECTION: {path.relative_to(ROOT)}")

    if "transcript_text" in text:
        fail(f"PUBLIC TRANSCRIPT FIELD: {path.relative_to(ROOT)}")


# ===========================================================================
# GATE 4 — BRANDING / NON-AFFILIATION / DOCUMENT IDENTITY / INDEXING
# ===========================================================================

htmls = (
    sorted(SURVEILLANCE.glob("*/daily_research_report_tv_v0_1.html"))
    + sorted(SURVEILLANCE.glob("*/daily_research_report_tv_ko_v0_1.html"))
)

public_htmls = [SURVEILLANCE / "index.html"] + htmls

DISCLAIMER_RE = re.compile(
    r"not\s+affiliated\s+with\s+or\s+endorsed\s+by\s+Bloomberg",
    re.I,
)

TITLE_RE = re.compile(
    r"<title>\s*(.*?)\s*</title>",
    re.I | re.S,
)

NOINDEX_TAG = '<meta name="robots" content="noindex, nofollow">'

for path in public_htmls:
    if not path.exists():
        fail(f"MISSING PUBLIC HTML: {path.relative_to(ROOT)}")
        continue

    text = path.read_text(encoding="utf-8", errors="replace")

    title = TITLE_RE.search(text)

    if not title:
        fail(f"MISSING HTML TITLE: {path.relative_to(ROOT)}")
    elif "bloomberg" in title.group(1).lower():
        fail(f"BLOOMBERG PRIMARY TITLE: {path.relative_to(ROOT)}")

    if NOINDEX_TAG not in text:
        fail(f"MISSING NOINDEX: {path.relative_to(ROOT)}")

for path in htmls:
    text = path.read_text(encoding="utf-8", errors="replace")

    for old in OLD_PUBLIC_BRANDING:
        if old in text:
            fail(f"OLD PUBLIC BRANDING: {path.relative_to(ROOT)}")

    if not DISCLAIMER_RE.search(text):
        fail(f"MISSING NON-AFFILIATION DISCLAIMER: {path.relative_to(ROOT)}")


# ===========================================================================
# GATE 5 — SOURCE SYNTHESIS / SYSTEM INTERPRETATION BOUNDARY
# ===========================================================================

for path in public_rendered:
    text = path.read_text(encoding="utf-8", errors="replace")

    if "SOURCE-DERIVED SYNTHESIS" not in text:
        fail(f"MISSING SOURCE LABEL: {path.relative_to(ROOT)}")

    if "SYSTEM RESEARCH INTERPRETATION" not in text:
        fail(f"MISSING SYSTEM LABEL: {path.relative_to(ROOT)}")


# ===========================================================================
# GATE 6 — SYSTEM-GENERATED MONITORING IMPLICATIONS MUST BE NON-PRESCRIPTIVE
# ===========================================================================

for path in en_jsons:
    obj = load_json(path)

    if not isinstance(obj, dict):
        continue

    for idx, row in enumerate(obj.get("daily_action", []), start=1):
        if not isinstance(row, dict):
            continue

        for field in ("action", "why", "what_to_monitor"):
            value = str(row.get(field, ""))

            if EN_DIRECTIVE.search(value):
                fail(
                    f"EN SYSTEM DIRECTIVE: "
                    f"{path.parent.name} daily_action[{idx}].{field}"
                )


for path in ko_jsons:
    obj = load_json(path)

    if not isinstance(obj, dict):
        continue

    report = obj.get("report", obj)

    if not isinstance(report, dict):
        continue

    for idx, row in enumerate(report.get("daily_action", []), start=1):
        if not isinstance(row, dict):
            continue

        for field in ("action", "why", "what_to_monitor"):
            value = str(row.get(field, ""))

            if KO_DIRECTIVE.search(value):
                fail(
                    f"KO SYSTEM DIRECTIVE: "
                    f"{path.parent.name} daily_action[{idx}].{field}"
                )


# ===========================================================================
# GATE 6B — RESEARCH TAKEAWAYS MUST ALSO BE NON-PRESCRIPTIVE
# ===========================================================================

for path in en_jsons:
    obj = load_json(path)

    if not isinstance(obj, dict):
        continue

    for idx, value in enumerate(obj.get("research_takeaways", []), start=1):
        text = str(value)

        if EN_DIRECTIVE.search(text):
            fail(
                f"EN RESEARCH TAKEAWAY DIRECTIVE: "
                f"{path.parent.name} research_takeaways[{idx}]"
            )


for path in ko_jsons:
    obj = load_json(path)

    if not isinstance(obj, dict):
        continue

    report = obj.get("report", obj)

    if not isinstance(report, dict):
        continue

    for idx, value in enumerate(report.get("research_takeaways", []), start=1):
        text = str(value)

        if KO_DIRECTIVE.search(text):
            fail(
                f"KO RESEARCH TAKEAWAY DIRECTIVE: "
                f"{path.parent.name} research_takeaways[{idx}]"
            )


# ===========================================================================
# GATE 7 — PUBLIC LABEL CONTRACT
# ===========================================================================

for path in public_rendered:
    text = path.read_text(encoding="utf-8", errors="replace")

    if re.search(r"\bDAILY ACTION\b", text, re.I):
        fail(f"LEGACY DAILY ACTION LABEL: {path.relative_to(ROOT)}")


# ===========================================================================
# RESULT
# ===========================================================================

print("=" * 78)
print("PUBLIC SURFACE GATE v0.1")
print("=" * 78)
print(f"EN REPORTS : {len(en_jsons)}")
print(f"KO REPORTS : {len(ko_jsons)}")
print(f"HTML FILES : {len(htmls)}")
print(f"FAILURES   : {len(failures)}")

if failures:
    print("-" * 78)

    for item in failures:
        print("FAIL |", item)

    print("=" * 78)
    print("PUBLIC SURFACE GATE v0.1: FAIL")
    sys.exit(1)

print("=" * 78)
print("PUBLIC SURFACE GATE v0.1: PASS")
