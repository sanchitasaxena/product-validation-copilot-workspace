# QA Tracker Validation Rules

These rules define the validation contract for the future XLSX bug bash tracker generator and reviewer.

## Scenario row rules

### Required fields

Every non-empty scenario row must include:

- ID
- Feature
- Scenario Description
- Expected Result
- Status

Prerequisites and Testers may be blank for setup or unassigned scenarios, but should be flagged as warnings when missing.

### ID rules

- IDs must use `T-###` format.
- IDs must be unique.
- Dependency references must point to existing scenario IDs.
- Dependency separators such as `/`, `,`, and whitespace should be parsed.

### Style rules

Descriptions should match engineering-authored bug bash style:

- concise,
- action-oriented,
- functional/system behavior focused,
- not written as a user story,
- not written as a moderated research task.

Flag descriptions that begin with:

- `Verify that`
- `As a user`
- `You are`
- `How would you`
- `Tell me about`

These may be valid research tasks but should not be default QA scenario wording.

### Expected result rules

Expected results should be observable pass/fail conditions. Flag expected results that are:

- empty,
- only subjective,
- only a UI path,
- missing when status is Passed or Failed.

### Status rules

Accepted normalized statuses:

- Pending
- In Progress
- Passed
- Failed
- Blocked

Icons may be displayed in Excel, but validation should normalize them.

## Bug row rules

### Required fields

Every non-empty bug row should include:

- Type
- Description
- Status

Warnings should be raised for missing:

- Date Reported
- Feature
- Severity
- Owner
- Evidence link
- Scenario ID

### Issue type rules

Allowed types:

- Bug
- Friction
- Improvement

### Severity rules

Allowed severities:

- 1-Critical
- 2-High
- 3-Medium
- 4-Low
- Unrated

Missing severity is a warning. Missing severity on unresolved bugs is a stronger warning.

### Scenario linkage rules

- If a bug description includes `T-###`, parse and store it as Scenario ID.
- If a scenario is Failed, it should have at least one linked bug row or an explicit note explaining why not.
- If a bug row has no scenario ID, classify it as `orphan`, `exploratory`, or `no-scenario`.

## Evidence rules

Evidence links may include:

- Slack threads
- Box files
- Screenshots
- Jira issues
- Logs
- GitHub/GitHub Enterprise links
- Other URLs

Warnings:

- critical/high unresolved bugs without evidence,
- bugs with broken or malformed URL text,
- screenshot links placed in owner fields due to column drift.

## Summary rules

The generator should produce or support summaries for:

- scenario count by feature area,
- pass/fail/pending rate by feature area,
- failed scenarios without bugs,
- bugs by type,
- bugs by severity,
- open critical/high bugs,
- owner workload,
- orphan bugs,
- blocked dependency chains,
- release-readiness risks.

## Release-readiness rules

Copilot may summarize release readiness but must not make the release decision. Humans decide launch readiness.

Flag as high risk:

- any unresolved `1-Critical` bug,
- failed scenario without linked bug or owner,
- core feature area with low pass rate,
- dependency chain blocked near setup scenarios,
- many orphan bugs without scenario mapping.

