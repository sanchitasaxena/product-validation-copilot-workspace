#!/usr/bin/env python3
"""
Run the reusable Project QA Bug Bash Pilot Workflow.

Inputs:
- an existing RAUC-style tracker, a QA context JSON file, OR source documents;
- feature/product area details;
- optional local target audience query fields.

Outputs:
- resolved-target-audience.json
- qa-context.normalized.json
- bug-bash-tracker.xlsx
- validation.json
- review-summary.md
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


WORKSPACE = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
RESOLVER = WORKSPACE / "target-audience" / "resolve_target_audience.py"
IMPORTER = WORKSPACE / "generators" / "xlsx" / "import_bug_bash_tracker.py"
GENERATOR = WORKSPACE / "generators" / "xlsx" / "generate_bug_bash_tracker.py"
VALIDATOR = WORKSPACE / "tools" / "validate_context.py"
SOURCE_INTAKE = WORKSPACE / "tools" / "build_qa_context_from_sources.py"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=WORKSPACE, text=True, capture_output=True, check=False)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {result.returncode}: {' '.join(command)}")
    return result


def slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or "qa-bug-bash"


def count_generator_validation(path: Path) -> tuple[int, int, list[dict[str, str]]]:
    if not path.exists():
        return 0, 0, []
    data = load_json(path)
    errors = data.get("errors", [])
    warnings = data.get("warnings", [])
    issues = data.get("issues", errors + warnings)
    return len(errors), len(warnings), issues


def bug_scenario_ids(bug: dict[str, Any]) -> list[str]:
    ids = list(bug.get("scenarioIds") or [])
    if bug.get("scenarioId"):
        ids.append(str(bug["scenarioId"]))
    ids.extend(re.findall(r"T-\d+", str(bug.get("description", ""))))
    return sorted(set(ids))


def normalize_imported_legacy_context(qa_context: dict[str, Any]) -> None:
    for scenario in qa_context.get("scenarios", []):
        if not isinstance(scenario, dict):
            continue
        if not scenario.get("expectedResult"):
            scenario["expectedResult"] = "Review required: source tracker did not include an expected result."
            scenario["needsEngineeringReview"] = True
            scenario.setdefault("styleWarnings", [])
            scenario["styleWarnings"].append("Expected result was missing in imported source tracker.")
            existing_notes = scenario.get("notes", "")
            scenario["notes"] = (
                f"{existing_notes} Workflow normalization added a review placeholder for missing expected result."
            ).strip()
        if not scenario.get("status"):
            scenario["status"] = "Pending"
            scenario["needsEngineeringReview"] = True


def build_summary_markdown(
    args: argparse.Namespace,
    audience: dict[str, Any],
    qa_context: dict[str, Any],
    validation_path: Path,
    workbook_path: Path,
    normalized_path: Path,
) -> str:
    validation_errors, validation_warnings, generator_issues = count_generator_validation(validation_path)
    scenarios = qa_context.get("scenarios", [])
    bugs = qa_context.get("bugs", [])
    failed_scenarios = [scenario.get("id", "(missing ID)") for scenario in scenarios if scenario.get("status") == "Failed"]
    orphan_bugs = [
        bug.get("id", "(missing ID)")
        for bug in bugs
        if not bug_scenario_ids(bug) or bug.get("orphanClassification") in {"orphan", "no-scenario", "exploratory"}
    ]
    unresolved_critical_high = [
        bug.get("id", "(missing ID)")
        for bug in bugs
        if bug.get("status") in {"New", "In Progress", "QA"} and bug.get("severity") in {"1-Critical", "2-High"}
    ]
    scenarios_needing_review = [
        scenario.get("id", "(missing ID)") for scenario in scenarios if scenario.get("needsEngineeringReview")
    ]
    target_summary = audience.get("generatorContext", {}).get("targetAudienceSummary", {})
    if args.existing_tracker:
        base_input = "existing tracker"
    elif args.source_doc:
        base_input = "source documents"
    else:
        base_input = "QA context JSON"

    next_actions = []
    if audience.get("humanReviewRequired"):
        next_actions.append("Confirm or replace the resolved target audience before treating the context as official.")
    if validation_errors:
        next_actions.append("Fix validation errors before using the tracker for a live bug bash.")
    if unresolved_critical_high:
        next_actions.append("Assign owners and release decisions for unresolved critical/high issues.")
    if orphan_bugs:
        next_actions.append("Review orphan/exploratory bugs and link them to scenarios where appropriate.")
    if scenarios_needing_review:
        next_actions.append("Have engineering review and approve all drafted or inferred scenarios before the bug bash.")
    if not next_actions:
        next_actions.append("Ask engineering to review scenario coverage and approve the tracker for use.")

    issue_lines = "\n".join(
        f"- {item.get('severity', 'warning')}: {item.get('area', item.get('path', 'unknown'))} "
        f"{item.get('rowId', '')} - {item.get('message', '')}".rstrip()
        for item in generator_issues[:25]
    ) or "- None"

    return f"""# Project QA Bug Bash Review Summary

