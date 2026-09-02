# Independent Market Research Pipeline

An evidence-grounded market research system for transforming long-form institutional market commentary into structured, traceable, and decision-relevant daily research.

## Explore the Project

🌐 **[Project Portfolio / Start Here](https://petal-chair-9d2.notion.site/Independent-Market-Research-Pipeline-Automated-Evidence-Grounded-Institutional-Market-Research-Sy-3c60169c5b49800bab2cde19b7b74cbb)**  
📺 **[Live Research Desk](https://sellina95.github.io/bloomberg-surveillance-research/)**
📊 **[Global Capital Flow Monitor](https://sellina95.github.io/Global-Capital-Flow-Monitor/)**

**Portfolio** explains the research problem and system design.  
**Live Research Desk** shows the resulting daily market research.  
This repository contains the methodology, validation framework, and reproducibility evidence behind the system.
**Global Capital Flow Monitor** is a separate cross-asset decision system translating macro, liquidity, credit, positioning, and market-risk signals into systematic risk-budget and portfolio-allocation decisions.  
This repository contains the methodology, validation framework, and reproducibility evidence behind the research pipeline.

## The Research Problem

Financial markets produce an enormous volume of macroeconomic views, policy interpretations, cross-asset perspectives, and institutional commentary every day.

The challenge is not simply collecting more information. It is determining:

> **Which narratives matter, which views recur or conflict across market participants, and can those conclusions be traced back to the original evidence?**

This project explores that problem by structuring individual market perspectives and their supporting evidence before synthesizing recurring themes, disagreements, and cross-asset implications into evidence-grounded daily research.

## How Source Material Becomes Independent Research

Bloomberg Surveillance is used as **source material**, not as a substitute for independent analysis. Views expressed by guests or market participants are not presented as the author's own market views.

The research pipeline transforms source material through a structured process:

**Source Material → Evidence Extraction → Research Analysis → Cross-Asset Interpretation → Independent Research Synthesis**

Individual claims are first linked to their supporting evidence and source location. The system then compares perspectives across market participants to identify **recurring narratives, areas of disagreement, market-relevant themes, and potential cross-asset implications**.

The resulting daily brief is therefore not intended to reproduce or simply summarize Bloomberg content. It is an **independent, source-grounded research synthesis** whose derived interpretations remain traceable to the underlying evidence.

## Why I Built This

My background spans **Computer Science, technology support and Global Markets Operations at Bank of America, and corporate credit analysis at ICBC**.

Across these experiences, I became increasingly interested in a problem at the intersection of markets and technology: **how can large volumes of market information be transformed into structured, traceable, and decision-relevant research?**

I built this project independently to explore that problem as a research system — combining automated information processing with source provenance, evidence grounding, validation controls, and institutional market research workflows.

The current implementation uses Bloomberg Surveillance as a research source. The objective is not to reproduce or republish the program, but to build an independent research workflow that can trace derived market interpretations back to their supporting source evidence.

> **Independent project:** This repository is not affiliated with or endorsed by Bloomberg. Bloomberg Surveillance is used solely as a source program for research. Public outputs contain paraphrased research synthesis; source transcripts and evidence-rich intermediate data are kept outside the public publication layer.

## Purpose

This project is designed to reduce the time required to review long-form
institutional market commentary while preserving the context needed for
independent research.

The system is intentionally designed as a research and evidence pipeline,
not as a trading or execution system.

Initial pipeline:

Date
→ Episode Discovery
→ Raw Transcript
→ Transcript Processing
→ Institutional Research Extraction
→ Daily Research Brief

---

## Research Principles

- Preserve raw source material separately from processed output.
- Distinguish FACT from GUEST VIEW and analyst interpretation.
- Preserve speaker/institution attribution where available.
- Preserve source provenance and timestamps where available.
- Do not treat commentary frequency as a trading signal.
- Do not connect outputs directly to production investment systems.
- External facts and transcript-derived statements must remain distinguishable.
- Research outputs must remain auditable against the underlying source.
- Automated failures must be explicit rather than silently producing incomplete
  research artifacts.

---

## v0.1 Goal

For a Bloomberg Surveillance broadcast date:

1. Discover the relevant episode.
2. Acquire an available transcript.
3. Preserve the raw transcript.
4. Produce a structured daily research brief.
5. Maintain enough provenance to audit the summary against the source.

The automated workflow may discover the latest valid broadcast rather than
requiring a manually supplied date.

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

**Status: CLOSED — PASS**

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

---

## Public Data Governance

This project maintains an explicit boundary between private source material
and public research outputs.

### Private Research Layer

The following materials are not part of the public publication surface:

- Raw or reconstructed source transcripts
- Guest transcript bodies
- Canonical transcript segment collections
- Evidence-rich research datasets and intermediate artifacts
- Source excerpts used internally for grounding and validation

These materials may be used internally by the research pipeline but are not
intended for public distribution.

### Public Research Layer

The public surface is limited to:

- Research code, architecture, and methodology
- Non-sensitive provenance and publication metadata
- Paraphrased source-derived synthesis
- Clearly labeled system research interpretation
- Validated English and Korean presentation artifacts

Public reports do not intentionally reproduce source transcript or evidence
text. Source-derived synthesis and system-generated interpretation are
explicitly distinguished in the presentation layer.

System-generated monitoring implications are research observations rather
than personalized investment recommendations or instructions to change a
portfolio position.

This is an independent research-engineering project and is not affiliated
with or endorsed by Bloomberg.

## Research Boundary

Bloomberg Surveillance commentary is research material, not a trading signal.

Guest views, reported facts, transcript-derived interpretations, and external
context must remain distinguishable in downstream outputs.

Research summaries must remain grounded in the supplied transcript.

For each key view:

- the claim must be supported by one or more transcript segments;
- the supporting segment IDs must originate from the supplied transcript;
- evidence text must be preserved from the source;
- unsupported claims must not be presented as transcript-derived facts;
- analytical market implications must remain distinguishable from what the guest
  explicitly said.

---

# Automated Daily Research Pipeline

The research pipeline can run automatically on a clean GitHub Actions runner
without relying on local development artifacts.

## Schedule

The production research workflow runs on weekdays at:

- **07:30 KST**
- **22:30 UTC on the previous day**

The workflow also supports manual execution through GitHub Actions
(`workflow_dispatch`).

GitHub Actions scheduling may experience minor execution delay around the
scheduled time.

---

## Runtime Flow

```text
Scheduled GitHub Actions
        ↓
Episode Discovery
        ↓
Surveillance Inventory Update
        ↓
Latest Valid Episode Selection
        ↓
Raw Transcript Ingestion
        ↓
Current-Video Chapter Metadata
        ↓
Canonical Transcript Dataset
        ↓
Guest Unit Construction
        ↓
Guest Transcript Extraction
        ↓
Evidence-Grounded Research Summaries
        ↓
Structured Research Dataset
        ↓
Daily Cross-Guest Research Report
        ↓
Markdown / TV Report
        ↓
Research Artifact Commit
```

---

## Runtime Data Contract

Each daily run is parameterized by:

- `SURVEILLANCE_DATE`
- `VIDEO_ID`

The production pipeline must acquire and process data for the actual episode
selected during the current run.

Source acquisition must not depend on historical probe artifacts or local-only
development files.

For example, the production daily pipeline must not depend on fixed artifacts
such as:

```text
data/raw/youtube_probe/serpapi_2026-08-14.json
data/raw/youtube_probe/supadata_2026-08-14.json
```

Instead:

- YouTube transcript data is acquired for the current `VIDEO_ID`.
- Chapter metadata is queried for the current `VIDEO_ID`.
- Raw inputs are stored under the current processing date.
- Canonical outputs are generated from current-run inputs.
- Historical probe artifacts remain research/development artifacts and are not
  production runtime dependencies.

---

## Episode Discovery

The discovery layer searches for Bloomberg Surveillance TV episodes and builds
a structured video inventory.

Current discovery uses:

- SerpApi YouTube search;
- Bloomberg Surveillance title filtering;
- video ID deduplication;
- publication date extraction;
- episode metadata preservation.

The discovery layer is responsible for finding candidate episodes.

The inventory layer is responsible for maintaining the reusable episode
inventory and selecting valid episodes for processing.

The system must not assume that a date-based URL slug or manually constructed
YouTube URL is valid.

---

## Raw Transcript Ingestion

The ingestion layer retrieves the transcript for the selected episode.

Runtime inputs:

- `SURVEILLANCE_DATE`
- `VIDEO_ID`
- `SUPADATA_API_KEY`

The raw transcript is stored separately from processed research outputs.

Example runtime artifact:

```text
data/raw/youtube/<DATE>/transcript.json
```

The ingestion layer must preserve the source response without applying research
interpretation.

---

## Canonicalization

The canonicalization layer combines:

```text
Current VIDEO_ID
        +
Current SerpApi chapter metadata
        +
Current Supadata transcript
        ↓
youtube_canonical_v0_2.json
```

Chapter metadata is queried for the current `VIDEO_ID`.

The canonicalization layer must not load historical fixed-date probe files.

The canonical dataset preserves:

- chapter metadata;
- chapter start times;
- transcript segments;
- segment timestamps;
- transcript text;
- chapter assignments;
- source attribution;
- transcript coverage;
- unassigned segment count.

A canonical build must fail or enter review when required source inputs are
missing.

---

## Guest Unit Construction

Guest interviews are represented as structured units derived from the canonical
episode structure.

Each guest unit preserves:

- unit ID;
- chapter;
- guest;
- title;
- start timestamp;
- end timestamp;
- transcript segments belonging to the unit.

Guest boundaries are treated as research data and should remain auditable
against the canonical transcript.

---

## Guest Transcript Extraction

Guest-level transcript artifacts are created from canonical transcript
segments.

The extraction layer does not generate new transcript content.

It selects the transcript segments belonging to each identified guest unit and
preserves them as the evidence base for downstream research generation.

---

## Evidence-Grounded Research Generation

Guest-level research summaries are generated from the supplied guest
transcript.

The research generation layer uses Gemini for structured research extraction.

The intended output separates:

1. What the guest said.
2. Why the view matters.
3. Market implication.

Maximum key views are constrained by the research schema.

Every key view must contain supporting transcript segment IDs.

Evidence is subsequently materialized from the canonical transcript rather than
being trusted solely from model-generated text.

Research generation failures are explicitly recorded.

Rate-limit handling and retry logic are implemented so that temporary model API
limits do not automatically convert into silent missing research units.

---

## Research Dataset

Validated guest research summaries are converted into a structured research
dataset.

The dataset provides a stable intermediate layer between individual guest
research and the daily cross-guest synthesis.

A research unit that fails completeness or evidence validation must not be
silently treated as a valid completed unit.

---

## Daily Research Report

The daily report synthesizes validated guest research units into a cross-guest
market research brief.

The report is intended to help identify:

- recurring macro themes;
- areas of disagreement;
- cross-asset implications;
- institutional perspectives;
- notable market risks;
- changes in narrative emphasis.

The report remains a research artifact and is not a trading instruction.

---

## TV Report

A human-readable TV-style HTML report is generated from the structured daily
research report.

Example artifact:

```text
data/processed/surveillance/<DATE>/
    daily_research_report_tv_v0_1.html
```

The TV report is a presentation layer over the validated research dataset and
does not constitute an independent source of truth.

---

# Validation Gates

The daily pipeline is expected to fail rather than silently continue when
required research inputs are unavailable.

Current validation layers include:

- required secret availability;
- episode discovery;
- inventory validity;
- transcript availability;
- canonical chapter/transcript coverage;
- guest-unit construction;
- guest transcript extraction;
- evidence-grounded research generation;
- research dataset completeness;
- daily report generation;
- final artifact verification.

A research summary that cannot be generated or grounded against the supplied
transcript remains explicitly marked for review or failure.

The pipeline should not report an operational PASS when required artifacts are
missing.

---

# Clean Runner Requirement

A successful local run is not sufficient evidence of production readiness.

The automated workflow is designed to validate the complete pipeline on a clean
GitHub Actions runner, where:

- local caches are unavailable;
- historical probe files are unavailable;
- developer-specific environment state is unavailable;
- only explicitly configured secrets are available;
- repository-tracked code and runtime-generated artifacts are available.

This design helps expose hidden dependencies before the research system is
relied upon for recurring daily use.

---

# Secrets

The automated workflow requires the following GitHub Actions secrets:

```text
SUPADATA_API_KEY
GEMINI_API_KEY
SERPAPI_API_KEY
```

Secrets are never stored in the repository.

They are injected only into the workflow steps that require them.

---

# Research / Production Boundary

This repository is a research system.

Automated outputs are research artifacts and must not be interpreted as
production trading instructions.

The pipeline is intentionally separated from investment execution systems.

Future integration into another research or investment project should preserve
the same source, provenance, validation, and research/production boundaries.

---

# Reusable Research Automation Architecture

The automation is designed as a reusable research pattern rather than a
Bloomberg-specific execution system.

The general architecture is:

```text
Discovery
    ↓
Point-in-Time Source Ingestion
    ↓
Canonicalization
    ↓
Validation
    ↓
Evidence-Grounded Research
    ↓
Structured Dataset
    ↓
Report / Artifact
```

This architecture can later be adapted to other research sources, including:

- macroeconomic releases;
- company earnings;
- financial news;
- central-bank communications;
- industry research;
- institutional commentary;
- other structured or semi-structured research sources.

The source-specific acquisition and parsing layers may change, but the
validation, provenance, evidence, research, and artifact layers should remain
conceptually separated.

This allows the research automation architecture to be reused without coupling
external information directly to production investment logic.

---

# Operational Governance

The repository distinguishes between:

## Research / Development

Used for:

- probes;
- source comparison;
- boundary experiments;
- parser development;
- schema experiments;
- validation tests;
- research methodology development.

## Automated Daily Runtime

Used for:

- current episode discovery;
- current-source ingestion;
- canonicalization;
- validated research extraction;
- daily report generation;
- recurring artifact production.

Development artifacts must not become hidden dependencies of the automated
runtime.

---

# Repository Structure

```text
.
├── .github/
│   └── workflows/
│       └── daily-surveillance.yml
│
├── data/
│   ├── raw/
│   │   └── youtube/
│   │       └── <DATE>/
│   │
│   └── processed/
│       └── surveillance/
│           └── <DATE>/
│
├── docs/
│   └── validation/
│
├── scripts/
│   ├── discover_surveillance_videos_v0_3.py
│   ├── update_surveillance_inventory_v0_1.py
│   ├── run_latest_surveillance_v0_1.py
│   ├── youtube_daily_runner_v0_3.py
│   ├── generate_research_summaries_gemini_v0_2.py
│   ├── build_research_dataset_v0_1.py
│   ├── build_daily_research_report_v0_1.py
│   └── render_daily_research_report_v0_1.py
│
└── tests/
    ├── run_youtube_daily_ingestion_v0_1.py
    ├── build_youtube_canonical_v0_2.py
    ├── build_guest_units_v0_3.py
    └── build_guest_transcripts_v0_1.py
```

---

# Status

**Research prototype with automated daily pipeline.**

Current automated workflow:

- **GitHub Actions:** ACTIVE
- **Scheduled execution:** Weekdays 07:30 KST
- **Manual execution:** SUPPORTED
- **Clean-runner execution:** VALIDATED
- **Runtime legacy probe dependency:** REMOVED
- **Evidence-grounded guest research:** ACTIVE
- **Daily research report:** ACTIVE
- **TV report:** ACTIVE

The system remains a research workflow and is not connected directly to
production investment execution.
