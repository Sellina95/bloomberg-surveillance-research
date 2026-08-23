# Bloomberg Surveillance Research

A personal research workflow for converting long-form Bloomberg Surveillance
transcripts into structured, source-preserving institutional market briefs.

## Purpose

This project is designed to reduce the time required to review long-form
institutional market commentary while preserving the context needed for
independent research.

Initial pipeline:

Date
→ Episode Discovery
→ Raw Transcript
→ Transcript Processing
→ Institutional Research Extraction
→ Daily Research Brief

## Research Principles

- Preserve raw source material separately from processed output.
- Distinguish FACT from GUEST VIEW and analyst interpretation.
- Preserve speaker/institution attribution where available.
- Preserve source provenance and timestamps where available.
- Do not treat commentary frequency as a trading signal.
- Do not connect outputs directly to production investment systems.
- External facts and transcript-derived statements must remain distinguishable.

## v0.1 Goal

Given a Bloomberg Surveillance date:

1. Discover the relevant episode.
2. Acquire an available transcript.
3. Preserve the raw transcript.
4. Produce a structured daily research brief.
5. Maintain enough provenance to audit the summary against the source.

## Status

Research prototype.

---

## Acquisition Contract v0.1

### Canonical Input

- Input key: `date`
- Format: `YYYY-MM-DD`
- One requested date represents one Bloomberg Surveillance broadcast date.

### Canonical Scope

For v0.1, the canonical source is:

- Program: Bloomberg Surveillance
- Edition: TV
- One canonical TV episode per requested broadcast date.

Bloomberg Surveillance Radio and individual interview clips are intentionally
excluded from the v0.1 canonical dataset.

### Source Priority

1. Official Bloomberg-distributed transcript when available.
2. Official podcast/distribution transcript when available.
3. YouTube English captions as fallback.
4. Third-party transcript services only as discovery/fallback sources.

The exact source used must always be recorded.

### Raw Preservation Rule

Raw transcript content must be preserved separately from derived outputs.

The acquisition layer must not:

- summarize the transcript;
- correct wording;
- silently repair names or numbers;
- remove content;
- merge external information into the transcript.

Cleaning and interpretation belong to later pipeline stages.

### Required Provenance

Every acquired episode must preserve, where available:

- requested date;
- episode title;
- broadcast/published date;
- source provider;
- source URL;
- transcript type;
- acquisition timestamp;
- raw transcript file path.

### Acquisition Gate

Status: **CLOSED — PASS**

Validation window:

- 2026-08-01 through 2026-08-21
- 15 Bloomberg Surveillance TV episodes discovered
- 15/15 episode pages available
- 15/15 published transcripts available
- 15/15 transcript API requests successful
- 15/15 transcripts contained segments, words, and word-level timestamps

Canonical episode URLs are discovered from official Omny RSS metadata.
Episode URLs must not be inferred from date-based slug conventions.

Detailed evidence:

`docs/validation/acquisition_gate_v0.1.md`

### Research Boundary

Bloomberg Surveillance commentary is research material, not a trading signal.

Guest views, reported facts, transcript-derived interpretations, and external
context must remain distinguishishable in downstream outputs.