## Workflow inputs

- Feature: {qa_context.get('feature', args.feature)}
- Product area: {qa_context.get('productArea', args.product_area)}
- Base input: {base_input}
- RAUC-specific workflow: No. RAUC is only a style/reference example.

## Target audience resolution

- Status: {audience.get('resolutionStatus')}
- Mode: {audience.get('mode')}
- Data status: {target_summary.get('dataStatus', audience.get('match', {}).get('dataStatus'))}
- Confidence: {audience.get('match', {}).get('confidence')}
- Human review required: {audience.get('humanReviewRequired')}
- Selected source: {audience.get('selectedSource')}
- Primary persona: {target_summary.get('primaryPersona', '')}

## Generated outputs

- Resolved audience: resolved-target-audience.json
- Normalized QA context: {normalized_path.name}
- XLSX tracker: {workbook_path.name}
- Validation JSON: {validation_path.name}
{"- Source intake report: source-intake.json" if args.source_doc else ""}

## Tracker summary

- Scenario count: {len(scenarios)}
- Bug/issue count: {len(bugs)}
- Validation errors: {validation_errors}
- Validation warnings: {validation_warnings}
- Failed scenarios: {", ".join(failed_scenarios) or "None"}
- Orphan/exploratory bugs: {", ".join(orphan_bugs) or "None"}
- Unresolved critical/high bugs: {", ".join(unresolved_critical_high) or "None"}
- Scenarios needing engineering review: {", ".join(scenarios_needing_review) or "None"}

## Validation details

{issue_lines}

## Next review actions

{chr(10).join(f"- {action}" for action in next_actions)}

## Limits of this workflow

