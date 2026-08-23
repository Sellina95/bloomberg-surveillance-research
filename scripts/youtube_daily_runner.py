from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


SERPAPI_ENDPOINT = "https://serpapi.com/search.json"
SUPADATA_ENDPOINT = "https://api.supadata.ai/v1/youtube/transcript"


def fetch_serpapi_chapters(video_id, api_key):
    params = {
        "engine": "youtube_video",
        "v": video_id,
        "api_key": api_key,
    }

    request = Request(
        SERPAPI_ENDPOINT + "?" + urlencode(params),
        headers={"Accept": "application/json"},
    )

    with urlopen(request, timeout=120) as response:
        data = json.loads(
            response.read().decode("utf-8")
        )

    chapters = data.get("chapters", [])

    if not chapters:
        raise RuntimeError(
            "SerpApi returned no chapters"
        )

    return [
        {
            "chapter": i + 1,
            "title": c["title"],
            "start_seconds": float(c["time_start"]),
            "source": "serpapi",
        }
        for i, c in enumerate(chapters)
    ]


def fetch_supadata_transcript(video_url, api_key):
    url = (
        SUPADATA_ENDPOINT
        + "?"
        + urlencode({"url": video_url})
    )

    request = Request(
        url,
        headers={
            "x-api-key": api_key,
            "Accept": "application/json",
        },
    )

    with urlopen(request, timeout=120) as response:
        data = json.loads(
            response.read().decode("utf-8")
        )

    content = data.get("content", [])

    if not content:
        raise RuntimeError(
            "Supadata returned empty transcript"
        )

    return [
        {
            "segment_id": i,
            "start_seconds": item["offset"] / 1000,
            "end_seconds": (
                item["offset"] + item.get("duration", 0)
            ) / 1000,
            "text": item["text"],
            "lang": item.get("lang"),
            "source": "supadata",
        }
        for i, item in enumerate(content)
    ]


GUEST_RE = re.compile(
    r"^.+\s+[—-]\s+"
    r"([^—-]+)"
)


def is_guest_chapter(title):
    match = GUEST_RE.match(title.strip())

    if not match:
        return False

    words = match.group(1).strip().split()

    return len(words) >= 2


def run(date, video_id):

    serp_key = os.environ["SERPAPI_API_KEY"]
    supa_key = os.environ["SUPADATA_API_KEY"]

    video_url = (
        "https://www.youtube.com/watch?v="
        + video_id
    )

    print("=" * 100)
    print("YOUTUBE DAILY RUNNER")
    print("=" * 100)
    print("DATE:", date)
    print("VIDEO:", video_url)
    print()

    chapters = fetch_serpapi_chapters(
        video_id,
        serp_key,
    )

    print(
        "CHAPTERS:",
        len(chapters),
    )

    segments = fetch_supadata_transcript(
        video_url,
        supa_key,
    )

    print(
        "TRANSCRIPT SEGMENTS:",
        len(segments),
    )

    video_end = max(
        s["end_seconds"]
        for s in segments
    )

    for i, chapter in enumerate(chapters):

        start = chapter["start_seconds"]

        end = (
            chapters[i + 1]["start_seconds"]
            if i + 1 < len(chapters)
            else video_end
        )

        for segment in segments:

            if (
                start
                <= segment["start_seconds"]
                < end
            ):
                segment["chapter"] = chapter["chapter"]

    guest_chapters = []

    for chapter in chapters:

        chapter["is_guest"] = is_guest_chapter(
            chapter["title"]
        )

        if chapter["is_guest"]:
            guest_chapters.append(chapter)

    units = []

    for unit_id, chapter in enumerate(
        guest_chapters,
        start=1,
    ):

        index = chapters.index(chapter)

        start = chapter["start_seconds"]

        end = (
            chapters[index + 1]["start_seconds"]
            if index + 1 < len(chapters)
            else video_end
        )

        rows = [
            s
            for s in segments
            if (
                start
                <= s["start_seconds"]
                < end
            )
        ]

        units.append(
            {
                "unit_id": unit_id,
                "chapter": chapter["chapter"],
                "title": chapter["title"],
                "start_seconds": start,
                "end_seconds": end,
                "segment_count": len(rows),
            }
        )

    coverage = (
        video_end
        - min(s["start_seconds"] for s in segments)
    ) / 60

    output = Path(
        "data/processed/surveillance"
    ) / date

    output.mkdir(
        parents=True,
        exist_ok=True,
    )

    canonical = {
        "date": date,
        "video_id": video_id,
        "chapter_count": len(chapters),
        "transcript_segment_count": len(segments),
        "coverage_minutes": coverage,
        "chapters": chapters,
        "segments": segments,
    }

    (output / "youtube_canonical.json").write_text(
        json.dumps(
            canonical,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    (output / "guest_units.json").write_text(
        json.dumps(
            {
                "date": date,
                "video_id": video_id,
                "guest_count": len(units),
                "guest_units": units,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 100)
    print("RESULT")
    print("=" * 100)
    print("CHAPTERS:", len(chapters))
    print("TRANSCRIPT:", len(segments))
    print(f"COVERAGE: {coverage:.1f} minutes")
    print("GUEST COUNT:", len(units))

    if (
        len(chapters) > 0
        and len(segments) > 0
        and coverage > 120
        and len(units) > 0
    ):
        print("DAILY PIPELINE: PASS")
    else:
        print("DAILY PIPELINE: REVIEW")

    print("=" * 100)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--date",
        required=True,
    )

    parser.add_argument(
        "--video-id",
        required=True,
    )

    args = parser.parse_args()

    run(
        args.date,
        args.video_id,
    )
