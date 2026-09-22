# Synthetic QA Source Document Intake Example

This example demonstrates the Project QA Bug Bash Pilot Workflow starting from three synthetic source formats:

- `sources/feature-brief.md`
- `sources/api-notes.txt`
- `sources/permissions-notes.docx`

No confidential data, SharePoint content, or official Target Audience Catalog data is used.

## Run

```bash
python3 tools/run_qa_bug_bash_workflow.py \
  --feature "Registry artifact approval workflow" \
  --product-area "HCP Terraform Registry" \
  --persona "platform admin" \
  --source-doc examples/source-document-intake/sources/feature-brief.md \
  --source-doc examples/source-document-intake/sources/api-notes.txt \
  --source-doc examples/source-document-intake/sources/permissions-notes.docx \
  --output-dir examples/source-document-intake/workflow-output \
  --confirm-audience-match
```

Use `--force` to replace deterministic outputs from a previous run.

## Source format

Explicit scenario blocks provide the most reliable extraction:

```text
Feature area: Approval policy API
Scenario: Create an approval rule through API
Prerequisites: Organization usage control is enabled
Expected result: API returns the created rule with a stable identifier
Interface: API
```

Markdown headings can replace `Feature area:`. Requirement bullets under headings containing terms such as `requirements`, `behavior`, `permissions`, `API`, `CLI`, `limits`, or `edge cases` are accepted as fallback inputs.

Fallback scenarios are marked `inferred`. All scenarios created from source documents require engineering review.

## Outputs

The `workflow-output/` folder contains:

- resolved target audience JSON;
- source intake report;
- draft and normalized QA context JSON;
- generated XLSX bug bash tracker;
- validation JSON;
- markdown review summary.

The example produces eight scenarios: seven from explicit source blocks and one inferred from an edge-case requirement bullet.
