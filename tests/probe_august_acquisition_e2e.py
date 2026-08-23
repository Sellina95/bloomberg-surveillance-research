from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import requests


RSS_URL = (
    "https://omny.fm/shows/"
    "bloomberg-surveillance/playlists/podcast.rss"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
}

WINDOW_START = datetime(2026, 8, 1, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 8, 22, tzinfo=timezone.utc)


def clean(value: str | None) -> str:
    return (value or "").strip()


def discover_episodes() -> list[dict[str, Any]]:
    response = requests.get(
        RSS_URL,
        headers=HEADERS,
        timeout=60,
    )
    response.raise_for_status()

    root = ET.fromstring(response.content)
    episodes = []

    for item in root.findall("./channel/item"):
        title = clean(item.findtext("title"))
        pub_raw = clean(item.findtext("pubDate"))
        link = clean(item.findtext("link"))
        guid = clean(item.findtext("guid"))

        if not pub_raw or not link:
            continue

        try:
            pub_date = parsedate_to_datetime(pub_raw)

            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(
                    tzinfo=timezone.utc
                )

            pub_date = pub_date.astimezone(timezone.utc)

        except (TypeError, ValueError):
            continue

        if not (
            WINDOW_START <= pub_date < WINDOW_END
        ):
            continue

        if not title.lower().startswith(
            "bloomberg surveillance tv"
        ):
            continue

        episodes.append(
            {
                "date": pub_date.date().isoformat(),
                "title": title,
                "link": link,
                "guid": guid,
            }
        )

    return sorted(
        episodes,
        key=lambda x: x["date"],
    )


def extract_transcript_metadata(
    html: str,
) -> tuple[str | None, bool | None]:

    url_match = re.search(
        r'"TranscriptUrl":"([^"]+)"',
        html,
    )

    published_match = re.search(
        r'"HasPublishedTranscript":(true|false)',
        html,
        flags=re.IGNORECASE,
    )

    transcript_url = (
        url_match.group(1)
        if url_match
        else None
    )

    published = (
        published_match.group(1).lower() == "true"
        if published_match
        else None
    )

    return transcript_url, published


def validate_episode(
    episode: dict[str, Any],
) -> dict[str, Any]:

    result = {
        **episode,
        "episode_http": None,
        "published": None,
        "transcript_url": False,
        "transcript_http": None,
        "speakers": 0,
        "segments": 0,
        "words": 0,
        "timestamps": False,
        "status": "FAIL",
        "error": None,
    }

    try:
        page = requests.get(
            episode["link"],
            headers=HEADERS,
            timeout=30,
        )

        result["episode_http"] = page.status_code

        if page.status_code != 200:
            return result

        transcript_url, published = (
            extract_transcript_metadata(page.text)
        )

        result["published"] = published
        result["transcript_url"] = (
            transcript_url is not None
        )

        if not transcript_url:
            return result

        transcript = requests.get(
            transcript_url,
            headers=HEADERS,
            timeout=30,
        )

        result["transcript_http"] = (
            transcript.status_code
        )

        if transcript.status_code != 200:
            return result

        payload = transcript.json()

        speakers = payload.get("speakers", [])
        segments = payload.get("segments", [])

        words = [
            word
            for segment in segments
            for word in segment.get("words", [])
        ]

        result["speakers"] = len(speakers)
        result["segments"] = len(segments)
        result["words"] = len(words)

        result["timestamps"] = bool(words) and all(
            "start" in word
            and "end" in word
            for word in words
        )

        if (
            published is True
            and len(segments) > 0
            and len(words) > 0
            and result["timestamps"]
        ):
            result["status"] = "PASS"

    except Exception as exc:
        result["error"] = (
            f"{type(exc).__name__}: {exc}"
        )

    return result


def main() -> None:
    episodes = discover_episodes()

    print()
    print("DISCOVERED TV EPISODES:", len(episodes))
    print()

    results = [
        validate_episode(episode)
        for episode in episodes
    ]

    print(
        f"{'DATE':<12}"
        f"{'EP':<6}"
        f"{'PUB':<7}"
        f"{'URL':<7}"
        f"{'TR':<6}"
        f"{'SPK':<6}"
        f"{'SEG':<7}"
        f"{'WORDS':<8}"
        f"{'TIME':<7}"
        f"{'STATUS':<8}"
    )

    print("-" * 74)

    for result in results:
        print(
            f"{result['date']:<12}"
            f"{str(result['episode_http']):<6}"
            f"{str(result['published']):<7}"
            f"{str(result['transcript_url']):<7}"
            f"{str(result['transcript_http']):<6}"
            f"{result['speakers']:<6}"
            f"{result['segments']:<7}"
            f"{result['words']:<8}"
            f"{str(result['timestamps']):<7}"
            f"{result['status']:<8}"
        )

        if result["error"]:
            print(
                "  ERROR:",
                result["error"],
            )

    passed = sum(
        result["status"] == "PASS"
        for result in results
    )

    print()
    print(
        f"RESULT: {passed}/{len(results)} "
        "discovered episodes PASS"
    )

    if results and passed == len(results):
        print(
            "AUGUST E2E ACQUISITION PROBE: PASS"
        )
    else:
        print(
            "AUGUST E2E ACQUISITION PROBE: FAIL"
        )


if __name__ == "__main__":
    main()
