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
    broadcast_date_basis: str
    upload_date: str
    upload_date_raw: str
    source_mode: str
    identity_mode: str
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
        r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
        r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|"
        r"Nov(?:ember)?|Dec(?:ember)?)\s+(\d{1,2})"
        r"(?:st|nd|rd|th)?,?\s+(20\d{2})\b",
        text,
        re.I,
    )
    if named:
        try:
            raw = " ".join(named.groups())
            for format_string in ("%B %d %Y", "%b %d %Y"):
                try:
                    return datetime.strptime(raw, format_string).date().isoformat()
                except ValueError:
                    pass
        except ValueError:
            pass
    return ""


def parse_partial_named_date(text: str, *, reference_year: int) -> str:
    """Resolve 'September 8' only when an exact provider year is available."""
    named = re.search(
        r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
        r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|"
        r"Nov(?:ember)?|Dec(?:ember)?)\s+(\d{1,2})"
        r"(?:st|nd|rd|th)?\b",
        text,
        re.I,
    )
    if not named:
        return ""
    raw = f"{named.group(1)} {named.group(2)} {reference_year}"
    for format_string in ("%B %d %Y", "%b %d %Y"):
        try:
            return datetime.strptime(raw, format_string).date().isoformat()
        except ValueError:
            pass
    return ""


def has_exact_provider_date(value: object) -> bool:
    """Relative labels are useful for ranking, never for broadcast dating."""
    return bool(parse_explicit_date(str(value or "").strip()))


def hydrate_search_result(search_item: dict, detail_payload: dict) -> dict:
    """Merge exact youtube_video metadata over an incomplete search snippet."""
    detail = (
        detail_payload.get("video_results")
        or detail_payload.get("video")
        or detail_payload
    )
    if isinstance(detail, list):
        wanted = search_item.get("video_id")
        detail = next(
            (row for row in detail if isinstance(row, dict) and row.get("video_id") == wanted),
            detail[0] if detail and isinstance(detail[0], dict) else {},
        )
    if not isinstance(detail, dict):
        detail = {}

    merged = dict(search_item)
    for field in (
        "video_id", "title", "link", "description", "published_date",
        "upload_date", "length", "duration",
    ):
        value = detail.get(field)
        if value not in (None, "", [], {}):
            merged[field] = value

    search_channel = search_item.get("channel") or {}
    detail_channel = detail.get("channel") or detail_payload.get("channel") or {}
    if isinstance(search_channel, dict) and isinstance(detail_channel, dict):
        merged["channel"] = {**search_channel, **detail_channel}
    if detail_payload.get("chapters"):
        merged["chapters"] = detail_payload["chapters"]
    merged["metadata_hydrated"] = True
    return merged


def normalize_upload_date(value: object, *, today: date | None = None) -> str:
    raw = str(value or "").strip()
    explicit = parse_explicit_date(raw)
    if explicit:
        return explicit
    match = re.fullmatch(
        r"(\d+)\s+(minute|minutes|hour|hours|day|days|week|weeks)\s+ago",
        raw,
        re.I,
    )
    if match:
        anchor = today or datetime.now(timezone.utc).date()
        amount = int(match.group(1))
        unit = match.group(2).lower()
        days = amount * 7 if unit.startswith("week") else (
            amount if unit.startswith("day") else 0
        )
        return (anchor - timedelta(days=days)).isoformat()
    if raw.lower() in {"today", "streamed today"}:
        return (today or datetime.now(timezone.utc).date()).isoformat()
    return ""


def rank_search_candidates(
    items: Iterable[dict], *, today: date | None = None
) -> list[dict]:
    """Prefer recent full-program search results before paid hydration."""
    anchor = today or datetime.now(timezone.utc).date()

    def key(item: dict) -> tuple[str, int]:
        upload_date = normalize_upload_date(
            item.get("published_date") or item.get("upload_date"),
            today=anchor,
        )
        duration = parse_duration(item.get("length") or item.get("duration"))
        return upload_date or "0000-00-00", duration

    return sorted(items, key=key, reverse=True)


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
    hosts = tuple(marker for marker in HOST_MARKERS if marker in description.lower())
    if not hosts:
        raise DiscoveryError("description does not identify a Surveillance host")

    # SerpApi's current youtube_video response can expose the programme name in
    # the title while its full description names the presenters but omits the
    # words "Bloomberg Surveillance". Treat those two metadata fields as one
    # identity record; never infer identity from a headline title alone.
    program_in_description = bool(PROGRAM_MARKER.search(description))
    program_in_title = bool(PROGRAM_MARKER.search(title))
    if not program_in_description and not program_in_title:
        raise DiscoveryError("metadata does not identify Bloomberg Surveillance")
    identity_mode = (
        "description_program_and_hosts"
        if program_in_description
        else "title_program_description_hosts"
    )

    video_id = str(item.get("video_id") or item.get("id") or "").strip()
    if not video_id:
        raise DiscoveryError("video id missing")
    url = str(item.get("link") or item.get("url") or "").strip()
    if not url:
        url = f"https://www.youtube.com/watch?v={video_id}"

    upload_raw = str(item.get("published_date") or item.get("upload_date") or "")
    upload_date = normalize_upload_date(upload_raw, today=today)
    if not upload_date:
        raise DiscoveryError("upload date cannot be normalized")

    duration = parse_duration(item.get("length") or item.get("duration"))
    if not duration:
        raise DiscoveryError("duration missing or invalid")

    supplied_broadcast_date = str(item.get("broadcast_date") or "").strip()
    broadcast_date = parse_explicit_date(supplied_broadcast_date)
    broadcast_date_basis = "provider_broadcast_date"
    if not broadcast_date:
        broadcast_date = parse_explicit_date(f"{title}\n{description}")
        broadcast_date_basis = "title_or_description"
    if not broadcast_date and has_exact_provider_date(upload_raw):
        broadcast_date = parse_partial_named_date(
            f"{title}\n{description}",
            reference_year=date.fromisoformat(upload_date).year,
        )
        if broadcast_date:
            broadcast_date_basis = "partial_title_date_with_provider_year"
    if not broadcast_date:
        # Headline-titled full shows may omit the calendar date from both the
        # title and description. Only use the provider upload date after the
        # official channel, programme, host, hydration, and duration contracts
        # have all passed. Short clips can never enter this fallback.
        if (
            item.get("metadata_hydrated")
            and program_in_description
            and duration >= FULL_PROGRAM_SECONDS
            and has_exact_provider_date(upload_raw)
        ):
            broadcast_date = upload_date
            broadcast_date_basis = "official_full_show_upload_date"
        else:
            raise DiscoveryError(
                "exact broadcast date missing; relative upload labels "
                "cannot establish a broadcast date"
            )

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
        broadcast_date_basis=broadcast_date_basis,
        upload_date=upload_date,
        upload_date_raw=upload_raw,
        source_mode=("chaptered" if item.get("chapters") else "chapter_unknown"),
        identity_mode=identity_mode,
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
