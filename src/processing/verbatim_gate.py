from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any, Iterable


TOKEN_RE = re.compile(r"[a-z0-9]+(?:['’-][a-z0-9]+)?", re.I)


def strings(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for child in value.values():
            yield from strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from strings(child)
    elif isinstance(value, str):
        yield value


def tokens(text: str) -> list[str]:
    return [match.group(0).casefold().replace("’", "'") for match in TOKEN_RE.finditer(text)]


def exposure_failures(
    public_values: Iterable[str],
    private_values: Iterable[str],
    *,
    exact_words: int = 10,
    fuzzy_min_words: int = 14,
    fuzzy_ratio: float = 0.86,
) -> list[str]:
    source_rows = [tokens(value) for value in private_values]
    source_rows = [row for row in source_rows if len(row) >= exact_words]
    source_shingles = {
        tuple(row[i:i + exact_words])
        for row in source_rows
        for i in range(len(row) - exact_words + 1)
    }
    failures: list[str] = []
    for index, value in enumerate(public_values):
        row = tokens(value)
        if len(row) < exact_words:
            continue
        if any(
            tuple(row[i:i + exact_words]) in source_shingles
            for i in range(len(row) - exact_words + 1)
        ):
            failures.append(f"public string {index}: exact {exact_words}-word source overlap")
            continue
        if len(row) < fuzzy_min_words:
            continue
        for source in source_rows:
            if len(source) < fuzzy_min_words:
                continue
            ratio = SequenceMatcher(None, row, source, autojunk=False).ratio()
            if ratio >= fuzzy_ratio:
                failures.append(
                    f"public string {index}: near-verbatim similarity {ratio:.3f}"
                )
                break
    return failures
