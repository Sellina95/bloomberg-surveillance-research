from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta, timezone
from typing import Iterable


OFFICIAL_CHANNEL = "Bloomberg Television"
OFFICIAL_CHANNEL_ID = "UCIALMKvObZNtJ6AmdCLP7Lg"
PROGRAM_MARKER = re.compile(r"\bbloomberg\s+surveillance\b", re.I)
HOST_MARKERS = (
    "tom keene",
    "lisa abramowicz",
    "jonathan ferro",
    "annmarie hordern",
    "danielle booth",
)
EXCLUDED_MARKERS = (
    "podcast",
    "opening bell",
    "closing bell",
    "daybreak",
)
FULL_PROGRAM_SECONDS = 110 * 60


class DiscoveryError(RuntimeError):
    """A fail-closed source-discovery decision."""


@dataclass(frozen=True)
class Candidate:
    video_id: str
    title: str
    url: str
    channel_name: str
    channel_id: str
    channel_verified: bool
    description: str
    duration_seconds: int
    broadcast_date: str
    upload_date: str
    upload_date_raw: str
    source_mode: str
    host_markers: tuple[str, ...]

    def as_dict(self) -> dict:
        payload = asdict(self)
        payload["host_markers"] = list(self.host_markers)
        return payload


def parse_duration(value: object) -> int:
    if isinstance(value, (int, float)):
        return max(0, int(value))
    if not isinstance(value, str):
        return 0
    parts = value.strip().split(":")
    if not parts or not all(part.isdigit() for part in parts):
        return 0
    total = 0
    for part in parts:
        total = total * 60 + int(part)
    return total


def parse_explicit_date(text: str) -> str:
    patterns = (
        (r"\b(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})\b", "%Y-%m-%d"),
        (r"\b(\d{1,2})/(\d{1,2})/(20\d{2})\b", "%m-%d-%Y"),
    )
    for pattern, order in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        values = match.groups()
        raw = "-".join(values)
        try:
            return datetime.strptime(raw, order).date().isoformat()
        except ValueError:
            pass

    named = re.search(
        r"\b(January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+(\d{1,2})"
        r"(?:st|nd|rd|th)?,?\s+(20\d{2})\b",
        text,
        re.I,
    )
    if named:
        try:
            return datetime.strptime(
                " ".join(named.groups()), "%B %d %Y"
            ).date().isoformat()
        except ValueError:
            pass
    return ""


def normalize_upload_date(value: object, *, today: date | None = None) -> str:
    raw = str(value or "").strip()
    explicit = parse_explicit_date(raw)
    if explicit:
        return explicit
    match = re.fullmatch(r"(\d+)\s+(day|days)\s+ago", raw, re.I)
    if match:
        anchor = today or datetime.now(timezone.utc).date()
        return (anchor - timedelta(days=int(match.group(1)))).isoformat()
    if raw.lower() in {"today", "streamed today"}:
        return (today or datetime.now(timezone.utc).date()).isoformat()
    return ""


def normalize_candidate(item: dict, *, today: date | None = None) -> Candidate:
    channel = item.get("channel") or {}
    title = str(item.get("title") or "").strip()
    description = str(item.get("description") or "").strip()
    combined = f"{title}\n{description}".lower()

    channel_name = str(
        item.get("channel_name") or channel.get("name") or ""
    ).strip()
    channel_id = str(
        item.get("channel_id") or channel.get("id") or channel.get("channel_id") or ""
    ).strip()
    verified = bool(
        item.get("channel_verified", channel.get("verified", False))
    )
    if channel_name.casefold() != OFFICIAL_CHANNEL.casefold():
        raise DiscoveryError("not the official Bloomberg Television channel")
    if channel_id and channel_id != OFFICIAL_CHANNEL_ID:
        raise DiscoveryError("channel id conflicts with Bloomberg Television")
    if not verified and channel_id != OFFICIAL_CHANNEL_ID:
        raise DiscoveryError("official channel identity is not verified")
    if any(marker in combined for marker in EXCLUDED_MARKERS):
        raise DiscoveryError("excluded Bloomberg program or summary")
    if not PROGRAM_MARKER.search(description):
        raise DiscoveryError("description does not identify Bloomberg Surveillance")

    hosts = tuple(marker for marker in HOST_MARKERS if marker in description.lower())
    if not hosts:
        raise DiscoveryError("description does not identify a Surveillance host")

    video_id = str(item.get("video_id") or item.get("id") or "").strip()
    if not video_id:
        raise DiscoveryError("video id missing")
    url = str(item.get("link") or item.get("url") or "").strip()
    if not url:
        url = f"https://www.youtube.com/watch?v={video_id}"

    broadcast_date = parse_explicit_date(f"{title}\n{description}")
    if not broadcast_date:
        raise DiscoveryError("explicit broadcast date missing")
    upload_raw = str(item.get("published_date") or item.get("upload_date") or "")
    upload_date = normalize_upload_date(upload_raw, today=today)
    if not upload_date:
        raise DiscoveryError("upload date cannot be normalized")

    duration = parse_duration(item.get("length") or item.get("duration"))
    if not duration:
        raise DiscoveryError("duration missing or invalid")

    return Candidate(
        video_id=video_id,
        title=title,
        url=url,
        channel_name=channel_name,
        channel_id=channel_id or OFFICIAL_CHANNEL_ID,
        channel_verified=True,
        description=description,
        duration_seconds=duration,
        broadcast_date=broadcast_date,
        upload_date=upload_date,
        upload_date_raw=upload_raw,
        source_mode=("chaptered" if item.get("chapters") else "chapter_unknown"),
        host_markers=hosts,
    )


def select_candidates(items: Iterable[dict], *, today: date | None = None) -> tuple[list[Candidate], list[dict]]:
    accepted: list[Candidate] = []
    rejected: list[dict] = []
    for item in items:
        try:
            accepted.append(normalize_candidate(item, today=today))
        except DiscoveryError as exc:
            rejected.append({
                "video_id": item.get("video_id") or item.get("id"),
                "title": item.get("title", ""),
                "reason": str(exc),
            })

    by_date: dict[str, list[Candidate]] = {}
    for candidate in accepted:
        by_date.setdefault(candidate.broadcast_date, []).append(candidate)

    selected: list[Candidate] = []
    for broadcast_date, rows in sorted(by_date.items()):
        full = [row for row in rows if row.duration_seconds >= FULL_PROGRAM_SECONDS]
        if not full:
            rejected.extend({
                "video_id": row.video_id,
                "title": row.title,
                "reason": "no full-program candidate meets the duration contract",
            } for row in rows)
            continue
        pool = full
        best_duration = max(row.duration_seconds for row in pool)
        best = [row for row in pool if row.duration_seconds == best_duration]
        if len(best) != 1:
            raise DiscoveryError(
                f"ambiguous candidates for {broadcast_date}: "
                + ", ".join(row.video_id for row in best)
            )
        selected.append(best[0])
    return selected, rejected
