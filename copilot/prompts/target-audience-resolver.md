# Target Audience Resolver Prompt

Use this prompt to resolve or discover persona, JTBD, and CUJ context.

## Modes

### Catalog-grounded mode

Use when official or source-backed target audience context exists in the Target Audience Catalog, RFCs, PRDs, prior research, or user-provided source docs.

### Discovery mode

Use when audience/JTBD/CUJ context is missing, outdated, disputed, or the purpose of the research is to discover it.

## Required output

Produce:

- mode,
- product area,
- primary persona,
- secondary personas,
- JTBDs,
- CUJs,
- source references,
- confidence,
- ambiguities,
- missing context,
- allowed artifacts,
- blocked or discouraged artifacts,
- human review requirements.

## Local resolver CLI

For v1, prefer the local resolver before inventing audience context:

```bash
python3 target-audience/resolve_target_audience.py \
  --feature "<feature>" \
  --product-area "<product area>" \
  --persona "<role/persona if known>" \
  --artifact <qa|research|uxr-intake|document-edit> \
  --output target-audience/out/<name>.resolved.json
```

If the user confirms the match, rerun with `--confirm-best-match` or set the resolved block only after explicit human confirmation.

Use `generatorContext.targetAudienceSummary` in QA and research context packages. Keep the full resolver output as source evidence.

## Rules

- Do not invent official catalog entries.
- Label inferred context.
- Ask for confirmation when multiple matches exist.
- In discovery mode, allow discovery artifacts and block validation artifacts that require known audience context.
- Do not use SharePoint or Microsoft Graph in v1 resolver runs.
