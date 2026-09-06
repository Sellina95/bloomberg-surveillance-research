from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.acquisition.source_discovery import (
    DiscoveryError,
    hydrate_search_result,
    select_candidates,
)


TODAY = date(2026, 9, 6)

snippet = {
    "video_id": "hydration-test",
    "title": "Jobs Shock Reshapes the Rate Path",
    "channel": {"name": "Bloomberg Television", "verified": True},
}
detail = {
    "video_results": {
        "video_id": "hydration-test",
        "description": "Bloomberg Surveillance full broadcast for Sep 4, 2026, "
        "with Tom Keene and Lisa Abramowicz.",
        "published_date": "Sep 5, 2026",
        "length": "2:03:00",
        "channel": {
            "name": "Bloomberg Television",
            "id": "UCIALMKvObZNtJ6AmdCLP7Lg",
            "verified": True,
        },
    },
    "chapters": [{"title": "Opening", "time_start": 0}],
}
hydrated = hydrate_search_result(snippet, detail)
selected, _ = select_candidates([hydrated], today=TODAY)
assert selected[0].video_id == "hydration-test"
assert selected[0].source_mode == "chaptered"
print("SOURCE METADATA HYDRATION: PASS")

top_level = dict(detail["video_results"])
top_level["chapters"] = detail["chapters"]
hydrated_top_level = hydrate_search_result(snippet, top_level)
selected, _ = select_candidates([hydrated_top_level], today=TODAY)
assert selected[0].video_id == "hydration-test"


def item(video_id: str, title: str, description: str, length: str, **extra):
    return {
        "video_id": video_id,
        "title": title,
        "description": description,
        "length": length,
        "published_date": "September 5, 2026",
        "channel": {
            "name": "Bloomberg Television",
            "id": "UCIALMKvObZNtJ6AmdCLP7Lg",
            "verified": True,
        },
        **extra,
    }


headline = item(
    "headline-full",
    "Jobs Shock Reshapes the Rate Path",
    "Bloomberg Surveillance full broadcast for September 4, 2026, "
    "with Tom Keene and Lisa Abramowicz.",
    "2:03:00",
)
short = item(
    "headline-short",
    "Jobs Shock Reshapes the Rate Path — Highlights",
    "Bloomberg Surveillance broadcast for September 4, 2026 with Tom Keene.",
    "22:13",
)

selected, rejected = select_candidates([short, headline], today=TODAY)
assert [row.video_id for row in selected] == ["headline-full"]
assert selected[0].broadcast_date == "2026-09-04"
assert selected[0].upload_date == "2026-09-05"
assert selected[0].url.endswith("headline-full")
print("SOURCE DISCOVERY CONTRACT: PASS")
print("HEADLINE-TITLE DISCOVERY: PASS")

discovery_script = (
    Path(__file__).resolve().parents[1]
    / "scripts/discover_surveillance_videos_v0_3.py"
).read_text(encoding="utf-8")
assert '"channel": CHANNEL_HANDLE' not in discovery_script
assert '"engine": "youtube"' in discovery_script
assert '"search_query": query' in discovery_script
assert '"engine": "youtube_video"' in discovery_script
assert '"v": video_id' in discovery_script
assert "SOURCE CANDIDATE DIAGNOSTICS" in discovery_script
assert '"description": description' not in discovery_script
print("SERPAPI OFFICIAL PARAMETER CONTRACT: PASS")

title_form = item(
    "title-form",
    "Bloomberg Surveillance 9/3/2026",
    "Markets coverage with Tom Keene and Lisa Abramowicz.",
    "1:58:00",
)
selected, _ = select_candidates([title_form], today=TODAY)
assert selected[0].broadcast_date == "2026-09-03"
assert selected[0].identity_mode == "title_program_description_hosts"

missing_program = item(
    "missing-program",
    "Jobs Shock Reshapes the Rate Path 9/3/2026",
    "Markets coverage with Tom Keene and Lisa Abramowicz.",
    "1:58:00",
)
selected, rejected = select_candidates([missing_program], today=TODAY)
assert selected == []
assert rejected[0]["reason"] == "metadata does not identify Bloomberg Surveillance"

selected, rejected = select_candidates([short], today=TODAY)
assert selected == []
assert rejected[-1]["reason"].startswith("no full-program")


excluded = item(
    "opening",
    "Opening Bell",
    "Bloomberg Surveillance September 4, 2026 with Tom Keene.",
    "2:10:00",
)
selected, rejected = select_candidates([excluded], today=TODAY)
assert selected == [] and rejected


ambiguous_a = item(
    "a",
    "Macro Reset",
    "Bloomberg Surveillance September 3, 2026 with Tom Keene.",
    "2:00:00",
)
ambiguous_b = item(
    "b",
    "Rates Reset",
    "Bloomberg Surveillance September 3, 2026 with Lisa Abramowicz.",
    "2:00:00",
)
try:
    select_candidates([ambiguous_a, ambiguous_b], today=TODAY)
except DiscoveryError:
    pass
else:
    raise AssertionError("ambiguous source selection must fail closed")
