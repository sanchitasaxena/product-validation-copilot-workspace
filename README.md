# Product Validation Copilot Workspace

A local, Copilot-friendly toolkit for turning product documents into reviewable QA and research artifacts.

The workspace has two separate paths:

```text
PRD / RFC
├── QA → functional scenarios → bug-bash XLSX → release-readiness summary
└── Research → audience/JTBD/CUJ review → study materials or Monday.com answer draft
```

It does not submit forms, run research, or make product decisions automatically. Generated material is a draft until a human approves it.

## What it creates today

| Output | Format | Status |
|---|---|---|
| QA bug-bash tracker with Scenarios, Bug Tracker, Summary, and Validation sheets | XLSX | End-to-end |
| Normalized QA context and source-intake record | JSON | End-to-end |
| Persona, JTBD, and CUJ candidates cross-checked against a local catalog snapshot | JSON | End-to-end for labeled and normal-prose sources |
| Research plan | JSON source plus DOCX | Implemented; human review required |
| Moderated usability-testing guide with tasks mapped to CUJs | JSON source plus DOCX | Implemented; human review required |
| Unmoderated test materials | JSON source plus DOCX | Implemented; human review required |
| Discovery interview guide | JSON source plus DOCX | Implemented; human review required |
| Discovery survey | JSON source, polished DOCX, Forms Quick Import DOCX, CSV, and instructions | Implemented; import and human review required |
| Monday.com UXR request answers | JSON, Markdown, and DOCX answer sheet | Implemented as a draft; never submitted |

Raw transcript synthesis, live document-link ingestion, Microsoft Forms publication, and Monday.com form submission are not implemented.

## Requirements

- Python 3.9+
- `officecli` for DOCX input/output and Office validation

Install Python dependencies:

```bash
cd product-validation-copilot-workspace
./setup.sh
source .venv/bin/activate
```

`setup.sh` installs the pinned packages in `requirements.txt`. If `officecli` is missing, setup succeeds but warns that DOCX workflows are unavailable.

## Five-minute demo

The repository includes synthetic, non-confidential inputs. The commands below write outputs to `/tmp`.

### 1. Create a QA bug-bash spreadsheet

```bash
python3 tools/run_qa_bug_bash_workflow.py \
  --feature "Registry approval workflow" \
  --product-area "HCP Terraform Registry" \
  --source-doc examples/source-document-intake/sources/feature-brief.md \
  --source-doc examples/source-document-intake/sources/api-notes.txt \
  --output-dir /tmp/product-validation-demo/qa
```

Open:

```text
/tmp/product-validation-demo/qa/registry-approval-workflow.bug-bash-tracker.xlsx
```

The workbook contains:

- `Scenarios`: functional, engineering-style test scenarios
- `Bug_Tracker`: bugs, friction, and improvements
- `Summary`: status, issue, owner, and release-risk information
- `Validation`: blocking errors and review warnings

### 2. Create moderated usability-testing material

```bash
python3 tools/run_research_workflow.py \
  --workflow testing-guide \
  --source-doc examples/research-source-intake/sources/registry-audit-trail-prd.md \
  --product-area "HCP Terraform Registry" \
  --feature "Registry artifact approval workflow" \
  --catalog-source examples/research-source-intake/sources/target-audience-catalog.synthetic.json \
  --include-synthetic-catalog \
  --output-dir /tmp/product-validation-demo/moderated
```

Review:

```text
/tmp/product-validation-demo/moderated/testing-guide.json
/tmp/product-validation-demo/moderated/testing-guide.docx
/tmp/product-validation-demo/moderated/review-summary.md
```

The testing tasks are mapped to CUJs extracted from the PRD. The bundled catalog is explicitly synthetic and is enabled only for this demo.

### 3. Create a discovery survey draft

```bash
python3 tools/run_research_workflow.py \
  --workflow discovery-survey \
  --source-doc examples/research-source-intake/sources/registry-audit-trail-prd.md \
  --product-area "HCP Terraform Registry" \
  --catalog-source examples/research-source-intake/sources/target-audience-catalog.synthetic.json \
  --include-synthetic-catalog \
  --output-dir /tmp/product-validation-demo/discovery
```

Review:

```text
/tmp/product-validation-demo/discovery/discovery-survey.json
/tmp/product-validation-demo/discovery/discovery-survey.docx
/tmp/product-validation-demo/discovery/discovery-survey.forms-import.docx
/tmp/product-validation-demo/discovery/discovery-survey.forms.json
/tmp/product-validation-demo/discovery/discovery-survey.forms.csv
/tmp/product-validation-demo/discovery/discovery-survey.forms-import.md
```

### 4. Draft Monday.com UXR request answers

```bash
python3 tools/run_research_workflow.py \
  --workflow monday-request \
  --input tests/fixtures/research-context.json \
  --output /tmp/product-validation-demo/monday-request.json
```

Review and copy from:

```text
/tmp/product-validation-demo/monday-request.md
/tmp/product-validation-demo/monday-request.docx
```

The answer sheet identifies missing information to ask the requester. It never opens or submits the form. Because the live Monday form could not be inspected reliably in the automated browser, the exact live field mapping is marked `unverified-live-form`.

## Inputs

### QA source documents

Supported local formats:

- Markdown (`.md`, `.markdown`)
- UTF-8 text (`.txt`)
- Word (`.docx`, extracted locally with `officecli`)

Best results use explicit labels:

```text
Feature area: Approval rules
Scenario: Create an approval rule
Prerequisites: Usage control is enabled
Expected result: The saved rule appears in the approval list
Interface: UI
```

