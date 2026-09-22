# QA Scenario Generator Prompt

Use this prompt to generate internal QA or bug bash scenarios from feature documentation.

## Style requirement

Follow the engineering-authored scenario style from the original RAUC bug tracker.

Write scenarios as concise functional coverage, not UX research tasks.

Use the detailed style rules in `qa/scenario-style-guide.md` and the examples in `qa/examples/rauc-original/style-corpus.md`.

## Inputs

- Feature name
- Product area
- RFC/PRD/user guide/implementation docs
- Prior bug tracker or bug bash data
- Known feature areas
- Interfaces under test: UI, API, CLI, permissions, data behavior, regression

## Output columns

- ID
- Feature
- Scenario Description
- Prerequisites
- Expected Result
- Testers
- Status
- Scenario Type
- Source
- Depends On
- Notes

## Generator handoff

When the scenario set is ready, structure it as QA context JSON compatible with `schemas/qa-context.schema.json`, then run:

```bash
python3 generators/xlsx/generate_bug_bash_tracker.py \
  --input <qa-context.json> \
  --output <bug-bash-tracker.xlsx> \
  --validation-report <validation-report.json>
```

## Rules

- Scenario descriptions should be short.
- Expected results must be observable.
- Prerequisites should describe setup state or dependency IDs.
- Mark source-backed, inferred, regression, edge case, or exploratory scenarios.
- Do not over-polish engineering phrasing.
- Do not convert QA rows into user stories or moderated research prompts.
- Preserve functional feature-area groupings.
- Parse and preserve dependencies such as `T-110` and `T-115/T-120`.
- Add `Needs Engineering Review` when a scenario is inferred from incomplete documentation.
- Require engineer review before final tracker use.
