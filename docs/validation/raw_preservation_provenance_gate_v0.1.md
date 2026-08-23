# Raw Preservation & Provenance Gate v0.1

## Status

CLOSED — PASS

## Purpose

This gate verifies that every acquired Bloomberg Surveillance transcript can
later be traced to the upstream episode and acquisition event from which it
originated, while preserving raw-file integrity and preventing silent
overwrite.

This gate does not validate transcript semantic accuracy or downstream
research interpretation.

## Canonical Raw Unit

One acquired Bloomberg Surveillance TV episode is stored as one immutable raw
acquisition unit.

Canonical directory:

data/raw/surveillance/YYYY-MM-DD/

Required files:

- transcript.json
- metadata.json

## Raw Transcript Contract

`transcript.json` contains the raw transcript API response without semantic
cleaning, speaker correction, summarization, or external enrichment.

The raw acquisition layer does not:

- correct transcription errors;
- resolve generic speaker labels;
- alter transcript words;
- remove transcript segments;
- summarize transcript content;
- merge external facts into the raw transcript.

## Required Provenance Metadata

`metadata.json` preserves:

- requested_date
- program
- episode_title
- published_at
- episode_guid
- canonical_episode_url
- transcript_url
- acquired_at_utc
- transcript_sha256
- transcript_bytes

## Integrity Contract

SHA-256 is calculated from the exact bytes persisted as `transcript.json`.

Stored raw bytes can later be independently hashed and compared with
`transcript_sha256` in metadata.

## Immutability Contract

Existing canonical raw acquisitions are not silently overwritten.

On rerun:

1. Existing transcript and metadata are detected.
2. Stored transcript SHA-256 is recomputed.
3. Stored integrity is verified.
4. Existing transcript and metadata remain unchanged.
5. The acquisition returns `EXISTS_INTEGRITY_PASS`.

If stored raw bytes differ from the hash recorded in metadata, acquisition
stops with an explicit `IntegrityError`.

Upstream transcript revisions are not silently substituted for the historical
raw acquisition. Revision detection/versioning is outside this gate.

## Atomic Publication Contract

New acquisition units are first written to a temporary sibling directory.

Publication sequence:

Raw transcript retrieval
→ temporary transcript write
→ temporary metadata write
→ integrity verification
→ atomic directory rename
→ canonical acquisition becomes visible

A partially completed acquisition must not be published as the canonical raw
unit.

## Validation Evidence

### 2026-08-14 — Initial Raw Acquisition

Result: PASS

Observed provenance:

- requested_date: 2026-08-14
- episode_guid: e0baee1b-367d-49c5-8f03-b4a6010a6ef1
- published_at: 2026-08-14T16:17:14+00:00
- acquired_at_utc: 2026-08-23T13:56:39.956916+00:00
- transcript_bytes: 444499
- transcript_sha256:
  6ba0820925c2281c2935071e97ceb7d3357a4656cd40869f64baa09315fbd52f

Canonical episode URL and official transcript API URL were preserved in
metadata.

### Independent Integrity Check

Result: PASS

- Stored bytes: 444499
- Metadata bytes: 444499
- Byte-size match: PASS
- Independently recomputed SHA-256 matched metadata: PASS

### Rerun / No-Overwrite Check

Result: PASS

Second acquisition of 2026-08-14 returned:

`EXISTS_INTEGRITY_PASS`

Before/after checks:

- transcript SHA-256 unchanged: PASS
- metadata SHA-256 unchanged: PASS

The original acquisition timestamp and provenance record were therefore not
rewritten by the normal rerun.

### Corruption Detection Check

Result: PASS

One byte in the stored 2026-08-14 transcript was deliberately modified.

Observed behavior:

- transcript SHA-256 changed;
- acquisition raised `IntegrityError`;
- corruption was detected;
- original bytes were restored;
- restored SHA-256 exactly matched the original hash.

### Atomic Raw Acquisition Check

Validation date: 2026-08-13

Result: PASS

Observed:

- acquisition status: ACQUIRED
- canonical directory created: PASS
- transcript.json present: PASS
- metadata.json present: PASS
- temporary directory absent after publication: PASS
- transcript byte count matched metadata: PASS
- independently recomputed SHA-256 matched metadata: PASS

### Atomic Failure Cleanup Check

Result: PASS

A simulated failure was introduced between temporary raw-transcript creation
and metadata completion.

Observed:

- simulated failure detected: PASS
- canonical acquisition directory remained absent: PASS
- temporary acquisition directory was removed: PASS
- incomplete acquisition was not published canonically: PASS

This test validates the failure-cleanup semantics of the temporary-unit
publication pattern. It does not claim that fault injection occurred inside
the live network acquisition path.

## Provenance Boundary

This gate establishes acquisition provenance, local raw integrity,
immutability, and atomic publication behavior.

It does not assert that:

- automatic transcription is semantically correct;
- speaker names are correct;
- numbers or proper nouns were transcribed correctly;
- guest identities have been resolved;
- transcript-derived statements are factual;
- downstream summaries are accurate.

Those validations belong to downstream gates.

## Gate Decision

Raw Preservation & Provenance Gate v0.1 is CLOSED — PASS.

The validated raw acquisition implementation may be used as the immutable
source layer for downstream transcript processing.
