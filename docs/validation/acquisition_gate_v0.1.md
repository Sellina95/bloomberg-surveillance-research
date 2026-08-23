# Acquisition Gate v0.1

## Status

CLOSED — PASS

## Validation Window

2026-08-01 through 2026-08-21

Within this window, 15 Bloomberg Surveillance TV episodes were published and
discovered through the official Omny RSS feed.

## Canonical Acquisition Path

Date
→ Official Omny Bloomberg Surveillance RSS
→ Bloomberg Surveillance TV episode metadata
→ Canonical episode URL
→ Published TranscriptUrl
→ Official Omny transcript API
→ Structured transcript JSON

Episode URLs are discovered from upstream RSS metadata and are not generated
from assumed URL naming conventions.

## Validation Results

| Check | Result |
|---|---:|
| TV episodes discovered | 15 |
| Episode page HTTP 200 | 15/15 |
| Published transcript available | 15/15 |
| Transcript URL discovered | 15/15 |
| Transcript API HTTP 200 | 15/15 |
| Non-empty transcript segments | 15/15 |
| Non-empty transcript words | 15/15 |
| Word-level timestamps present | 15/15 |
| End-to-end acquisition | PASS |

## Important Finding

An initial implementation assumed that episode URLs could be generated from
the broadcast date.

That assumption failed for episodes whose canonical URLs contain additional
suffixes such as `-podcast`.

Example:

- 2026-08-14
- 2026-08-17

The production acquisition design therefore does not infer episode URLs.
Canonical episode URLs must come from official RSS metadata.

## Raw Transcript Structure

The official transcript endpoint returns structured JSON containing:

- speaker indices;
- transcript segments;
- individual words;
- word-level start timestamps;
- word-level end timestamps.

Speaker labels may be generic and automatic transcription may contain errors.
Raw transcript data must therefore remain immutable. Any speaker resolution,
name correction, or text normalization belongs to a separate downstream layer.

## Boundary

This gate validates transcript acquisition and provenance structure only.

It does NOT validate:

- transcript semantic accuracy;
- speaker identity resolution;
- transcript cleaning;
- fact/view classification;
- theme extraction;
- summarization;
- external news synthesis;
- trading or investment signals.

## Gate Decision

Acquisition Gate v0.1 is CLOSED.

The validated acquisition path may now be implemented in `src/acquisition/`.
