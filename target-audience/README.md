# Target Audience Module

This module manages persona, JTBD, and CUJ context for product validation workflows.

## Modes

### Catalog-grounded mode

Use when a target audience record exists in the Target Audience Catalog or another approved source.

### Discovery mode

Use when the target audience, JTBD, or CUJ is unknown, outdated, disputed, or the subject of the research.

## Local snapshot first

V1 should use a local indexed snapshot of the Target Audience Catalog. This is safer than starting with SharePoint or Microsoft Graph integration.

## Local resolver

The v1 local resolver is `resolve_target_audience.py`. It reads local JSON fixtures from:

- `target-audience/source/`
- `target-audience/index/`
- `target-audience/examples/`

It does not call SharePoint or Microsoft Graph.

Example:

```bash
python3 target-audience/resolve_target_audience.py \
  --feature "Registry artifact approval workflow" \
  --product-area "HCP Terraform Registry" \
  --persona "platform admin" \
  --artifact qa \
  --confirm-best-match \
  --output target-audience/out/synthetic-registry-artifact-approval.resolved.json
```

The resolver outputs:

- `resolutionStatus`: `confirmed`, `needs-confirmation`, or `discovery-required`
- `mode`: `catalog-grounded` or `discovery`
- selected local source reference
- match score, confidence, and reasons
- audience context with persona/JTBD/CUJ claims
- ambiguity and missing-context notes
- `generatorContext.targetAudienceSummary`, which can be copied into QA or research context JSON

Use `--confirm-best-match` only when the operator agrees the top local match is the correct context. Without confirmation, downstream workflows should keep `humanReviewRequired: true`.

If no local fixture clears the match threshold, the resolver returns discovery mode and clearly labels persona/JTBD/CUJ claims as `to-be-discovered`.

## Future refresh

SharePoint or Microsoft Graph refresh can be added later. Refreshes should be reviewed before local index records are replaced.

## Reference for PRD/RFC intake

`tools/build_research_context_from_sources.py` treats this catalog as the reference set for existing
JTBD/CUJ/persona claims. When a PRD/RFC introduces a new JTBD or CUJ, it is compared against these
fixtures; a match is labeled `source-backed`, and anything without a match is labeled
`proposed-catalog-update` and requires human review before being added here.

## Confidence

Use:

- high: direct catalog or strong source match,
- medium: source-backed but not official,
- low: inferred or ambiguous.

Human confirmation is required for ambiguous matches and all proposed catalog updates.
