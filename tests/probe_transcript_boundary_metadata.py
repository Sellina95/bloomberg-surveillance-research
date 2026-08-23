from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DATES = [
    "2026-08-13",
    "2026-08-14",
]

RAW_ROOT = Path("data/raw/surveillance")


def describe(
    value: Any,
    indent: str = "",
    depth: int = 0,
    max_depth: int = 3,
) -> None:
    if depth > max_depth:
        return

    if isinstance(value, dict):
        for key, child in value.items():
            child_type = type(child).__name__

            if isinstance(child, (list, dict)):
                size = len(child)
                print(
                    f"{indent}{key}: "
                    f"{child_type} ({size})"
                )
                describe(
                    child,
                    indent + "  ",
                    depth + 1,
                    max_depth,
                )
            else:
                preview = repr(child)

                if len(preview) > 120:
                    preview = preview[:117] + "..."

                print(
                    f"{indent}{key}: "
                    f"{child_type} = {preview}"
                )

    elif isinstance(value, list):
        # Only inspect the structure of the first few items.
        for index, child in enumerate(value[:3]):
            print(
                f"{indent}[{index}]: "
                f"{type(child).__name__}"
            )
            describe(
                child,
                indent + "  ",
                depth + 1,
                max_depth,
            )


BOUNDARY_TERMS = (
    "chapter",
    "marker",
    "section",
    "topic",
    "title",
    "cue",
    "break",
    "speaker",
    "segment",
)


for date in DATES:
    path = (
        RAW_ROOT
        / date
        / "transcript.json"
    )

    payload = json.loads(
        path.read_text(encoding="utf-8")
    )

    print("=" * 80)
    print("DATE:", date)

    print()
    print("TOP-LEVEL KEYS")
    print("-" * 80)

    for key, value in payload.items():
        if isinstance(value, (list, dict)):
            print(
                f"{key}: "
                f"{type(value).__name__} "
                f"({len(value)})"
            )
        else:
            print(
                f"{key}: "
                f"{type(value).__name__}"
            )

    print()
    print("POSSIBLE BOUNDARY-RELATED KEYS")
    print("-" * 80)

    matches: list[str] = []

    def search_keys(
        value: Any,
        path_parts: list[str],
        depth: int = 0,
    ) -> None:
        if depth > 5:
            return

        if isinstance(value, dict):
            for key, child in value.items():
                lower = key.lower()

                if any(
                    term in lower
                    for term in BOUNDARY_TERMS
                ):
                    matches.append(
                        ".".join(
                            path_parts + [key]
                        )
                    )

                search_keys(
                    child,
                    path_parts + [key],
                    depth + 1,
                )

        elif isinstance(value, list):
            # Structure should repeat, so inspect only
            # the first few elements.
            for index, child in enumerate(value[:5]):
                search_keys(
                    child,
                    path_parts + [f"[{index}]"],
                    depth + 1,
                )

    search_keys(payload, [])

    unique_matches = list(
        dict.fromkeys(matches)
    )

    if unique_matches:
        for match in unique_matches:
            print(match)
    else:
        print("NONE")

    print()
    print("STRUCTURE PREVIEW")
    print("-" * 80)

    describe(
        payload,
        max_depth=2,
    )

print("=" * 80)
