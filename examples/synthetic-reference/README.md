# Synthetic Reference Example

This folder is a synthetic reference run for the Product Validation Copilot Workspace.

It does not use SharePoint, Microsoft Graph, real Target Audience Catalog content, or confidential project data.

## Files

- `resolved-target-audience.synthetic.json`: local Target Audience Resolver output for a made-up registry artifact approval workflow.
- `qa-context.synthetic.json`: QA context JSON with the resolver's `generatorContext` merged in.
- `bug-bash-tracker.synthetic.xlsx`: generated bug bash tracker workbook.
- `validation.synthetic.json`: generator validation report.

## What this proves

- A local audience fixture can be resolved into a generator-ready context block.
- That context block can be carried into QA context JSON.
- The XLSX generator can produce a tracker with `Scenarios`, `Bug_Tracker`, `Summary`, and `Validation` sheets.
- The generated workbook can pass Office/OpenXML validation.

## What this does not prove

- It does not prove real Target Audience Catalog retrieval works.
- It does not prove SharePoint or Microsoft Graph integration works.
- It does not prove PM, design, UXR, or QA users can operate the workflow without help.
- It does not prove source documents such as PRDs, RFCs, DOCX files, or tickets can be ingested automatically.
- It does not prove generated scenarios have been approved by engineering.

## Known validation warning

The synthetic bug tracker intentionally includes one orphan/exploratory improvement row. The validation report should contain one warning that the row has no linked scenario ID.
