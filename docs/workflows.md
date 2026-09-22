# Workflows

## Request routing

Every Copilot interaction starts by identifying the request type:

- target audience resolution,
- discovery-mode research,
- research plan generation,
- interview or testing guide generation,
- internal QA tracker generation,
- existing QA XLSX import/review,
- structured synthesis packaging,
- Monday.com UXR request answer drafting.

## Standard flow

```text
Route request
-> Gather minimum context
-> Resolve audience if needed
-> Create context package
-> Generate or review artifact
-> Show assumptions and source references
-> Ask for human confirmation
-> Apply edits or export artifact
```

## Human confirmation required

- Ambiguous persona/JTBD/CUJ matches
- Discovery vs validation mode changes
- Research method selection
- copying Monday.com answers or submitting the form
- Office document edits
- Proposed Target Audience Catalog updates
