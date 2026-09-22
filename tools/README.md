# Tools

This folder contains workflow CLIs for the Product Validation Copilot Workspace.

## Validate context JSON

```bash
python3 tools/validate_context.py \
  --input generators/xlsx/examples/synthetic_registry_artifact_approval_qa_context.json \
  --type qa-context
```

Supported types:

- `target-audience`
- `qa-context`
- `qa-scenario`
- `bug-report`
- `research-context`
- `research-plan`
- `synthesis-report`
- `uxr-intake`
- `testing-guide`
- `unmoderated-test`
- `discovery-guide`
- `discovery-survey`
- `monday-request`
- `discovery-guide`
- `testing-guide`
- `auto`

Validation covers all first-class context types, required fields, enums, cross-artifact QA relationships, and human-approval gates. It exits non-zero on errors.

## Build research artifacts from a PRD/RFC

`build_research_context_from_sources.py` extracts persona/JTBD/CUJ/decision/requirement/research-question candidates from labeled sections and ordinary prose in Markdown, text, or DOCX PRDs/RFCs. It preserves source excerpts, labels extraction confidence, and cross-references audience claims against local Target Audience Catalog fixtures.

```bash
python3 tools/run_research_workflow.py \
  --workflow discovery-guide \
  --source-doc path/to/prd.md \
  --product-area "<product area>" \
  --feature "<feature, if known>" \
  --output-dir out/
```

See `examples/research-source-intake/` for a full worked example. Demo-ready workflows are `plan`, `testing-guide`, `unmoderated-test`, `discovery-guide`, `discovery-survey`, and `monday-request`. Raw synthesis is intentionally delegated to Product Designer Bootstrap or Automation UXR.

## Build research artifacts from a pre-authored context

`run_research_workflow.py --input <research-context.json> --output <path>` creates a validated JSON source and a reviewable DOCX. `monday-request` also writes Markdown and never submits the form. `discovery-survey` additionally writes a Forms Quick Import DOCX, structured JSON/CSV, and import instructions. Every JSON artifact is validated automatically and a `<output>.validation.json` is written alongside it.

## Run Project QA Bug Bash Pilot Workflow

Use an existing QA context JSON:

```bash
python3 tools/run_qa_bug_bash_workflow.py \
  --feature "Registry artifact approval workflow" \
  --product-area "HCP Terraform Registry" \
  --persona "platform admin" \
  --qa-context generators/xlsx/examples/synthetic_registry_artifact_approval_qa_context.json \
  --output-dir examples/project-qa-bug-bash-pilot \
  --confirm-audience-match
```

Or use an existing RAUC-style tracker:

```bash
python3 tools/run_qa_bug_bash_workflow.py \
  --feature "<feature>" \
  --product-area "<product area>" \
  --existing-tracker "<path-to-existing-tracker.xlsx>" \
  --output-dir "<output-dir>"
```

Or start from one or more Markdown, text, or DOCX source documents:

```bash
python3 tools/run_qa_bug_bash_workflow.py \
  --feature "<feature>" \
  --product-area "<product area>" \
  --source-doc "<feature-brief.md>" \
  --source-doc "<api-notes.txt>" \
  --source-doc "<permissions.docx>" \
  --output-dir "<output-dir>"
```

Source documents may use explicit `Feature area`, `Scenario`, `Prerequisites`, `Expected result`, and `Interface` labels. Requirement bullets are supported as a lower-confidence fallback. Every drafted scenario is marked for engineering review.

The workflow produces:

- `resolved-target-audience.json`
- `qa-context.normalized.json`
- `<feature>.bug-bash-tracker.xlsx`
- `validation.json`
- `review-summary.md`

Source-document runs also produce:

- `source-intake.json`
- `draft.qa-context.json`

RAUC is not required by this workflow. RAUC is only a reference corpus for engineering-authored QA scenario style.
