# Research Source Intake Example

This is a synthetic, non-confidential end-to-end reference run demonstrating how a PRD/RFC becomes a
reviewable research artifact, with new JTBD/CUJ candidates cross-checked against the local Target
Audience Catalog.

## Input

- `sources/registry-audit-trail-prd.md`: a synthetic PRD containing a persona, two JTBDs, two CUJs,
  a decision statement, and two research questions. One JTBD/CUJ pair intentionally duplicates the
  bundled `sources/target-audience-catalog.synthetic.json` fixture; the
  other JTBD/CUJ pair is new and does not exist in any local catalog fixture.

## Command

```bash
python3 tools/run_research_workflow.py \
  --workflow discovery-guide \
  --source-doc examples/research-source-intake/sources/registry-audit-trail-prd.md \
  --product-area "HCP Terraform Registry" \
  --feature "Registry artifact approval workflow" \
  --catalog-source examples/research-source-intake/sources/target-audience-catalog.synthetic.json \
  --include-synthetic-catalog \
  --output-dir examples/research-source-intake/workflow-output
```

## Output

- `research-context.normalized.json`: extracted decision, research questions, and audience claims,
  each labeled `source-backed` (matched an existing catalog fixture) or `proposed-catalog-update`
  (new, from the PRD, not yet approved).
- `audience-proposal.json`: a target-audience-shaped file a human can review and, if approved,
  promote into `target-audience/source/` as a new catalog entry.
- `discovery-guide.json`: the schema-backed discovery guide draft.
- `discovery-guide.validation.json`: validation result (0 errors expected).
- `review-summary.md`: human-readable summary distinguishing existing vs. new JTBD/CUJ and next
  review actions.

## What this proves

- PRDs/RFCs can be ingested directly (no manually hand-authored context JSON required).
- New JTBDs/CUJs introduced by a PRD are detected and flagged for catalog review rather than
  silently treated as established audience truth.
- The same source documents can drive either a `testing-guide` (moderated/unmoderated usability
  tasks mapped to CUJs) or a `discovery-guide` (open-ended assumption-validation questions) by
  changing only `--workflow`.

## Limits

- Extraction uses explicit labels/headings plus conservative normal-prose heuristics. Inferred and
  uncertain claims preserve source excerpts and require review.
- Synthetic catalog data is ignored unless `--include-synthetic-catalog` is explicitly supplied.
- Matching against the catalog uses token-overlap similarity, not embeddings; paraphrased JTBDs/CUJs
  may need a human to confirm they are the same underlying claim.
- Nothing here is submitted or treated as approved automatically. `humanReviewRequired` is always
  `true`, and new proposals must be reviewed before being added to the Target Audience Catalog.