- This workflow does not call SharePoint or Microsoft Graph.
- Source-document extraction is deterministic; arbitrary prose may not produce complete coverage.
- Explicit source scenario blocks provide better fidelity than requirement-bullet fallback.
- Drafted scenarios require engineering review.
- Human review is still required before using generated or imported scenarios with a team.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Project QA Bug Bash Pilot Workflow.")
    parser.add_argument("--feature", required=True, help="Feature under test.")
    parser.add_argument("--product-area", required=True, help="Product area.")
    parser.add_argument("--persona", help="Optional persona or role for local target audience matching.")
    parser.add_argument("--qa-context", help="Path to existing QA context JSON.")
    parser.add_argument("--existing-tracker", help="Path to existing RAUC-style tracker XLSX.")
    parser.add_argument(
        "--source-doc",
        action="append",
        help="Markdown, text, or DOCX source document. Repeatable and mutually exclusive with other base inputs.",
    )
    parser.add_argument("--output-dir", required=True, help="Directory for workflow outputs.")
    parser.add_argument("--confirm-audience-match", action="store_true", help="Confirm the best local audience match.")
    parser.add_argument("--force", action="store_true", help="Overwrite deterministic workflow outputs if they already exist.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_modes = sum([bool(args.qa_context), bool(args.existing_tracker), bool(args.source_doc)])
    if input_modes != 1:
        print("Provide exactly one base input: --qa-context, --existing-tracker, or one or more --source-doc.", file=sys.stderr)
        sys.exit(2)

    output_dir = Path(args.output_dir).expanduser()
    if not output_dir.is_absolute():
        output_dir = WORKSPACE / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    resolved_path = output_dir / "resolved-target-audience.json"
    normalized_path = output_dir / "qa-context.normalized.json"
    workbook_path = output_dir / f"{slug(args.feature)}.bug-bash-tracker.xlsx"
    validation_path = output_dir / "validation.json"
    review_path = output_dir / "review-summary.md"
    imported_path = output_dir / "imported.qa-context.json"
    draft_path = output_dir / "draft.qa-context.json"
    intake_path = output_dir / "source-intake.json"
    deterministic_outputs = [resolved_path, normalized_path, workbook_path, validation_path, review_path]
    if args.existing_tracker:
        deterministic_outputs.append(imported_path)
    if args.source_doc:
        deterministic_outputs.extend([draft_path, intake_path])
    existing_outputs = [path for path in deterministic_outputs if path.exists()]
    if existing_outputs and not args.force:
        print(
            "Refusing to overwrite existing workflow outputs. Use --force to replace:\n"
            + "\n".join(f"- {path}" for path in existing_outputs),
            file=sys.stderr,
        )
        sys.exit(2)

    resolve_command = [
        PYTHON,
        str(RESOLVER),
        "--feature",
        args.feature,
        "--product-area",
        args.product_area,
        "--artifact",
        "qa",
        "--output",
        str(resolved_path),
    ]
    if args.persona:
        resolve_command.extend(["--persona", args.persona])
    if args.confirm_audience_match:
        resolve_command.append("--confirm-best-match")
    run_command(resolve_command)
    run_command([PYTHON, str(VALIDATOR), "--input", str(resolved_path), "--type", "target-audience"])

    if args.existing_tracker:
        run_command(
            [
                PYTHON,
                str(IMPORTER),
                "--input",
                args.existing_tracker,
                "--output",
                str(imported_path),
                "--feature",
                args.feature,
                "--product-area",
                args.product_area,
            ]
        )
        qa_context = load_json(imported_path)
        normalize_imported_legacy_context(qa_context)
    elif args.source_doc:
        intake_command = [
            PYTHON,
            str(SOURCE_INTAKE),
            "--feature",
            args.feature,
            "--product-area",
            args.product_area,
            "--output",
            str(draft_path),
            "--intake-report",
            str(intake_path),
            "--audience-grounding-required",
        ]
        for source in args.source_doc:
            intake_command.extend(["--source", source])
        run_command(intake_command)
        qa_context = load_json(draft_path)
    else:
        qa_context = load_json(Path(args.qa_context).expanduser().resolve())

    audience = load_json(resolved_path)
    qa_context["feature"] = qa_context.get("feature") or args.feature
    qa_context["productArea"] = qa_context.get("productArea") or args.product_area
    qa_context.update(audience.get("generatorContext", {}))
    source_docs = list(qa_context.get("sourceDocs") or [])
    source_docs.append(str(resolved_path.relative_to(WORKSPACE) if resolved_path.is_relative_to(WORKSPACE) else resolved_path))
    qa_context["sourceDocs"] = sorted(set(source_docs))
    qa_context["workflowMetadata"] = {
        "workflow": "project-qa-bug-bash-pilot",
        "baseInput": "existing-tracker" if args.existing_tracker else ("source-documents" if args.source_doc else "qa-context"),
        "reusableWorkflow": True,
        "raucSpecific": False,
    }
    write_json(normalized_path, qa_context)

    run_command([PYTHON, str(VALIDATOR), "--input", str(normalized_path), "--type", "qa-context"])
    run_command(
        [
            PYTHON,
            str(GENERATOR),
            "--input",
            str(normalized_path),
            "--output",
            str(workbook_path),
            "--validation-report",
            str(validation_path),
        ]
    )

    review_path.write_text(
        build_summary_markdown(args, audience, qa_context, validation_path, workbook_path, normalized_path),
        encoding="utf-8",
    )

    print("Workflow complete:")
    print(f"- {resolved_path}")
    print(f"- {normalized_path}")
    print(f"- {workbook_path}")
    print(f"- {validation_path}")
    print(f"- {review_path}")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
