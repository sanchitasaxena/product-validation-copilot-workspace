# Generate Bug Bash Tracker Workflow

## Inputs

- Feature documentation
- Prior QA tracker if available
- Feature areas
- Interfaces under test
- Release or bug bash goal

## Steps

1. Read source documents.
2. Read `qa/scenario-style-guide.md` and use the original RAUC style corpus as the scenario-writing pattern.
3. Extract functional behavior, limits, permissions, state changes, error states, and interface coverage.
4. Generate scenarios in engineering-authored style.
5. Mark each scenario as source-backed, inferred, regression, edge case, or exploratory.
6. Validate rows against `qa/validation-rules.md` and `generators/xlsx/bug-bash-tracker.rules.json`.
7. Create tracker-ready rows.
8. Ask for engineer review before final use.

## Required output

- Scenarios tab
- Bug Tracker tab
- Summary tab
- Validation tab
- Optional validation warnings JSON

## Generator requirements

The future XLSX generator should add summary support for:

- pass/fail rate by feature,
- unresolved critical/high issues,
- failed scenarios without linked bugs,
- orphan bugs,
- owner workload,
- blocked dependency chains.

## Current implementation

Use the first XLSX generator:

```bash
python3 generators/xlsx/generate_bug_bash_tracker.py \
  --input generators/xlsx/examples/rauc_sample_qa_context.json \
  --output generators/xlsx/out/RAUC_Bug_Bash_Tracker.xlsx \
  --validation-report generators/xlsx/out/RAUC_Bug_Bash_Tracker.validation.json
```

The input should follow the QA context shape defined in `schemas/qa-context.schema.json`.
