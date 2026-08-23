from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

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


def clean(text: str | None) -> str:
    return (text or "").strip()


def main() -> None:
    r = requests.get(
        RSS_URL,
        headers=HEADERS,
        timeout=60,
    )

    print("RSS HTTP:", r.status_code)
    print("RSS BYTES:", len(r.content))

    if r.status_code != 200:
        raise SystemExit("FAIL — RSS unavailable")

    root = ET.fromstring(r.content)

    items = root.findall("./channel/item")

    print("TOTAL RSS ITEMS:", len(items))
    print()

    matches = []

    for item in items:
        title = clean(item.findtext("title"))
        pub_date_raw = clean(item.findtext("pubDate"))
        link = clean(item.findtext("link"))
        guid = clean(item.findtext("guid"))

        if not pub_date_raw:
            continue

        try:
            pub_date = parsedate_to_datetime(pub_date_raw)

            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)

            pub_date_utc = pub_date.astimezone(timezone.utc)

        except (TypeError, ValueError):
            continue

        if not (
            WINDOW_START <= pub_date_utc < WINDOW_END
        ):
            continue

        # Exact program-edition classification by title,
        # not substring matching against a guessed URL.
        if not title.lower().startswith(
            "bloomberg surveillance tv"
        ):
            continue

        matches.append(
            {
                "title": title,
                "pub_date": pub_date_raw,
                "link": link,
                "guid": guid,
            }
        )

    print("=" * 100)
    print("BLOOMBERG SURVEILLANCE TV — 2026-08-01 THROUGH 2026-08-21")
    print("=" * 100)
    print()

    for index, episode in enumerate(matches, 1):
        print(f"[{index}]")
        print("TITLE:", episode["title"])
        print("PUBDATE:", episode["pub_date"])
        print("LINK:", episode["link"])
        print("GUID:", episode["guid"])
        print()

    print("=" * 100)
    print("TV EPISODES FOUND:", len(matches))


if __name__ == "__main__":
    main()
