from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.acquisition.source_discovery import (
    DiscoveryError,
    EXCLUDED_MARKERS,
    OFFICIAL_CHANNEL,
    OFFICIAL_CHANNEL_ID,
    hydrate_search_result,
    select_candidates,
)

API_KEY = os.environ["SERPAPI_API_KEY"]
ENDPOINT = "https://serpapi.com/search.json"
QUERIES = (
    "site:youtube.com Bloomberg Television full show Tom Keene Lisa Abramowicz",
    "site:youtube.com Bloomberg Television Surveillance full broadcast",
    "site:youtube.com Bloomberg Television Jonathan Ferro Annmarie Hordern full show",
)
CHANNEL_HANDLE = "@markets"
MAX_DETAIL_CANDIDATES = 12
OUTPUT = ROOT / "data/processed/surveillance/surveillance_video_inventory_v0_3.json"


def search_youtube(query: str) -> list[dict]:
    url = ENDPOINT + "?" + urlencode({
        "engine": "youtube",
        "search_query": query,
        "api_key": API_KEY,
    })
    with urlopen(
        Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60
    ) as response:
        return json.loads(response.read().decode("utf-8")).get("video_results", [])


def fetch_channel_uploads() -> list[dict]:
    url = ENDPOINT + "?" + urlencode({
        "engine": "youtube",
        "channel": CHANNEL_HANDLE,
        "api_key": API_KEY,
    })
    with urlopen(
        Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60
    ) as response:
        return json.loads(response.read().decode("utf-8")).get("video_results", [])


def fetch_video_detail(video_id: str) -> dict:
    url = ENDPOINT + "?" + urlencode({
        "engine": "youtube_video",
        "v": video_id,
        "api_key": API_KEY,
    })
    with urlopen(
        Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60
    ) as response:
        return json.loads(response.read().decode("utf-8"))


def official_search_candidate(item: dict) -> bool:
    channel = item.get("channel") or {}
    name = str(channel.get("name") or item.get("channel_name") or "").strip()
    channel_id = str(channel.get("id") or channel.get("channel_id") or "").strip()
    if name.casefold() != OFFICIAL_CHANNEL.casefold() and channel_id != OFFICIAL_CHANNEL_ID:
        return False
    combined = f"{item.get('title', '')}\n{item.get('description', '')}".lower()
    return not any(marker in combined for marker in EXCLUDED_MARKERS)


def main() -> None:
    discovered: dict[str, dict] = {}
    for item in fetch_channel_uploads():
        video_id = item.get("video_id")
        if not video_id:
            continue
        channel_item = dict(item)
        channel_item.setdefault("channel", {
            "name": OFFICIAL_CHANNEL,
            "id": OFFICIAL_CHANNEL_ID,
            "verified": True,
        })
        if official_search_candidate(channel_item):
            discovered[video_id] = channel_item
    for query in QUERIES:
        for item in search_youtube(query):
            video_id = item.get("video_id")
            if video_id and official_search_candidate(item):
                discovered[video_id] = item

    hydrated = []
    hydration_failures = []
    for item in list(discovered.values())[:MAX_DETAIL_CANDIDATES]:
        video_id = item["video_id"]
        try:
            hydrated.append(hydrate_search_result(item, fetch_video_detail(video_id)))
        except Exception as exc:
            hydration_failures.append({
                "video_id": video_id,
                "title": item.get("title", ""),
                "reason": f"metadata hydration failed: {type(exc).__name__}",
            })

    try:
        selected, rejected = select_candidates(hydrated)
    except DiscoveryError as exc:
        raise SystemExit(f"SOURCE DISCOVERY CONTRACT: FAIL — {exc}")

    if not selected:
        reasons = "; ".join(row["reason"] for row in rejected[:5])
        raise SystemExit(
            "SOURCE DISCOVERY CONTRACT: FAIL — no unambiguous official full broadcast; "
            + reasons
        )

    payload = {
        "schema_version": "surveillance_video_inventory_v0_4",
        "discovered_at": datetime.now(timezone.utc).isoformat(),
        "query_count": len(QUERIES),
        "candidate_count": len(discovered),
        "hydrated_count": len(hydrated),
        "selected_count": len(selected),
        "videos": [candidate.as_dict() for candidate in selected],
        "rejections": rejected + hydration_failures,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("SOURCE DISCOVERY CONTRACT: PASS")
    if any("bloomberg surveillance" not in row.title.lower() for row in selected):
        print("HEADLINE-TITLE DISCOVERY: PASS")
    print("OUTPUT:", OUTPUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
