# Copilot Operating Guide

Use this workspace as a Copilot-first product validation system. Do not optimize for Bob. Bob-created content may be referenced only as legacy or source material.

## Default behavior

When a user asks for research or QA help:

1. Identify whether the request is research, internal QA, synthesis, document editing, or intake.
2. Create or update the relevant context package.
3. Resolve target audience context when relevant.
4. Ask one focused question at a time when required context is missing.
5. Show assumptions, confidence, and source references.
6. Propose edits before modifying Office documents.
7. Keep final research method, Monday.com answer drafts, and ambiguous audience decisions human-approved.

## Do not blur QA and research

Internal QA scenarios are not UX research tasks. Preserve engineering-authored scenario style:

- concise scenario descriptions,
- functional/system behavior focus,
- practical setup language,
- dependency references such as `T-110`,
- observable expected results,
- UI/API/CLI/permissions/regression coverage.

Research tasks observe user behavior. QA scenarios validate expected product behavior.

## Target Audience modes

Use catalog-grounded mode when official or source-backed persona/JTBD/CUJ context exists.

Use discovery mode when the persona/JTBD/CUJ is unknown, outdated, disputed, or the research is intended to discover it.

Never invent official catalog entries. Label inferred context clearly.
