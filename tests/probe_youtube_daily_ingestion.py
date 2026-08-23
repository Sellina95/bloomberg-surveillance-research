from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


VIDEO_URL = "https://www.youtube.com/watch?v=qWYTenEUdFc"

OUT = Path("data/raw/youtube_probe")
OUT.mkdir(parents=True, exist_ok=True)

print("=" * 100)
print("YOUTUBE DAILY INGESTION PROBE")
print("=" * 100)
print("VIDEO:", VIDEO_URL)
print()

# ------------------------------------------------------------
# A. Metadata / chapters availability
# ------------------------------------------------------------

metadata_cmd = [
    "yt-dlp",
    "--dump-single-json",
    "--skip-download",
    "--no-warnings",
    VIDEO_URL,
]

metadata = subprocess.run(
    metadata_cmd,
    capture_output=True,
    text=True,
)

if metadata.returncode != 0:
    print("METADATA: FAIL")
    print(metadata.stderr[-2000:])
    print()
    print("INGESTION GATE: FAIL")
    sys.exit(1)

try:
    info = json.loads(metadata.stdout)
except json.JSONDecodeError:
    print("METADATA: FAIL — invalid JSON")
    sys.exit(1)

print("METADATA: PASS")

print(
    "TITLE:",
    info.get("title"),
)

print(
    "VIDEO ID:",
    info.get("id"),
)

print(
    "DURATION:",
    info.get("duration"),
)

chapters = info.get("chapters") or []

print(
    "CHAPTERS:",
    len(chapters),
)

# ------------------------------------------------------------
# B. Subtitle discovery
# ------------------------------------------------------------

print()
print("-" * 100)
print("SUBTITLE DISCOVERY")
print("-" * 100)

subtitle_cmd = [
    "yt-dlp",
    "--list-subs",
    "--no-warnings",
    VIDEO_URL,
]

subs = subprocess.run(
    subtitle_cmd,
    capture_output=True,
    text=True,
)

if subs.returncode != 0:
    print("SUBTITLE DISCOVERY: FAIL")
    print(subs.stderr[-2000:])
    print()
    print("INGESTION GATE: FAIL")
    sys.exit(1)

print("SUBTITLE DISCOVERY: PASS")

print(
    subs.stdout[-5000:]
)

# ------------------------------------------------------------
# C. Actual auto-caption download
# ------------------------------------------------------------

print()
print("-" * 100)
print("AUTO-CAPTION DOWNLOAD")
print("-" * 100)

download_cmd = [
    "yt-dlp",
    "--skip-download",
    "--write-auto-subs",
    "--sub-langs",
    "en",
    "--sub-format",
    "vtt",
    "-o",
    str(OUT / "%(id)s.%(ext)s"),
    VIDEO_URL,
]

download = subprocess.run(
    download_cmd,
    capture_output=True,
    text=True,
)

if download.returncode != 0:
    print("AUTO-CAPTION DOWNLOAD: FAIL")
    print(download.stderr[-3000:])
    print()
    print("INGESTION GATE: FAIL")
    sys.exit(1)

print("AUTO-CAPTION DOWNLOAD: PASS")

files = list(OUT.glob("*"))

print(
    "FILES:",
    [str(x) for x in files],
)

if not files:
    print("INGESTION GATE: FAIL — no caption artifact")
    sys.exit(1)

print()
print("=" * 100)
print("INGESTION GATE: PASS")
print("=" * 100)
