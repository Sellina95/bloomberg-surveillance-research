# Transcript Normalization & Lineage Gate v0.1

## Status

CLOSED — PASS

## Purpose

Convert immutable raw Omny transcript JSON into deterministic, readable
segment records while preserving exact lineage back to the raw source.

This gate does not perform research chunking, semantic interpretation,
speaker identity resolution, transcription correction, or summarization.

## Input Contract

Canonical input:

data/raw/surveillance/YYYY-MM-DD/transcript.json

Required upstream provenance:

data/raw/surveillance/YYYY-MM-DD/metadata.json

The raw acquisition must already have passed the Raw Preservation &
Provenance integrity contract.

## Canonical Processed Segment

Each non-empty Omny transcript segment becomes one processed segment record.

Required fields:

- requested_date
- segment_id
- speaker_index
- start_seconds
- end_seconds
- word_count
- text

## Text Construction Contract

Processed `text` is constructed deterministically by joining the raw word
tokens in their original order with a single space.

The normalization layer must not:

- correct spelling;
- correct names;
- correct numbers;
- resolve speaker identities;
- merge segments;
- split segments;
- remove words;
- summarize content;
- add external information.

## Lineage Contract

Every processed segment must retain the original raw `segment_id`.

Its start timestamp must equal the first raw word start timestamp.

Its end timestamp must equal the last raw word end timestamp.

Its word_count must equal the number of raw words in that segment.

The processed text must be reproducible directly from the ordered raw word
tokens.

## Speaker Boundary

Raw Omny speaker indices are preserved exactly as provided.

Speaker indices are not treated as verified human identities.

Observed transcript structure shows that automatic speaker segmentation may
contain short interjections and apparent diarization noise. Speaker identity
resolution therefore belongs to a later downstream layer.

## Determinism Contract

For the same immutable raw transcript bytes, normalization must produce the
same processed segment content.

No LLM or stochastic model is permitted in this layer.

## Research Boundary

Omny segments are lineage anchors, not final research chunks.

Research chunking belongs to a separate downstream gate and may combine
multiple processed segments while preserving their source segment IDs and
timestamp range.

## Gate Validation Requirements

Before this gate can close, verify:

1. All non-empty raw segments are represented exactly once.
2. Segment IDs preserve raw ordering.
3. Speaker indices match raw values.
4. Start and end timestamps reproduce raw boundaries.
5. Word counts match raw segment word counts.
6. Processed text reproduces ordered raw word tokens.
7. Repeated normalization of identical raw input is deterministic.
8. Processed output preserves upstream raw SHA-256 lineage.

## Gate Decision

CLOSED — PASS

Validated across:
- 2026-08-13
- 2026-08-14

Both dates passed full raw-to-processed segment lineage validation,
ordering validation, field-level reproduction, raw SHA-256 lineage,
episode GUID lineage, deterministic serialization, persisted-output
verification, and deterministic rerun verification.
