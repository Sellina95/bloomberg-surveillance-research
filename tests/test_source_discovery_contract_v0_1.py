from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.acquisition.source_discovery import DiscoveryError, select_candidates


TODAY = date(2026, 9, 6)


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

title_form = item(
    "title-form",
    "Bloomberg Surveillance 9/3/2026",
    "Bloomberg Surveillance full broadcast with Tom Keene and Lisa Abramowicz.",
    "1:58:00",
)
selected, _ = select_candidates([title_form], today=TODAY)
assert selected[0].broadcast_date == "2026-09-03"

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
