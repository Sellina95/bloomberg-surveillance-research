from __future__ import annotations

import json
from pathlib import Path


PATH = Path(
    "data/raw/youtube_probe/supadata_2026-08-14.json"
)

data = json.loads(
    PATH.read_text(encoding="utf-8")
)

content = data["content"]

offsets = [
    item["offset"]
    for item in content
    if "offset" in item
]

durations = [
    item.get("duration", 0)
    for item in content
]

first = min(offsets)
last_end = max(
    item["offset"] + item.get("duration", 0)
    for item in content
)

duration_seconds = last_end / 1000

print("=" * 100)
print("SUPADATA TRANSCRIPT COVERAGE VALIDATION")
print("=" * 100)

print("SEGMENTS:", len(content))
print("FIRST OFFSET:", first, "ms")
print("LAST END:", last_end, "ms")
print(
    "COVERAGE:",
    f"{duration_seconds / 3600:.2f} hours",
)
print(
    "COVERAGE:",
    f"{duration_seconds / 60:.1f} minutes",
)

print()
print("FIRST TEXT:")
print(content[0]["text"])

print()
print("LAST TEXT:")
print(content[-1]["text"])

print()
print("=" * 100)

if duration_seconds >= 2 * 3600:
    print("FULL-LENGTH COVERAGE: PASS")
else:
    print("FULL-LENGTH COVERAGE: REVIEW")

print("=" * 100)
