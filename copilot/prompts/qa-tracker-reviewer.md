# QA Tracker Reviewer Prompt

Use this prompt to review an existing QA or bug bash tracker.

## Review goals

Check for:

- duplicate scenario IDs,
- missing feature areas,
- missing expected results,
- invalid dependencies,
- failed scenarios without linked bug rows,
- bug rows without scenario IDs,
- missing severity,
- missing owner,
- missing evidence links,
- unresolved critical/high issues,
- stale or inconsistent statuses.
- scenario descriptions that drift into UX research task wording,
- inferred scenarios without review labels,
- screenshot/evidence links likely placed in the wrong column,
- blocked dependency chains.

## Output

Provide:

- release-readiness summary,
- issues requiring cleanup,
- scenario coverage gaps,
- bug tracker hygiene issues,
- recommended next actions.

Do not rewrite engineering-authored scenarios unless asked. If editing, preserve the original style.

Use `qa/validation-rules.md` and `generators/xlsx/bug-bash-tracker.rules.json` as the review contract.
