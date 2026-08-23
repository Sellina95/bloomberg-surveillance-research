from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


VIDEO_URL = "https://www.youtube.com/watch?v=qWYTenEUdFc"

OUT = Path("data/raw/youtube_probe")
OUT.mkdir(parents=True, exist_ok=True)

API_KEY = os.getenv("SUPADATA_API_KEY")

if not API_KEY:
    raise SystemExit(
        "FAIL — SUPADATA_API_KEY environment variable is not set"
    )


# Supadata YouTube transcript endpoint
URL = (
    "https://api.supadata.ai/v1/transcript"
    "?url="
    + VIDEO_URL
)


request = Request(
    URL,
    headers={
        "x-api-key": API_KEY,
        "Accept": "application/json",
    },
)


print("=" * 100)
print("SUPADATA YOUTUBE TRANSCRIPT PROBE")
print("=" * 100)
print("VIDEO:", VIDEO_URL)
print()


try:
    with urlopen(request, timeout=60) as response:
        status = response.status
        raw = response.read().decode("utf-8")

except HTTPError as exc:
    print("HTTP STATUS:", exc.code)
    print(exc.read().decode("utf-8", errors="replace")[:3000])
    raise SystemExit("SUPADATA PROBE: FAIL")

except URLError as exc:
    print("NETWORK ERROR:", exc)
    raise SystemExit("SUPADATA PROBE: FAIL")


print("HTTP STATUS:", status)

try:
    payload = json.loads(raw)
except json.JSONDecodeError:
    print(raw[:3000])
    raise SystemExit(
        "SUPADATA PROBE: FAIL — response is not JSON"
    )


raw_path = OUT / "supadata_2026-08-14.json"

raw_path.write_text(
    json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)


print("RAW ARTIFACT:", raw_path)
print()


# ------------------------------------------------------------
# Inspect response shape without assuming exact schema
# ------------------------------------------------------------

print("=" * 100)
print("RESPONSE STRUCTURE")
print("=" * 100)

if isinstance(payload, dict):

    print(
        "TOP-LEVEL KEYS:",
        list(payload.keys()),
    )

    for key, value in payload.items():

        if isinstance(value, list):
            print(
                f"{key}: LIST "
                f"({len(value)} items)"
            )

        elif isinstance(value, dict):
            print(
                f"{key}: DICT "
                f"({len(value)} keys)"
            )

        else:
            print(
                f"{key}: {type(value).__name__}"
            )

elif isinstance(payload, list):

    print(
        "TOP LEVEL: LIST",
        len(payload),
    )

else:

    print(
        "TOP LEVEL:",
        type(payload).__name__,
    )


# ------------------------------------------------------------
# Locate transcript-like content
# ------------------------------------------------------------

print()
print("=" * 100)
print("TRANSCRIPT CONTENT INSPECTION")
print("=" * 100)


def inspect(value, path="root"):

    if isinstance(value, list):

        for i, item in enumerate(value[:5]):
            inspect(
                item,
                f"{path}[{i}]",
            )

    elif isinstance(value, dict):

        for key, item in value.items():

            key_lower = key.lower()

            if any(
                token in key_lower
                for token in (
                    "text",
                    "transcript",
                    "content",
                    "segments",
                    "utterances",
                )
            ):

                if isinstance(item, list):
                    print(
                        f"{path}.{key}: "
                        f"LIST[{len(item)}]"
                    )

                    for sample in item[:3]:
                        print(
                            "  ",
                            str(sample)[:500],
                        )

                elif isinstance(item, str):

                    print(
                        f"{path}.{key}: "
                        f"{item[:500]}"
                    )

            elif isinstance(item, (dict, list)):

                inspect(
                    item,
                    f"{path}.{key}",
                )


inspect(payload)


print()
print("=" * 100)
print("SUPADATA PROBE COMPLETE")
print("=" * 100)
