# Research Module

The research module supports product research workflows that produce evidence for product, design, and roadmap decisions.

## Workflows

- Create research plans
- Create discovery guides
- Create moderated or unmoderated testing guides
- Hand off raw transcript synthesis to Product Designer Bootstrap or Automation UXR
- Draft answers for the Monday.com UXR request form

## Target Audience modes

Research artifacts should use catalog-grounded mode when official persona/JTBD/CUJ context exists.

Discovery artifacts should use discovery mode when audience context is unknown or is the subject of the research.

## Human-in-the-loop requirements

Humans approve research method, recruiting criteria, Monday.com answers, and official Target Audience Catalog updates.

## Executable V1 builders

The workflow builder creates schema-shaped draft artifacts and never implies approval. It supports
two input modes: a pre-authored research context JSON, or PRD/RFC source documents ingested directly.

### From a PRD/RFC (source documents)

`tools/build_research_context_from_sources.py` extracts persona/JTBD/CUJ/decision/requirement/research-question
candidates from labeled sections and conservative ordinary-prose rules in Markdown, text, or DOCX PRDs/RFCs, then cross-references each persona/JTBD/CUJ
candidate against local Target Audience Catalog fixtures. Each candidate is labeled either
`source-backed` (matches an existing catalog claim) or `proposed-catalog-update` (new, from the
source document, not yet approved). See `../examples/research-source-intake/` for a full worked
example, including a case where the PRD reuses an existing JTBD/CUJ and introduces a new one.

```bash
python3 tools/run_research_workflow.py \
  --workflow discovery-guide \
  --source-doc path/to/prd.md \
  --source-doc path/to/rfc.docx \
  --product-area "<product area>" \
  --feature "<feature, if known>" \
  --output-dir out/
```

`--workflow` may be `plan`, `testing-guide`, `unmoderated-test`, `discovery-guide`,
`discovery-survey`, or `monday-request`. This
produces `research-context.normalized.json`, `audience-proposal.json`, `<workflow>.json`,
`<workflow>.docx`, `<workflow>.validation.json`, and `review-summary.md` — the summary calls out exactly which
JTBD/CUJ/persona claims are new proposals requiring human review before being treated as catalog
truth.

### From a pre-authored research context

```bash
python3 tools/run_research_workflow.py \
  --workflow plan \
  --input tests/fixtures/research-context.json \
  --output /tmp/research-plan.json

python3 tools/run_research_workflow.py \
  --workflow monday-request \
  --input tests/fixtures/research-context.json \
  --output /tmp/monday-request.json
```

Use `--approve` only after a human has reviewed a Monday answer draft; it means approved for copying,
not submitted. Every artifact is validated
automatically and a `<output>.validation.json` is written alongside it.

## What is not yet automated

- No SharePoint/Microsoft Graph/Confluence/Google Docs link ingestion — only local files.
- Discovery surveys produce a polished DOCX and a Microsoft Forms Quick Import package; they do not create or publish a hosted form.
- Raw transcript/note/survey-response synthesis is handled by Product Designer Bootstrap or Automation UXR.
- Extraction uses labels/headings and conservative prose heuristics, not semantic understanding; inferred and uncertain claims require review.
- Catalog matching uses token-overlap similarity, not embeddings.
