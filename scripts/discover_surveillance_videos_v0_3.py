from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.acquisition.source_discovery import (
    DiscoveryError,
    EXCLUDED_MARKERS,
    OFFICIAL_CHANNEL,
    OFFICIAL_CHANNEL_ID,
    HOST_MARKERS,
    PROGRAM_MARKER,
    hydrate_search_result,
    parse_explicit_date,
    parse_duration,
    normalize_upload_date,
    rank_search_candidates,
    select_candidates,
)

API_KEY = os.environ["SERPAPI_API_KEY"]
ENDPOINT = "https://serpapi.com/search.json"
QUERIES = (
    "site:youtube.com Bloomberg Television full show Tom Keene Lisa Abramowicz",
    "site:youtube.com Bloomberg Television Surveillance full broadcast",
    "site:youtube.com Bloomberg Television Jonathan Ferro Lisa Abramowicz Annmarie Hordern",
)
MAX_DETAIL_CANDIDATES = 6
DISCOVERY_WINDOW_DAYS = 2
OUTPUT = ROOT / "data/processed/surveillance/surveillance_video_inventory_v0_3.json"


def search_youtube(query: str) -> list[dict]:
    url = ENDPOINT + "?" + urlencode({
        "engine": "youtube",
        "search_query": query,
        "api_key": API_KEY,
    })
    try:
        with urlopen(
            Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60
        ) as response:
            return json.loads(response.read().decode("utf-8")).get("video_results", [])
    except HTTPError as exc:
        if exc.code == 429:
            raise SystemExit(
                "SOURCE DISCOVERY PROVIDER: FAIL — "
                "SerpApi HTTP 429; account quota or provider rate limit exhausted"
            ) from exc
        raise


def fetch_video_detail(video_id: str) -> dict:
    url = ENDPOINT + "?" + urlencode({
        "engine": "youtube_video",
        "v": video_id,
        "api_key": API_KEY,
    })
    try:
        with urlopen(
            Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60
        ) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 429:
            raise SystemExit(
                "SOURCE DISCOVERY PROVIDER: FAIL — "
                "SerpApi HTTP 429; account quota or provider rate limit exhausted"
            ) from exc
        raise


def official_search_candidate(item: dict) -> bool:
    channel = item.get("channel") or {}
    name = str(channel.get("name") or item.get("channel_name") or "").strip()
    channel_id = str(channel.get("id") or channel.get("channel_id") or "").strip()
    if name.casefold() != OFFICIAL_CHANNEL.casefold() and channel_id != OFFICIAL_CHANNEL_ID:
        return False
    combined = f"{item.get('title', '')}\n{item.get('description', '')}".lower()
    return not any(marker in combined for marker in EXCLUDED_MARKERS)


def target_broadcast_date() -> str:
    override = os.environ.get("SURVEILLANCE_DATE", "").strip()
    if override:
        try:
            target = date.fromisoformat(override[:10])
        except ValueError as exc:
            raise SystemExit(
                f"SOURCE DISCOVERY CONTRACT: FAIL — invalid SURVEILLANCE_DATE: {override}"
            ) from exc
    else:
        # Workflow runs at 07:30 KST, while GitHub Actions clock is UTC.
        # Resolve the publication/broadcast target in Korea local time so
        # 22:30 UTC on Thursday correctly targets Friday in KST.
        # Scheduled publication runs at 07:30 KST for the prior
        # Bloomberg Surveillance broadcast day.
        target = datetime.now(ZoneInfo("Asia/Seoul")).date() - timedelta(days=1)
        while target.weekday() >= 5:
            target -= timedelta(days=1)
    return target.isoformat()


def target_aware_shortlist(items: list[dict], target_date: str) -> list[dict]:
    target = date.fromisoformat(target_date)
    ranked = rank_search_candidates(items)

    nearby: list[dict] = []
    for item in ranked:
        upload_date = normalize_upload_date(
            item.get("published_date") or item.get("upload_date")
        )
        if not upload_date:
            continue
        try:
            upload = date.fromisoformat(upload_date)
        except ValueError:
            continue
        if abs((upload - target).days) <= DISCOVERY_WINDOW_DAYS:
            nearby.append(item)

    # For the target-date window, do not truncate before hydration.
    # If provider date metadata is unavailable, retain a bounded fallback.
    return (
        nearby[:MAX_DETAIL_CANDIDATES]
        if nearby
        else ranked[:MAX_DETAIL_CANDIDATES]
    )


def main() -> None:
    discovered: dict[str, dict] = {}
    for query in QUERIES:
        for item in search_youtube(query):
            video_id = item.get("video_id")
            if video_id and official_search_candidate(item):
                discovered[video_id] = item

    # The official search response already supplies channel and length.
    # Hydrate only full-program candidates to cap SerpApi calls and obtain
    # the complete description needed by the strict identity contract.
    full_program_results = [
        item for item in discovered.values()
        if parse_duration(item.get("length") or item.get("duration")) >= 110 * 60
    ]
    target_date = target_broadcast_date()
    shortlist = target_aware_shortlist(full_program_results, target_date)

    print("TARGET BROADCAST DATE:", target_date)
    print("FULL-PROGRAM SEARCH CANDIDATES:", len(full_program_results))
    print("HYDRATION SHORTLIST:", len(shortlist))

    hydrated = []
    hydration_failures = []
    for item in shortlist:
        video_id = item["video_id"]
        try:
            hydrated.append(hydrate_search_result(item, fetch_video_detail(video_id)))
        except Exception as exc:
            hydration_failures.append({
                "video_id": video_id,
                "title": item.get("title", ""),
                "reason": f"metadata hydration failed: {type(exc).__name__}",
            })

    # Non-sensitive diagnostics are printed only to establish the live
    # provider contract. Never print descriptions or transcript text.
    print("SOURCE CANDIDATE DIAGNOSTICS")
    for item in hydrated:
        channel = item.get("channel") or {}
        description = str(item.get("description") or "")
        print(json.dumps({
            "video_id": item.get("video_id"),
            "title": item.get("title", ""),
            "channel_name": channel.get("name"),
            "channel_id": channel.get("id") or channel.get("channel_id"),
            "channel_verified": channel.get("verified"),
            "duration_seconds": parse_duration(
                item.get("length") or item.get("duration")
            ),
            "broadcast_date_detected": parse_explicit_date(
                f"{item.get('title', '')}\n{description}"
            ),
            "upload_date_raw": item.get("published_date") or item.get("upload_date"),
            "description_program_marker": bool(PROGRAM_MARKER.search(description)),
            "description_host_markers": [
                marker for marker in HOST_MARKERS if marker in description.lower()
            ],
            "chapters_available": bool(item.get("chapters")),
        }, ensure_ascii=False, sort_keys=True))

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

    target_selected = [
        candidate
        for candidate in selected
        if candidate.broadcast_date == target_date
    ]
    if not target_selected:
        print("TARGET-DATE REJECTION DIAGNOSTICS")
        for row in (rejected + hydration_failures)[:10]:
            print(json.dumps({
                "video_id": row.get("video_id"),
                "title": row.get("title", ""),
                "reason": row.get("reason", ""),
            }, ensure_ascii=False, sort_keys=True))
        raise SystemExit(
            "SOURCE DISCOVERY CONTRACT: FAIL — "
            f"no validated full Bloomberg Surveillance broadcast for {target_date}"
        )

    payload = {
        "schema_version": "surveillance_video_inventory_v0_4",
        "discovered_at": datetime.now(timezone.utc).isoformat(),
        "query_count": len(QUERIES),
        "candidate_count": len(discovered),
        "shortlist_count": len(shortlist),
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
