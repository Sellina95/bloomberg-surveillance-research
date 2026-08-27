from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SOURCE = (
    ROOT
    / "data"
    / "processed"
    / "surveillance"
)

OUTPUT = ROOT / "_site"

EN_TV = "daily_research_report_tv_v0_1.html"
KO_TV = "daily_research_report_tv_ko_v0_1.html"


def main() -> None:

    if not SOURCE.exists():
        raise SystemExit(
            f"FAIL — surveillance root missing: {SOURCE}"
        )

    home = SOURCE / "index.html"

    if not home.exists():
        raise SystemExit(
            f"FAIL — Research Desk Home missing: {home}"
        )

    # Build from zero every time.
    # Prevent stale public artifacts surviving a new deployment.
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)

    OUTPUT.mkdir(parents=True)

    shutil.copy2(
        home,
        OUTPUT / "index.html",
    )

    copied = []

    for date_dir in sorted(SOURCE.iterdir()):

        if not date_dir.is_dir():
            continue

        date = date_dir.name
        parts = date.split("-")

        if (
            len(parts) != 3
            or not all(part.isdigit() for part in parts)
        ):
            continue

        public_files = []

        en = date_dir / EN_TV
        ko = date_dir / KO_TV

        if en.exists():
            public_files.append(en)

        if ko.exists():
            public_files.append(ko)

        if not public_files:
            continue

        target_dir = OUTPUT / date
        target_dir.mkdir(parents=True)

        for source_file in public_files:
            target = target_dir / source_file.name

            shutil.copy2(
                source_file,
                target,
            )

            copied.append(
                target.relative_to(OUTPUT).as_posix()
            )

    if not copied:
        raise SystemExit(
            "FAIL — no public TV artifacts discovered"
        )

    # Prevent Jekyll processing.
    (OUTPUT / ".nojekyll").write_text(
        "",
        encoding="utf-8",
    )

    print("=" * 100)
    print("RESEARCH DESK PAGES v0.1")
    print("=" * 100)
    print("PUBLIC ROOT:", OUTPUT)
    print("HOME: index.html")
    print("TV ARTIFACTS:", len(copied))

    for item in copied:
        print("PUBLIC:", item)

    print("=" * 100)
    print("PUBLIC-SAFE BUILD: PASS")
    print("=" * 100)


if __name__ == "__main__":
    main()
