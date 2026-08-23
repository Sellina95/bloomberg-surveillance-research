from __future__ import annotations

import json
import os
import time
from urllib.request import Request, urlopen


VIDEO_URL = "https://www.youtube.com/watch?v=qWYTenEUdFc"
API_KEY = os.environ["SUPADATA_API_KEY"]

BASE = "https://api.supadata.ai/v1"


SCHEMA = {
    "type": "object",
    "properties": {
        "chapters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "chapter_number": {
                        "type": "integer"
                    },
                    "start_time": {
                        "type": "string"
                    },
                    "title": {
                        "type": "string"
                    },
                    "guest": {
                        "type": "string"
                    },
                },
                "required": [
                    "chapter_number",
                    "start_time",
                    "title",
                    "guest",
                ],
            },
        }
    },
    "required": ["chapters"],
}


def request_json(
    method: str,
    url: str,
    body: dict | None = None,
):
    headers = {
        "x-api-key": API_KEY,
        "Accept": "application/json",
    }

    data = None

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    request = Request(
        url,
        method=method,
        headers=headers,
        data=data,
    )

    with urlopen(request, timeout=120) as response:
        return response.status, json.loads(
            response.read().decode("utf-8")
        )


print("=" * 100)
print("SUPADATA CHAPTER EXTRACTION PROBE")
print("=" * 100)

# ------------------------------------------------------------
# 1. Create extraction job
# ------------------------------------------------------------

status, response = request_json(
    "POST",
    f"{BASE}/extract",
    {
        "url": VIDEO_URL,
        "schema": SCHEMA,
        "prompt": (
            "Extract the actual chapter structure of this YouTube "
            "video. Return the chapter number, exact chapter start "
            "timestamp, exact chapter title, and guest name if the "
            "chapter is a guest interview. Do not invent chapters. "
            "If a chapter is not a guest interview, set guest to ''."
        ),
    },
)

print("CREATE STATUS:", status)
print("CREATE RESPONSE:")
print(json.dumps(
    response,
    ensure_ascii=False,
    indent=2,
))

if "jobId" not in response:
    raise SystemExit(
        "FAIL — no extraction job ID"
    )

job_id = response["jobId"]

print()
print("JOB ID:", job_id)

# ------------------------------------------------------------
# 2. Poll result
# ------------------------------------------------------------

print()
print("-" * 100)
print("POLLING")
print("-" * 100)

for attempt in range(120):

    status, result = request_json(
        "GET",
        f"{BASE}/extract/{job_id}",
    )

    job_status = result.get("status")

    print(
        f"ATTEMPT {attempt + 1:03d} | "
        f"HTTP={status} | "
        f"STATUS={job_status}"
    )

    if job_status == "completed":

        print()
        print("=" * 100)
        print("EXTRACTION RESULT")
        print("=" * 100)

        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
            )
        )

        Path = __import__("pathlib").Path

        output = Path(
            "data/raw/youtube_probe/"
            "supadata_chapters_2026-08-14.json"
        )

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output.write_text(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        print()
        print("OUTPUT:", output)
        print()
        print("CHAPTER EXTRACTION: PASS")
        raise SystemExit(0)

    if job_status == "failed":

        print()
        print("EXTRACTION FAILED")
        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
            )
        )

        raise SystemExit(1)

    time.sleep(2)

raise SystemExit(
    "FAIL — extraction did not complete within timeout"
)
