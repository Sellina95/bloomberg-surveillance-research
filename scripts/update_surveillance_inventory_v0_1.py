from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

INVENTORY = (
    ROOT
    / "data/processed/surveillance/"
    / "surveillance_video_inventory_august_2026.json"
)

DISCOVER = (
    ROOT
    / "scripts/discover_surveillance_videos_v0_3.py"
)


def main() -> None:

    if not INVENTORY.exists():
        raise SystemExit(
            f"FAIL — inventory not found: {INVENTORY}"
        )

    if not DISCOVER.exists():
        raise SystemExit(
            f"FAIL — discovery script not found: {DISCOVER}"
        )

    print("=" * 100)
    print("SURVEILLANCE INVENTORY UPDATE v0.1")
    print("=" * 100)

    # ------------------------------------------------------------
    # 1. Run existing discovery layer
    # ------------------------------------------------------------

    print()
    print("=" * 100)
    print("RUN DISCOVERY")
    print("=" * 100)

    result = subprocess.run(
        [
            sys.executable,
            str(DISCOVER),
        ],
        cwd=ROOT,
        env=os.environ.copy(),
    )

    if result.returncode != 0:
        raise SystemExit(
            "FAIL — surveillance discovery failed"
        )

    # ------------------------------------------------------------
    # 2. Locate discovery artifacts
    # ------------------------------------------------------------

    discovery_path = (
        ROOT
        / "data/processed/surveillance/"
        / "surveillance_video_inventory_v0_3.json"
    )

    if not discovery_path.exists():
        raise SystemExit(
            f"FAIL — discovery artifact not found: "
            f"{discovery_path}"
        )

    print(
        "DISCOVERY:",
        discovery_path,
    )

    # ------------------------------------------------------------
    # 3. Load existing inventory
    # ------------------------------------------------------------

    inventory = json.loads(
        INVENTORY.read_text(
            encoding="utf-8"
        )
    )

    existing_videos = inventory.get(
        "videos",
        []
    )

    existing_ids = {
        video.get("video_id")
        for video in existing_videos
        if video.get("video_id")
    }

    # ------------------------------------------------------------
    # 4. Load discovered videos
    # ------------------------------------------------------------

    discovered = json.loads(
        discovery_path.read_text(
            encoding="utf-8"
        )
    )

    if isinstance(discovered, dict):
        discovered_videos = discovered.get(
            "videos",
            []
        )
    elif isinstance(discovered, list):
        discovered_videos = discovered
    else:
        discovered_videos = []

    # ------------------------------------------------------------
    # 5. Add only genuinely new videos
    # ------------------------------------------------------------

    import re
    from datetime import datetime

    added = []

    for video in discovered_videos:

        video_id = (
            video.get("video_id")
            or video.get("id")
        )

        title = video.get(
            "title",
            "",
        )

        if not video_id:
            continue

        if video_id in existing_ids:
            continue

        # Bloomberg Surveillance titles contain
        # the actual broadcast date:
        # "Bloomberg Surveillance 8/20/2026"
        match = re.search(
            r"Bloomberg Surveillance\\s+"
            r"(\\d{1,2})/(\\d{1,2})/(\\d{4})",
            title,
            flags=re.IGNORECASE,
        )

        if not match:
            print(
                "SKIP — unable to parse video date:",
                video_id,
                "|",
                title,
            )
            continue

        month, day, year = match.groups()

        video_date = datetime.strptime(
            f"{year}-{month}-{day}",
            "%Y-%m-%d",
        ).date().isoformat()

        normalized = {
            "video_id": video_id,
            "title": title,
            "link": video.get(
                "link",
                (
                    "https://www.youtube.com/watch?v="
                    + video_id
                ),
            ),
            "channel_name": video.get(
                "channel_name",
                "Bloomberg Television",
            ),
            "channel_verified": video.get(
                "channel_verified",
                True,
            ),
            "published_date": video.get(
                "published_date",
                "",
            ),
            "length": video.get(
                "length",
                "",
            ),
            "description": video.get(
                "description",
                "",
            ),
            "video_date": video_date,
        }

        existing_videos.append(
            normalized
        )

        existing_ids.add(
            video_id
        )

        added.append(
            normalized
        )

    # ------------------------------------------------------------
    # 6. Sort chronologically
    # ------------------------------------------------------------

    existing_videos.sort(
        key=lambda x: (
            x.get("video_date")
            or "0000-00-00"
        )
    )

    inventory["videos"] = existing_videos
    inventory["selected_count"] = len(
        existing_videos
    )

    inventory["end_date"] = (
        max(
            (
                v.get("video_date")
                for v in existing_videos
                if v.get("video_date")
            ),
            default=inventory.get(
                "end_date",
                "",
            ),
        )
    )

    # ------------------------------------------------------------
    # 7. Write updated inventory
    # ------------------------------------------------------------

    INVENTORY.write_text(
        json.dumps(
            inventory,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # ------------------------------------------------------------
    # 8. Result
    # ------------------------------------------------------------

    print()
    print("=" * 100)
    print("INVENTORY UPDATE RESULT")
    print("=" * 100)

    print(
        "EXISTING:",
        len(existing_videos) - len(added),
    )

    print(
        "ADDED:",
        len(added),
    )

    print(
        "TOTAL:",
        len(existing_videos),
    )

    for video in added:

        print(
            "NEW:",
            video["video_date"],
            "|",
            video["video_id"],
            "|",
            video["title"],
        )

    print()
    print(
        "OUTPUT:",
        INVENTORY,
    )

    print("=" * 100)
    print("STATUS: PASS")
    print("=" * 100)


if __name__ == "__main__":
    main()
