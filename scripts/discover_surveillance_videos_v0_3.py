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

from src.acquisition.source_discovery import DiscoveryError, select_candidates

API_KEY = os.environ["SERPAPI_API_KEY"]
ENDPOINT = "https://serpapi.com/search.json"
QUERIES = (
    "site:youtube.com Bloomberg Television full show Tom Keene Lisa Abramowicz",
    "site:youtube.com Bloomberg Television Surveillance full broadcast",
    "site:youtube.com Bloomberg Television Jonathan Ferro Annmarie Hordern full show",
)
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


def main() -> None:
    discovered: dict[str, dict] = {}
    for query in QUERIES:
        for item in search_youtube(query):
            video_id = item.get("video_id")
            if video_id:
                discovered[video_id] = item

    try:
        selected, rejected = select_candidates(discovered.values())
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
        "selected_count": len(selected),
        "videos": [candidate.as_dict() for candidate in selected],
        "rejections": rejected,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("SOURCE DISCOVERY CONTRACT: PASS")
    if any("bloomberg surveillance" not in row.title.lower() for row in selected):
        print("HEADLINE-TITLE DISCOVERY: PASS")
    print("OUTPUT:", OUTPUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
