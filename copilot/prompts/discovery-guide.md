# Discovery Guide Prompt

Use this prompt when persona, JTBD, CUJ, workflow, or mental model context is unknown, disputed, or
the explicit subject of the research (a "discovery survey" or discovery interview guide).

## Requirements

- Label every assumption as `source-backed`, `to-be-discovered`, `proposed-catalog-update`, or
  `user-provided-assumption`. Never present an assumption as confirmed catalog fact.
- Write open-ended questions that surface behavior and mental models rather than usability task
  wording.
- Include synthesis prompts for promoting validated findings into proposed catalog updates.
- If the request instead has known, catalog-grounded audience context and a defined workflow to
  validate, route to the testing guide prompt.

## Executable path

```bash
python3 tools/run_research_workflow.py \
  --workflow discovery-guide \
  --source-doc path/to/prd.md \
  --source-doc path/to/rfc.docx \
  --product-area "<product area>" \
  --output-dir out/
```

This ingests the PRD/RFC, cross-references any persona/JTBD/CUJ candidates against the local Target
Audience Catalog, and produces a schema-backed discovery guide draft plus a review summary that
separates existing catalog matches from new proposals. See `examples/research-source-intake/` for a
worked example.

## Do not use when

If audience context is already catalog-grounded and the goal is to validate a known workflow, use
the testing guide prompt instead.
