"""Check the actual public snapshot, not just the newest report."""
from __future__ import annotations

import json
import re
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

WITHDRAWN_DATES = {"2023-02-15"}  # Accidental daily discovery of an archive episode.
EN_JSON = "daily_research_report_v0_1.json"
KO_JSON = "daily_research_report_ko_v0_1.json"
EN_HTML = "daily_research_report_tv_v0_1.html"
KO_HTML = "daily_research_report_tv_ko_v0_1.html"


class CalendarLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and "nav-date" in attrs.get("class", "").split():
            self.links.append(attrs.get("href", "").split("?", 1)[0])


def snapshot_failures(root: Path) -> list[str]:
    failures = []
    status_path = root / "publication_status_v0_1.json"
    if not status_path.exists():
        return ["publication status missing"]
    try:
        records = json.loads(status_path.read_text(encoding="utf-8"))["dates"]
        status = {row["date"]: row for row in records}
        if len(status) != len(records):
            failures.append("duplicate status dates")
    except (ValueError, KeyError, TypeError):
        return ["invalid publication status"]
    dates = set()
    for directory in root.iterdir():
        if not directory.is_dir() or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", directory.name):
            continue
        if directory.name in WITHDRAWN_DATES:
            if any(directory.glob("daily_research_report*")):
                failures.append(f"withdrawn publication remains: {directory.name}")
        en_files = [(directory / name).is_file() for name in (EN_JSON, EN_HTML)]
        ko_files = [(directory / name).is_file() for name in (KO_JSON, KO_HTML)]
        if not any(en_files + ko_files):
            continue
        if not all(en_files):
            failures.append(f"incomplete EN publication: {directory.name}")
        if any(ko_files) and not all(ko_files):
            failures.append(f"incomplete KO publication: {directory.name}")
        dates.add(directory.name)
        record = status.get(directory.name, {})
        for language, exists in (("en", all(en_files)), ("ko", all(ko_files))):
            if (record.get(language, {}).get("status") == "available") != exists:
                failures.append(f"status/file mismatch: {directory.name} {language}")
    if set(status) != dates:
        failures.append("status dates differ from public files")
    for day in sorted(dates):
        for language, filename in (("en", EN_HTML), ("ko", KO_HTML)):
            path = root / day / filename
            if not path.exists():
                continue
            html = path.read_text(encoding="utf-8")
            parser = CalendarLinks()
            parser.feed(html)
            expected = {
                f"../{other}/{KO_HTML if language == 'ko' and (root / other / KO_HTML).exists() else EN_HTML}"
                for other in dates
            }
            if set(parser.links) != expected or len(parser.links) != len(expected):
                failures.append(f"stale/broken calendar: {day}/{filename}")
            if re.search(r"\{\s*['\"](?:view|evidence_basis)['\"]\s*:", unescape(html)):
                failures.append(f"serialized research object: {day}/{filename}")
        md = root / day / "daily_research_report_v0_1.md"
        if md.exists() and re.search(r"\{\s*['\"](?:view|evidence_basis)['\"]\s*:", md.read_text(encoding="utf-8")):
            failures.append(f"serialized research object: {day}/{md.name}")
    home = root / "index.html"
    if dates and (not home.exists() or f"{max(dates)}/{EN_HTML}" not in home.read_text(encoding="utf-8")):
        failures.append("home does not point to latest publication")
    return failures


def main():
    failures = snapshot_failures(Path(__file__).resolve().parents[1] / "data/processed/surveillance")
    if failures:
        raise SystemExit("PUBLIC NAVIGATION CONTRACT: FAIL\n" + "\n".join(failures))
    print("PUBLIC NAVIGATION CONTRACT: PASS")


if __name__ == "__main__":
    main()
