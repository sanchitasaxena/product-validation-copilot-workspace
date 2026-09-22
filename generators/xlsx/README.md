# XLSX Generators and Importers

This folder contains the first working QA Excel workflow:

1. Import an existing engineering-authored bug bash tracker into QA context JSON.
2. Generate a normalized bug bash tracker workbook from that QA context JSON.

## Import an existing RAUC-style tracker

From the workspace root:

```bash
python3 generators/xlsx/import_bug_bash_tracker.py \
  --input "../RAUC Example/rauc context/RAUC_Bug_Tracker_2026_copy.xlsx" \
  --output generators/xlsx/out/RAUC_Bug_Tracker_2026.qa-context.json
```

The importer expects:

- a `Scenarios` sheet with `ID`, `Feature`, `Scenario Description`, `Prerequisites`, `Expected Result`, `Testers`, and `Status`;
- a `Bug_Tracker` sheet with `Date Reported`, `Type`, `Feature`, `Description`, `Severity`, `Owner`, `Link to screenshot`, `Status`, and optional `Column1` notes/category.

The importer preserves the engineering-authored language. It does not rewrite weak or messy rows into polished research language.

## Import behavior

- Resolves cached or formula-based scenario IDs.
- Normalizes shorthand references like `T104` to `T-104` for structured linking.
- Keeps original descriptions unchanged.
- Extracts scenario dependencies from prerequisites.
- Infers broad scenario type only for tracker filtering (`UI`, `API`, `CLI`, `Permissions`, `Setup`, etc.).
- Moves URL-shaped owner-column drift into `evidenceLinks`.
- Skips placeholder bug rows with no description and records them in `importMetadata.skippedRows`.
- Annotates missing legacy fields in `notes` and `validationWarnings`.

## Generate the normalized workbook

```bash
python3 generators/xlsx/generate_bug_bash_tracker.py \
  --input generators/xlsx/out/RAUC_Bug_Tracker_2026.qa-context.json \
  --output generators/xlsx/out/RAUC_Bug_Tracker_2026.imported.generated.xlsx \
  --validation-report generators/xlsx/out/RAUC_Bug_Tracker_2026.imported.validation.json
```

The generated workbook adds:

- richer scenario and bug columns;
- scenario-to-bug links;
- status and issue-type validation;
- summary and release-readiness views;
- a `Validation` tab that makes source cleanup visible.

## Expected cleanup from the original RAUC tracker

The original tracker is intentionally treated as real workflow data, not a sanitized demo. A successful import can still produce validation warnings or errors when the source has missing expected results, orphan bug rows, unresolved high-severity issues without owners, or failed scenarios without linked bugs.
