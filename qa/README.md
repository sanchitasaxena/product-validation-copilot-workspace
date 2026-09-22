# QA Module

The QA module supports internal QA, bug bash planning, scenario generation, tracker review, and release-readiness summaries.

Internal QA is a first-class product validation workflow, not a research sub-feature.

## Canonical style source

The original RAUC bug tracker is the canonical engineering-authored scenario style corpus.

## Issue types

- Bug: product behavior is broken.
- Friction: product behavior works but creates avoidable tester/user friction.
- Improvement: suggested enhancement or polish item.

## Core tracker relationship

Scenarios define expected behavior. Bug rows capture failures, frictions, or improvements discovered while testing. Where possible, bug rows should link back to scenario IDs.

## Implemented assets

- `scenario-style-guide.md`: human-readable style guide derived from the original RAUC tracker.
- `examples/rauc-original/style-corpus.md`: representative scenario, prerequisite, expected-result, and bug-row patterns.
- `validation-rules.md`: human-readable validation contract.
- `../generators/xlsx/bug-bash-tracker.rules.json`: machine-readable rules used by the XLSX generator.

## First generator

The XLSX generator is available at:

```text
../generators/xlsx/generate_bug_bash_tracker.py
```

It consumes QA context JSON and produces a workbook with:

- `Scenarios`
- `Bug_Tracker`
- `Summary`
- `Validation`

Sample input:

```text
../generators/xlsx/examples/rauc_sample_qa_context.json
```

## Project QA Bug Bash Pilot Workflow

The reusable pilot workflow lives at:

```text
../tools/run_qa_bug_bash_workflow.py
```

It supports three starting points:

- an existing RAUC-style tracker;
- a QA context JSON file.
- one or more Markdown, text, or DOCX feature documents.

It produces:

- resolved target audience JSON;
- normalized QA context JSON;
- XLSX bug bash tracker;
- validation JSON;
- markdown review summary.

This workflow is not RAUC-specific. RAUC is only the reference style corpus for concise, engineering-authored scenarios.

Before a tracker is used with a team, engineering should review:

- inferred scenarios;
- missing expected results filled with review placeholders;
- failed scenarios without linked bugs;
- orphan or exploratory bug rows;
- unresolved critical/high issues.

## Source document intake

`../tools/build_qa_context_from_sources.py` extracts local source documents into a draft QA context.

Supported formats:

- Markdown (`.md`, `.markdown`)
- UTF-8 text (`.txt`)
- Word (`.docx`) through local `officecli` text extraction

Explicit scenario blocks provide the best fidelity. Requirement bullets are a fallback and are marked `inferred`. The intake records source paths, hashes, extraction methods, source references, and scenario counts.

This is deterministic extraction, not semantic understanding of arbitrary prose. Missing coverage must be identified during engineering review.
