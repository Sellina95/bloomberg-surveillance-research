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
