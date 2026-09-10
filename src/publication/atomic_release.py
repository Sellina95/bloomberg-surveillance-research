from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Callable


PUBLIC_DATE_FILES = (
    "daily_research_report_v0_1.json",
    "daily_research_report_v0_1.md",
    "daily_research_report_ko_v0_1.json",
    "daily_research_report_tv_v0_1.html",
    "daily_research_report_tv_ko_v0_1.html",
    "report_provenance_v0_1.json",
)


def promote_date(
    staged_root: Path,
    public_root: Path,
    report_date: str,
    validate: Callable[[], None],
) -> None:
    """Validate first, then publish one new date with a directory rename."""
    validate()
    source = staged_root / report_date
    target = public_root / report_date
    if target.exists():
        raise RuntimeError(f"refusing to replace existing publication: {target}")
    missing = [name for name in PUBLIC_DATE_FILES if not (source / name).is_file()]
    if missing:
        raise RuntimeError("staged publication incomplete: " + ", ".join(missing))
    public_root.mkdir(parents=True, exist_ok=True)
    release = Path(tempfile.mkdtemp(prefix=f".{report_date}.release-", dir=public_root))
    try:
        for name in PUBLIC_DATE_FILES:
            shutil.copy2(source / name, release / name)
        os.replace(release, target)
    except BaseException:
        shutil.rmtree(release, ignore_errors=True)
        raise


def promote_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        shutil.copy2(source, temporary)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def promote_snapshot(staged_root: Path, public_root: Path, report_date: str,
                     validate: Callable[[], None]) -> None:
    """Promote date plus refreshed historical navigation; roll back on failure.

    Only explicit public filenames are copied. The caller commits/deploys after
    this returns, so no intermediate snapshot is sent to GitHub Pages.
    """
    validate()
    historical = sorted(
        path for name in ("daily_research_report_tv_v0_1.html",
                          "daily_research_report_tv_ko_v0_1.html")
        for path in staged_root.glob(f"*/{name}")
        if path.parent.name != report_date
    )
    sources = historical + [staged_root / name for name in
                            ("publication_status_v0_1.json", "index.html")]
    backups = {}
    for source in sources:
        if not source.is_file():
            raise RuntimeError(f"missing snapshot file: {source}")
        target = public_root / source.relative_to(staged_root)
        if source in historical and not target.is_file():
            raise RuntimeError(f"unexpected historical file: {target}")
        backups[target] = target.read_bytes() if target.exists() else None
    created = False
    try:
        promote_date(staged_root, public_root, report_date, validate=lambda: None)
        created = True
        for source in sources:
            promote_file(source, public_root / source.relative_to(staged_root))
    except BaseException:
        if created:
            # This directory was created by this call, never an existing report.
            shutil.rmtree(public_root / report_date)
            for target, content in backups.items():
                if content is None:
                    target.unlink(missing_ok=True)
                else:
                    target.write_bytes(content)
        raise
