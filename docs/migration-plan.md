# Migration Plan

## From product-research-qa-toolkit

Move or adapt:

- Research judgment and quality gates from the README and skills.
- Existing generated artifacts into examples.
- QA tracker generator concepts into the future XLSX generator.
- RAUC tracker examples into the QA module.

Rewrite:

- Bob-specific README language.
- Install flow.
- Generator architecture.

Rebuild:

- Target Audience Resolver.
- Schema-driven generators.
- Chat-based Office editing workflows.
- UXR intake workflow.

Quarantine or delete from the new workspace:

- Checked-in `node_modules`.
- RAUC-only assumptions inside generic generator files.

## From pocket-product-designer-bootstrap

Borrow:

- Front-door routing pattern.
- Context package template pattern.
- Modular setup philosophy.
- Local search/indexing concept.
- Persona/JTBD/CUJ framing.

Adapt:

- Frame/Map/Design/Ship into Resolve/Plan/Produce/Review/Submit.

## From automation-uxr

Borrow:

- Evidence discipline.
- One-question-at-a-time input collection.
- Editable intermediate draft pattern.
- Synthesis structure.

Adapt carefully:

- DOCX-to-markdown conversion. Preserve source fidelity and do not use aggressive spellcheck/normalization by default.

