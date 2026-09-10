"""Offline regressions for structured prose, stale calendars and promotion."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
from presentation_contract_v0_1 import scalar_text, list_item_text
from refresh_historical_navigation_v0_1 import build_navigation, navigation_token
from validate_public_navigation_v0_1 import snapshot_failures, EN_JSON, KO_JSON, EN_HTML, KO_HTML
from src.publication import atomic_release as atomic


def make_snapshot(root, dates):
    records = [{"date": day, "en": {"status": "available"},
                "ko": {"status": "available"}} for day in dates]
    root.mkdir(parents=True, exist_ok=True)
    (root / "publication_status_v0_1.json").write_text(json.dumps({"dates": records}))
    (root / "index.html").write_text(f"{max(dates)}/{EN_HTML}")
    status = {row["date"]: row for row in records}
    for day in dates:
        directory = root / day
        directory.mkdir(exist_ok=True)
        for name in atomic.PUBLIC_DATE_FILES:
            (directory / name).write_text("{}")
        for lang, name in (("en", EN_HTML), ("ko", KO_HTML)):
            (directory / name).write_text(build_navigation(status, day, lang))
    return status


class PublicationUI(unittest.TestCase):
    def test_real_renderers_accept_structured_views_without_research_rewrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / "data/processed/surveillance/2026-09-09"
            directory.mkdir(parents=True)
            for language, name in (("en", EN_JSON), ("ko", KO_JSON)):
                source = (ROOT / "data/processed/surveillance/2026-09-09" / name).read_bytes()
                (directory / name).write_bytes(source)
                subprocess.run([sys.executable, str(ROOT / "scripts/render_daily_research_tv_v0_1.py")],
                               cwd=root, env={**os.environ, "SURVEILLANCE_DATE": "2026-09-09",
                                              "SURVEILLANCE_LANG": language},
                               check=True, capture_output=True)
                rendered = (directory / (EN_HTML if language == "en" else KO_HTML)).read_text()
                self.assertNotIn("&#x27;view&#x27;:", rendered)
                self.assertNotIn("evidence_basis", rendered)
                self.assertEqual((directory / name).read_bytes(), source)
            subprocess.run([sys.executable, str(ROOT / "scripts/render_daily_research_report_v0_1.py")],
                           cwd=root, env={**os.environ, "SURVEILLANCE_DATE": "2026-09-09"},
                           check=True, capture_output=True)
            self.assertNotIn("{'view':", (directory / "daily_research_report_v0_1.md").read_text())

    def test_prose_contract(self):
        for prose in ("Public paraphrase <not markup>", "공개 요약 문장"):
            self.assertEqual(list_item_text(prose), prose)
            self.assertEqual(list_item_text({"view": prose, "evidence_basis": "not displayed"}), prose)
        for bad in ({"unexpected": "body"}, {"view": []}, {"view": "ok", "raw_text": "private"}):
            with self.assertRaises(ValueError):
                list_item_text(bad)
        with self.assertRaises(ValueError):
            scalar_text({"view": "never stringify"})

    def test_old_page_must_link_new_day_and_both_languages(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            status = make_snapshot(root, ["2026-09-08", "2026-09-09"])
            self.assertEqual(snapshot_failures(root), [])
            older = root / "2026-09-08" / KO_HTML
            older.write_text(build_navigation({"2026-09-08": status["2026-09-08"]}, "2026-09-08", "ko"))
            self.assertTrue(any("stale/broken calendar" in x for x in snapshot_failures(root)))
            self.assertNotEqual(navigation_token(status), navigation_token({"2026-09-08": status["2026-09-08"]}))

    def test_bad_objects_withdrawn_dates_and_missing_ko_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_snapshot(root, ["2023-02-15", "2026-09-09"])
            self.assertTrue(any("withdrawn" in x for x in snapshot_failures(root)))
            html = root / "2026-09-09" / EN_HTML
            html.write_text(html.read_text() + "{&#x27;view&#x27;: &#x27;bad&#x27;}")
            self.assertTrue(any("serialized research" in x for x in snapshot_failures(root)))
            (root / "2026-09-09" / KO_HTML).unlink()
            self.assertTrue(any("incomplete KO" in x for x in snapshot_failures(root)))

    def test_promotes_history_not_private_and_rolls_back_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            public, staged = root / "public", root / "staged"
            make_snapshot(public, ["2026-09-08"])
            make_snapshot(staged, ["2026-09-08", "2026-09-09"])
            (staged / "2026-09-09" / "guest_transcripts.json").write_text("private fixture")
            before = {p.relative_to(public): p.read_bytes() for p in public.rglob("*") if p.is_file()}
            original = atomic.promote_file
            calls = []

            def fail_second(source, target):
                calls.append(target)
                if len(calls) == 2:
                    raise OSError("simulated disk failure")
                original(source, target)

            with patch.object(atomic, "promote_file", side_effect=fail_second):
                with self.assertRaises(OSError):
                    atomic.promote_snapshot(staged, public, "2026-09-09", validate=lambda: None)
            after = {p.relative_to(public): p.read_bytes() for p in public.rglob("*") if p.is_file()}
            self.assertEqual(before, after)
            atomic.promote_snapshot(staged, public, "2026-09-09", validate=lambda: None)
            self.assertEqual(snapshot_failures(public), [])
            self.assertFalse((public / "2026-09-09" / "guest_transcripts.json").exists())


if __name__ == "__main__":
    unittest.main()
