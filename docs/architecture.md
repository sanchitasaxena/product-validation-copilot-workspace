# Architecture

Product Validation Copilot Workspace is organized around structured context, source grounding, and Copilot-guided workflows.

## Layers

1. Copilot workflow layer
   - Prompts and operating rules for routing, audience resolution, QA, research, synthesis handoff, and intake.
2. Context package layer
   - Structured research and QA context packages that capture decisions, sources, assumptions, and missing information.
3. Schema layer
   - JSON schemas that define target audience records, QA scenarios, bug reports, research plans, synthesis reports, and intake.
4. Module layer
   - Target Audience, QA, Research, Generators, Examples, and Legacy.
5. Artifact layer
   - XLSX QA trackers plus DOCX research deliverables and Microsoft Forms transfer packages rendered from structured JSON.

## Design principle

The artifact is not the source of truth. Context packages and schema-backed data are the source of truth. XLSX and DOCX files are validated renderings; survey packages additionally include a simplified Forms Quick Import DOCX and structured JSON/CSV.

## Validation tracks

```text
Product Validation
├── Research evidence
└── Internal QA evidence
```

Research evidence supports product, design, and user understanding decisions. Internal QA evidence supports release readiness and product behavior validation.
