# Generators

This folder contains schema-driven DOCX and XLSX generators.

## V1 status

V1 is schema-first. The first implemented generator is the XLSX bug bash tracker generator, with an importer for existing RAUC-style bug bash trackers.

## Planned generators

- XLSX bug bash tracker importer: `xlsx/import_bug_bash_tracker.py`
- XLSX bug bash tracker generator: `xlsx/generate_bug_bash_tracker.py`
- DOCX research plan generator
- DOCX discovery guide generator
- DOCX moderated testing guide generator
- DOCX synthesis report generator
- DOCX UXR intake package generator

## Rules

- Generators should consume structured schema data.
- Templates should be separate from content.
- RAUC-specific content belongs in examples, not generator code.
- Office document edits should be proposed and reviewed before final application.

## XLSX bug bash tracker contract

The improved bug bash tracker generator uses:

- `schemas/qa-context.schema.json`
- `schemas/qa-scenario.schema.json`
- `schemas/bug-report.schema.json`
- `qa/scenario-style-guide.md`
- `qa/validation-rules.md`
- `generators/xlsx/bug-bash-tracker.rules.json`

The generator should preserve engineering-authored scenario style while adding validation, normalized fields, dependencies, evidence links, and release-readiness summaries.

## Import an existing tracker

From the workspace root:

```bash
python3 generators/xlsx/import_bug_bash_tracker.py \
  --input "../RAUC Example/rauc context/RAUC_Bug_Tracker_2026_copy.xlsx" \
  --output generators/xlsx/out/RAUC_Bug_Tracker_2026.qa-context.json
```

The importer preserves source wording, resolves formula-based scenario IDs where possible, moves URL-shaped owner-column drift into evidence links, and annotates missing legacy fields in `notes` / `validationWarnings`.

## Generate a tracker

From the workspace root:

```bash
python3 generators/xlsx/generate_bug_bash_tracker.py \
  --input generators/xlsx/examples/rauc_sample_qa_context.json \
  --output generators/xlsx/out/RAUC_Bug_Bash_Tracker.xlsx \
  --validation-report generators/xlsx/out/RAUC_Bug_Bash_Tracker.validation.json
```

The generated workbook includes:

- `Scenarios`
- `Bug_Tracker`
- `Summary`
- `Validation`

Validation warnings are written both into the workbook and, when requested, to JSON.

## Reusable workflow runner

The recommended pilot entry point is:

```bash
python3 tools/run_qa_bug_bash_workflow.py \
  --feature "<feature>" \
  --product-area "<product area>" \
  --qa-context "<qa-context.json>" \
  --output-dir "<output-dir>"
```

The runner orchestrates local target audience resolution, optional tracker import, QA context normalization, context validation, XLSX generation, generator validation JSON, and a markdown review summary. Research artifact builders live in `../tools/run_research_workflow.py`.

Use `generators/xlsx/generate_bug_bash_tracker.py` directly only when you already have a validated QA context JSON file.
