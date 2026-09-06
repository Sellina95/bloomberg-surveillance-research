from __future__ import annotations

import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.publication.atomic_release import PUBLIC_DATE_FILES, promote_date


with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    staged = root / "staged"
    public = root / "public"
    source = staged / "2099-01-03"
    source.mkdir(parents=True)
    for name in PUBLIC_DATE_FILES:
        (source / name).write_text("candidate", encoding="utf-8")

    try:
        promote_date(
            staged, public, "2099-01-03",
            validate=lambda: (_ for _ in ()).throw(RuntimeError("gate failure")),
        )
    except RuntimeError:
        pass
    else:
        raise AssertionError("validation failure must stop promotion")
    assert not (public / "2099-01-03").exists()

    promote_date(staged, public, "2099-01-03", validate=lambda: None)
    assert all((public / "2099-01-03" / name).exists() for name in PUBLIC_DATE_FILES)

print("ATOMIC PUBLICATION CONTRACT: PASS")
