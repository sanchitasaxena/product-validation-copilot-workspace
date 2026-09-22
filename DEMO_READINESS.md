# Tuesday Demo Readiness

## Recommendation

**READY for an internal coworker demo, with the limitations below stated explicitly.**

The QA path creates a usable XLSX workbook. Research paths now create validated JSON sources plus reviewable DOCX deliverables; survey output also includes a Microsoft Forms Quick Import package.

## Verified demo paths

| Path | Result | Output |
|---|---|---|
| PRD/RFC to QA bug bash | Passed | XLSX, normalized QA JSON, validation JSON, review summary |
| PRD/RFC to persona/JTBD/CUJ review | Passed | Research context JSON and audience-proposal JSON |
| PRD/RFC to moderated testing guide | Passed | Validated JSON and DOCX with CUJ-mapped tasks |
| PRD/RFC to discovery survey | Passed | JSON, polished DOCX, Forms Quick Import DOCX, CSV, and instructions |
| Research context to Monday.com answers | Passed | JSON, Markdown, and DOCX answer sheets |

## Tests run

```text
python -m unittest discover -s tests -v
12 tests passed
```

The suite covers all six generated DOCX files, the QA XLSX, Forms package files, prose extraction, schema validation, and approval boundaries.

Office validation:

```text
officecli validate /tmp/product-validation-tuesday-demo/qa/registry-approval-workflow.bug-bash-tracker.xlsx
Validation passed: no errors found.

officecli validate examples/source-document-intake/sources/permissions-notes.docx
Validation passed: no errors found.
```

The automated suite validates the generated QA XLSX and every generated research DOCX with `officecli`. All demo commands completed successfully and their adjacent JSON validation reports contained zero errors.

## Recommended five-minute demonstration

1. Show the synthetic feature brief and API notes.
2. Run the QA command from the README.
3. Open the generated XLSX and show `Scenarios`, `Bug_Tracker`, `Summary`, and `Validation`.
4. Show the synthetic research PRD and its explicit Persona/JTBD/CUJ statements.
5. Run the moderated testing-guide command.
6. Compare `research-context.normalized.json`, `testing-guide.docx`, and `review-summary.md`.
7. If time permits, show the survey Forms package or `monday-request.docx`; explain that neither workflow publishes or submits a form.

## Manual preparation before Tuesday

- Run `./setup.sh` on the demo machine.
- Confirm `python3`, `openpyxl`, and `jsonschema` are available.
- Install `officecli` before demonstrating research DOCX generation or DOCX intake.
- Use the bundled synthetic catalog with `--include-synthetic-catalog`; do not imply it is real catalog data.
- Pre-open VS Code and an XLSX viewer.
- Use a clean output directory under `/tmp`.
- Avoid demonstrating raw transcript synthesis or live Monday.com form filling.

## Remaining risks

- Normal-prose extraction uses conservative heuristics and requires review.
- Catalog matching uses token similarity and can miss paraphrases.
- The repository does not include a real Target Audience Catalog snapshot.
- Microsoft Forms requires Quick Import plus manual completion of ratings, branching, and required settings.
- The live Monday.com field mapping could not be verified in the automated browser, so the answer draft uses the workspace's known intake fields.
- `synthesis` packages pre-structured findings but does not synthesize raw evidence.

## Privacy

The five demo paths run locally and make no network API calls. Generated outputs can reproduce source-document content and paths; use only the bundled synthetic inputs during the demo.

## GitHub publishing note

Before making the repository public, exclude or review:

- `generators/xlsx/out/`
- imported legacy trackers and outputs
- any real catalog snapshots
- internal URLs, names, transcripts, customer data, or absolute local paths

The bundled Tuesday demo inputs are synthetic and suitable for an internal demonstration.
