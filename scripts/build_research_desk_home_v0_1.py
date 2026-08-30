from __future__ import annotations

from html import escape
from pathlib import Path


ROOT = Path(
    "data/processed/surveillance"
)

TV_FILENAME = (
    "daily_research_report_tv_v0_1.html"
)

OUTPUT = ROOT / "index.html"

CACHE_TOKEN = "desk=v0_1"


def valid_date_dir(path: Path) -> bool:
    if not path.is_dir():
        return False

    parts = path.name.split("-")

    return (
        len(parts) == 3
        and all(
            part.isdigit()
            for part in parts
        )
    )


def discover_latest_public_tv():
    candidates = []

    if not ROOT.exists():
        raise SystemExit(
            f"FAIL — surveillance root missing: {ROOT}"
        )

    for date_dir in ROOT.iterdir():

        if not valid_date_dir(date_dir):
            continue

        tv = date_dir / TV_FILENAME

        if tv.exists():
            candidates.append(
                (
                    date_dir.name,
                    tv,
                )
            )

    if not candidates:
        raise SystemExit(
            "FAIL — no public EN TV artifacts found"
        )

    return sorted(
        candidates,
        key=lambda item: item[0],
    )[-1]


latest_date, latest_tv = (
    discover_latest_public_tv()
)

target = (
    f"{latest_date}/"
    f"{TV_FILENAME}"
    f"?{CACHE_TOKEN}"
)

target_html = escape(
    target,
    quote=True,
)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">

<meta name="robots" content="noindex, nofollow">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >
    <meta
        http-equiv="refresh"
        content="0; url={target_html}"
    >
    <title>Independent Market Research Desk</title>
</head>
<body>
    <main>
        <p>
            Opening latest Research Desk:
            <a href="{target_html}">
                {escape(latest_date)}
            </a>
        </p>
    </main>

    <script>
        window.location.replace(
            {target!r}
        );
    </script>
</body>
</html>
"""

OUTPUT.write_text(
    html,
    encoding="utf-8",
)

print(
    "=" * 100
)

print(
    "RESEARCH DESK HOME v0.1"
)

print(
    "=" * 100
)

print(
    "LATEST PUBLIC EN TV:",
    latest_date,
)

print(
    "TARGET:",
    target,
)

print(
    "OUTPUT:",
    OUTPUT,
)

print(
    "=" * 100
)

print(
    "HOME BUILD: PASS"
)

print(
    "=" * 100
)
