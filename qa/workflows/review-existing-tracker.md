# Review Existing Tracker Workflow

Use this workflow to inspect an existing QA tracker.

## Import first

For RAUC-style Excel trackers, convert the workbook into QA context JSON before reviewing:

```bash
python3 generators/xlsx/import_bug_bash_tracker.py \
  --input "../RAUC Example/rauc context/RAUC_Bug_Tracker_2026_copy.xlsx" \
  --output generators/xlsx/out/RAUC_Bug_Tracker_2026.qa-context.json
```

Then run the generated JSON through the tracker generator to create a normalized workbook with `Summary` and `Validation` tabs.

```bash
python3 generators/xlsx/generate_bug_bash_tracker.py \
  --input generators/xlsx/out/RAUC_Bug_Tracker_2026.qa-context.json \
  --output generators/xlsx/out/RAUC_Bug_Tracker_2026.imported.generated.xlsx \
  --validation-report generators/xlsx/out/RAUC_Bug_Tracker_2026.imported.validation.json
```

Do not treat validation warnings as importer failures by default. The original tracker contains real-world cleanup needs, and the point of import is to preserve that evidence while making issues reviewable.

## Checks

- Duplicate scenario IDs
- Missing expected results
- Missing prerequisites for dependent scenarios
- Failed scenarios without bug rows
- Bug rows without scenario references
- Missing severity/owner/evidence
- Unresolved critical or high issues
- Feature areas with high failure rate
- Legacy column drift, such as evidence links placed in owner fields
- Formula-based IDs that need to be resolved before reuse

## Output

Provide a release-readiness summary and cleanup checklist.
