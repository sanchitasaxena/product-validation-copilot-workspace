# Testing Guide Prompt

Use this prompt for moderated and unmoderated research testing guides.

## Requirements

- Confirm target audience or explicitly use discovery mode.
- Use research task wording, not QA scenario wording.
- Include participant criteria.
- Map tasks to JTBD/CUJ when available.
- Keep success criteria observable.
- Include facilitator notes and post-task probes.

## Do not use when

If the request is internal QA or bug bash, route to the QA scenario generator instead.

## Executable path

```bash
python3 tools/run_research_workflow.py \
  --workflow testing-guide \
  --source-doc path/to/prd.md \
  --product-area "<product area>" \
  --output-dir out/
```

Tasks are drawn from catalog-grounded/PRD-sourced CUJs when available; otherwise a placeholder task is drafted for human completion. Every generated task requires human review before use with participants.