Requirement bullets are accepted as a lower-confidence fallback. Every source-derived QA scenario requires engineering review.

### Research source documents

Supported local formats are Markdown, UTF-8 text, and DOCX. Best results use:

```text
Persona: Platform admin
JTBD: When ..., I need ..., so that ...
CUJ: Admin reviews and updates approval rules.
Decision: Whether the workflow is understandable.
Research Question: Can administrators recover from an error?
```

The extractor recognizes labels/headings and applies conservative rules to ordinary prose. It preserves source excerpts and marks results as `explicit`, `inferred`, or `uncertain`. Inferred and uncertain claims must be reviewed; missing context is never invented.

### Target Audience Catalog

By default, research intake checks only:

```text
target-audience/source/
target-audience/index/
```

Synthetic files in `target-audience/examples/` are never treated as approved catalog data. For real use, export reviewed catalog records into `source/` or `index/`, or pass one or more:

```bash
--catalog-source /path/to/approved-catalog.json
```

PRD/RFC claims are labeled:

- `source-backed`: similar to an eligible catalog claim; still requires confirmation
- `proposed-catalog-update`: no catalog match; a candidate to validate, not an approved update

Matching uses token overlap, so paraphrases can be missed or matched incorrectly. Review the match text and similarity score.

## Other research commands

Replace `WORKFLOW` with one of:

```text
plan
testing-guide
unmoderated-test
discovery-guide
discovery-survey
monday-request
```

Then run:

```bash
python3 tools/run_research_workflow.py \
  --workflow WORKFLOW \
  --source-doc /path/to/prd.md \
  --source-doc /path/to/rfc.docx \
  --product-area "Product area" \
  --output-dir /tmp/product-validation-output
```

Raw transcript and note synthesis is intentionally out of scope. Use Product Designer Bootstrap or Automation UXR for synthesis, then bring reviewed findings back into the product workflow as needed.

### Microsoft Forms

The discovery-survey workflow creates a simplified Word file for Microsoft Forms **Quick Import**. In Forms, choose **Quick Import**, upload `discovery-survey.forms-import.docx`, select **Form**, and review the conversion.

Quick Import supports titles/subtitles, multiple choice, and open text. Ratings, branching, required settings, and complex question types must be completed manually from the adjacent Forms JSON/CSV and instructions. The workspace never publishes or distributes the form.

## Human-review boundaries

Human review is required before:

- using generated QA scenarios in a live bug bash
- treating a persona/JTBD/CUJ match as confirmed
- treating a new JTBD/CUJ candidate as catalog data
- using research questions or tasks with participants
- copying Monday.com answers into the form
- publishing, distributing, or submitting any external form

`--approve` on `monday-request` means **approved for copying**, not submitted.

## Tests

Run all tests:

```bash
make test
```

Run quick smoke checks:

```bash
make smoke
```

Validate an Office artifact:

```bash
officecli validate /path/to/workbook.xlsx
officecli validate /path/to/document.docx
```

The test suite covers the QA XLSX path, labeled and normal-prose audience extraction, catalog opt-in safeguards, CUJ-mapped moderated tasks, DOCX generation, Microsoft Forms packaging, Monday.com draft behavior, validation, and missing-source failure handling.

## Privacy and security

- Processing is local; the tools do not call SharePoint, Microsoft Graph, Monday.com, or another external API.
- Source paths and SHA-256 hashes are written to intake metadata.
- Generated files may repeat sensitive PRD/RFC content. Review outputs before sharing or committing them.
- Do not commit internal transcripts, private URLs, customer information, credentials, or proprietary catalog exports to a public repository.
- The bundled examples are synthetic. Generated legacy files under `generators/xlsx/out/` should not be published without review.

## Known limitations

- No URL ingestion for Google Docs, Confluence, SharePoint, or other document links
- Prose extraction is heuristic rather than semantic and may miss or over-classify claims
- No raw transcript, survey-response, or note synthesis
- No live Microsoft Forms creation, publication, or distribution; Quick Import and manual review are required
- No live Monday.com field inspection, filling, or submission
- No real Target Audience Catalog snapshot is included
- No graphical interface; workflows are local CLIs and Copilot prompts
- Python dependencies are pinned, but `officecli` is an external prerequisite for DOCX workflows

## Troubleshooting

**DOCX extraction fails**

Install `officecli` and verify:

```bash
officecli --version
officecli validate your-file.docx
```

**No JTBDs or CUJs were extracted**

Use explicit `JTBD:` and `CUJ:` labels for the most reliable result. Normal-prose extraction is conservative; inspect `missingContext`, source excerpts, and extraction status before adding claims manually.

**Everything is marked as a new proposal**

Provide an approved local catalog snapshot with `--catalog-source`. Synthetic fixtures require both `--catalog-source` and `--include-synthetic-catalog`.

**The workflow exits after writing an artifact**

Read the adjacent `*.validation.json`. Blocking validation errors produce a non-zero exit code.

## Repository layout

```text
copilot/          Copilot routing prompts and context templates
docs/             Architecture, governance, and workflow notes
examples/         Synthetic reference inputs and outputs
generators/docx/  Research DOCX generator
generators/xlsx/  QA tracker importer and XLSX generator
qa/               QA style rules and workflows
research/         Research workflow guidance
schemas/          JSON Schema contracts
target-audience/  Local catalog snapshot and resolver
tests/            Unit and end-to-end demo tests
tools/            Workflow CLIs
```

See `DEMO_READINESS.md` for the current Tuesday-demo verification results and release recommendation.
