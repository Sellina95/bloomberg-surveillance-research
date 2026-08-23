from __future__ import annotations

import re
from pathlib import Path


PATH = Path(
    "data/reference/youtube/2026-08-14_transcript.txt"
)

if not PATH.exists():
    print("=" * 100)
    print("YOUTUBE TRANSCRIPT INPUT")
    print("=" * 100)
    print()
    print("FILE NOT FOUND:")
    print(PATH)
    print()
    print("YouTube Transcript panel에서 전체 transcript를 복사해서")
    print("위 경로의 txt 파일로 저장한 뒤 다시 실행하세요.")
    raise SystemExit(0)


text = PATH.read_text(
    encoding="utf-8"
)

lines = [
    line.strip()
    for line in text.splitlines()
    if line.strip()
]


timestamp_pattern = re.compile(
    r"^(?:(\d+):)?(\d{1,2}):(\d{2})$"
)

timestamps = []

for index, line in enumerate(lines):

    match = timestamp_pattern.match(line)

    if not match:
        continue

    groups = match.groups()

    if groups[0] is not None:
        seconds = (
            int(groups[0]) * 3600
            + int(groups[1]) * 60
            + int(groups[2])
        )
    else:
        seconds = (
            int(groups[1]) * 60
            + int(groups[2])
        )

    following = lines[index + 1:index + 3]

    timestamps.append(
        {
            "line": index,
            "seconds": seconds,
            "following": following,
        }
    )


print("=" * 100)
print("YOUTUBE TRANSCRIPT STRUCTURE PROBE")
print("=" * 100)

print("FILE:", PATH)
print("TOTAL LINES:", len(lines))
print("TIMESTAMP ENTRIES:", len(timestamps))

print("=" * 100)
print("FIRST 20 TIMESTAMP ENTRIES")
print("=" * 100)

for row in timestamps[:20]:

    print()
    print(
        f"{row['seconds']:7.1f}s | "
        f"LINE {row['line']}"
    )

    for text in row["following"]:
        print("  ", text[:250])


print()
print("=" * 100)
print("TRANSCRIPT STRUCTURE CHECK")
print("=" * 100)

if timestamps:
    print("TIMESTAMPS FOUND: PASS")
else:
    print("TIMESTAMPS FOUND: FAIL")

print("=" * 100)
