#!/usr/bin/env python3
"""
Extract Markdown, text, and DOCX feature sources into a draft QA context.

The builder prefers explicit scenario blocks:

    ## Feature area
    - Scenario: Create an approval rule
      Prerequisites: Usage control is enabled
      Expected result: Rule saves and appears in the approval list
      Interface: UI

Requirement bullets in behavior/requirements sections are accepted as a
fallback, but are marked inferred. Every produced scenario requires
engineering review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


WORKSPACE = Path(__file__).resolve().parents[1]
SUPPORTED_SUFFIXES = {".md", ".markdown", ".txt", ".docx"}
FIELD_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(feature area|scenario|prerequisites?|expected result|interface|scenario type|depends on|testers?|notes?)\s*:\s*(.*)$",
    re.IGNORECASE,
)
HEADING_RE = re.compile(r"^\s*#{1,6}\s+(.+?)\s*$")
BULLET_RE = re.compile(r"^\s*[-*]\s+(.+?)\s*$")
DEPENDENCY_RE = re.compile(r"T-\d+")
OFFICECLI_PATH_RE = re.compile(r"^\[.*\]\s*")
GENERIC_HEADINGS = {
    "feature brief",
    "overview",
    "requirements",
    "functional requirements",
    "expected behavior",
    "behaviors",
    "source",
    "notes",
}
FALLBACK_SECTION_WORDS = {
    "requirement",
    "behavior",
    "workflow",
    "permission",
    "api",
    "cli",
    "edge",
    "limit",
    "error",
}


@dataclass
class ExtractedSource:
    path: Path
    display_path: str
    source_type: str
    extraction_method: str
    text: str
    warnings: list[str]


def workspace_display_path(path: Path) -> str:
    try:
        return str(path.relative_to(WORKSPACE))
    except ValueError:
        return str(path)


def load_text(path: Path) -> ExtractedSource:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ValueError(f"Unsupported source format '{suffix}' for {path}. Supported: .md, .markdown, .txt, .docx.")
    if suffix == ".docx":
        result = subprocess.run(
            ["officecli", "view", str(path), "text", "--max-lines", "10000"],
            cwd=WORKSPACE,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip()
            raise ValueError(f"Could not extract DOCX text from {path}: {detail}")
        text = "\n".join(OFFICECLI_PATH_RE.sub("", line) for line in result.stdout.splitlines()).strip()
        method = "officecli-view-text"
    else:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"{path} is not UTF-8 text.") from exc
        method = "utf-8-text"
    if not text.strip():
        raise ValueError(f"Source document is empty: {path}")
    return ExtractedSource(
        path=path,
        display_path=workspace_display_path(path),
        source_type=suffix.lstrip("."),
        extraction_method=method,
        text=text,
        warnings=[],
    )


def normalized_field(value: str) -> str:
    value = value.lower().strip()
    if value.startswith("prerequisite"):
        return "prerequisites"
    if value == "expected result":
        return "expectedResult"
    if value in {"interface", "scenario type"}:
        return "scenarioType"
    if value == "depends on":
        return "dependsOn"
    if value == "feature area":
        return "featureArea"
    if value.startswith("tester"):
        return "testers"
    return value


def scenario_type(value: str, text: str) -> str:
    explicit = value.strip().lower()
    mapping = {
        "ui": "UI",
        "api": "API",
        "cli": "CLI",
        "permissions": "Permissions",
        "permission": "Permissions",
        "data": "Data",
        "regression": "Regression",
        "edge case": "Edge Case",
        "setup": "Setup",
        "exploratory": "Exploratory",
    }
    if explicit in mapping:
        return mapping[explicit]
    lowered = text.lower()
    if " cli" in f" {lowered}" or "command line" in lowered:
        return "CLI"
    if "api" in lowered or "endpoint" in lowered:
        return "API"
    if any(word in lowered for word in ["permission", "role", "admin only", "unauthorized", "forbidden"]):
        return "Permissions"
    if any(word in lowered for word in ["maximum", "minimum", "limit", "duplicate", "empty", "invalid"]):
        return "Edge Case"
    return "UI"


def concise_description(requirement: str) -> str:
    text = requirement.strip().rstrip(".")
    replacements = [
        (r"^(?:platform\s+)?admins?\s+(?:can|must|should)\s+", ""),
        (r"^(?:users?|operators?|members?)\s+(?:can|must|should)\s+", ""),
        (r"^the\s+system\s+(?:can|must|should)\s+", ""),
        (r"^the\s+(?:ui|api|cli)\s+(?:can|must|should)\s+", ""),
        (r"^(?:can|must|should)\s+", ""),
    ]
    for pattern, replacement in replacements:
        updated = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        if updated != text:
            text = updated
            break
    if text:
        text = text[0].upper() + text[1:]
    words = text.split()
    if len(words) > 14:
        text = " ".join(words[:14])
    return text or "Review documented behavior"


def source_ref(source: ExtractedSource, line_number: int) -> str:
    return f"{source.display_path}#text-line-{line_number}"


def parse_source(source: ExtractedSource) -> tuple[list[dict[str, Any]], list[str]]:
    scenarios: list[dict[str, Any]] = []
    feature_areas: list[str] = []
    current_heading = ""
    current: dict[str, Any] | None = None
    current_line = 0
    used_lines: set[int] = set()

    def finish_current() -> None:
        nonlocal current, current_line
        if not current:
            return
        description = str(current.get("scenario", "")).strip()
        if not description:
            current = None
            return
        expected = str(current.get("expectedResult", "")).strip()
        notes = str(current.get("notes", "")).strip()
        warnings: list[str] = []
        if not expected:
            expected = "Review required: source document did not provide an observable expected result."
            warnings.append("Expected result was not explicit in source.")
        feature_area = current_heading if current_heading and current_heading.lower() not in GENERIC_HEADINGS else "General"
        if feature_area not in feature_areas:
            feature_areas.append(feature_area)
        dependencies = sorted(set(DEPENDENCY_RE.findall(str(current.get("dependsOn") or current.get("prerequisites", "")))))
        testers = [item.strip() for item in str(current.get("testers", "")).split(",") if item.strip()]
        scenarios.append(
            {
                "feature": feature_area,
                "description": description,
                "prerequisites": str(current.get("prerequisites", "")).strip(),
                "expectedResult": expected,
                "testers": testers,
                "status": "Pending",
                "scenarioType": scenario_type(str(current.get("scenarioType", "")), f"{feature_area} {description} {expected}"),
                "sourceStatus": "source-backed",
                "dependsOn": dependencies,
                "relatedBugIds": [],
                "sourceRefs": [source_ref(source, current_line)],
                "needsEngineeringReview": True,
                "styleWarnings": warnings,
                "notes": f"Drafted from explicit source scenario block. {notes}".strip(),
            }
        )
        current = None

    lines = source.text.splitlines()
    for line_number, raw_line in enumerate(lines, start=1):
        heading = HEADING_RE.match(raw_line)
        if heading:
            finish_current()
            current_heading = heading.group(1).strip()
            continue
        field = FIELD_RE.match(raw_line)
        if field:
            key = normalized_field(field.group(1))
            value = field.group(2).strip()
            if key == "featureArea":
                finish_current()
                current_heading = value
            elif key == "scenario":
                finish_current()
                current = {"scenario": value}
                current_line = line_number
            elif current is not None:
                current[key] = value
            used_lines.add(line_number)
            continue
        if current is not None and raw_line.startswith(("  ", "\t")) and raw_line.strip():
            key = "expectedResult" if current.get("expectedResult") else "notes"
            current[key] = f"{current.get(key, '')}\n{raw_line.strip()}".strip()
            used_lines.add(line_number)
    finish_current()

    for line_number, raw_line in enumerate(lines, start=1):
        if line_number in used_lines:
            continue
        heading = HEADING_RE.match(raw_line)
        if heading:
            current_heading = heading.group(1).strip()
            continue
        bullet = BULLET_RE.match(raw_line)
        if not bullet:
            continue
        requirement = bullet.group(1).strip()
        if FIELD_RE.match(raw_line) or len(requirement) < 12:
            continue
        heading_lower = current_heading.lower()
        if not any(word in heading_lower for word in FALLBACK_SECTION_WORDS):
            continue
        feature_area = current_heading if current_heading.lower() not in GENERIC_HEADINGS else "General"
        if feature_area not in feature_areas:
            feature_areas.append(feature_area)
        scenarios.append(
            {
                "feature": feature_area,
                "description": concise_description(requirement),
                "prerequisites": "Review source document setup and preconditions.",
                "expectedResult": requirement,
                "testers": [],
                "status": "Pending",
                "scenarioType": scenario_type("", f"{feature_area} {requirement}"),
                "sourceStatus": "inferred",
                "dependsOn": [],
                "relatedBugIds": [],
                "sourceRefs": [source_ref(source, line_number)],
                "needsEngineeringReview": True,
                "styleWarnings": ["Scenario wording and setup were inferred from a requirement bullet."],
                "notes": "Drafted from unstructured requirement text; confirm scenario wording and prerequisites.",
            }
        )

    return scenarios, feature_areas


def deduplicate_scenarios(scenarios: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduplicated: list[dict[str, Any]] = []
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for scenario in scenarios:
        key = (scenario["feature"].strip().lower(), scenario["description"].strip().lower())
        existing = by_key.get(key)
        if existing:
            existing["sourceRefs"] = sorted(set(existing.get("sourceRefs", []) + scenario.get("sourceRefs", [])))
            continue
        by_key[key] = scenario
        deduplicated.append(scenario)
    return deduplicated


def build_context(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    sources = [load_text(Path(item).expanduser().resolve()) for item in args.source]
    all_scenarios: list[dict[str, Any]] = []
    feature_areas: list[str] = []
    documents: list[dict[str, Any]] = []
    for source in sources:
        scenarios, areas = parse_source(source)
        all_scenarios.extend(scenarios)
        for area in areas:
            if area not in feature_areas:
                feature_areas.append(area)
        documents.append(
            {
                "path": source.display_path,
                "type": source.source_type,
                "extractionMethod": source.extraction_method,
                "sha256": hashlib.sha256(source.path.read_bytes()).hexdigest(),
                "characterCount": len(source.text),
                "draftScenarioCount": len(scenarios),
                "warnings": source.warnings,
            }
        )

    all_scenarios = deduplicate_scenarios(all_scenarios)
    for offset, scenario in enumerate(all_scenarios):
        scenario["id"] = f"T-{args.start_id + offset}"

    if not all_scenarios:
        raise ValueError(
            "No QA scenarios could be extracted. Add explicit 'Scenario:', 'Prerequisites:', and "
            "'Expected result:' blocks or requirement bullets under a requirements/behavior heading."
        )

    context = {
        "feature": args.feature,
        "productArea": args.product_area,
        "qaGoal": args.qa_goal,
        "scenarioStyleSource": "Original RAUC bug tracker engineering-authored scenarios",
        "styleGuideRef": "qa/scenario-style-guide.md",
        "validationRulesRef": "generators/xlsx/bug-bash-tracker.rules.json",
        "sourceDocs": [source.display_path for source in sources],
        "featureAreas": feature_areas or ["General"],
        "audienceGroundingRequired": bool(args.audience_grounding_required),
        "scenarios": all_scenarios,
        "bugs": [],
        "sourceDocumentIntake": {
            "status": "draft",
            "documents": documents,
            "scenarioCount": len(all_scenarios),
            "allScenariosRequireEngineeringReview": True,
            "limitations": [
                "Extraction is deterministic and does not understand arbitrary product prose.",
                "Explicit scenario blocks provide better fidelity than requirement-bullet fallback.",
                "Source-backed means the behavior is present in the document, not that engineering approved the test.",
            ],
        },
    }
    intake_report = {
        "feature": args.feature,
        "productArea": args.product_area,
        "documents": documents,
        "featureAreas": feature_areas,
        "draftScenarioCount": len(all_scenarios),
        "sourceBackedScenarioCount": sum(1 for item in all_scenarios if item["sourceStatus"] == "source-backed"),
        "inferredScenarioCount": sum(1 for item in all_scenarios if item["sourceStatus"] == "inferred"),
        "engineeringReviewRequired": True,
    }
    return context, intake_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a draft QA context from Markdown, text, or DOCX sources.")
    parser.add_argument("--feature", required=True, help="Feature under test.")
    parser.add_argument("--product-area", required=True, help="Product area.")
    parser.add_argument("--source", action="append", required=True, help="Source .md, .txt, or .docx file. Repeatable.")
    parser.add_argument("--output", required=True, help="Output draft QA context JSON.")
    parser.add_argument("--intake-report", help="Optional source intake report JSON.")
    parser.add_argument("--qa-goal", default="bug-bash", choices=["bug-bash", "release-readiness", "regression", "exploratory"])
    parser.add_argument("--start-id", type=int, default=401, help="First numeric QA scenario ID.")
    parser.add_argument("--audience-grounding-required", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        context, intake_report = build_context(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(context, indent=2) + "\n", encoding="utf-8")
    if args.intake_report:
        report_path = Path(args.intake_report).expanduser().resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(intake_report, indent=2) + "\n", encoding="utf-8")
    print(f"Done: {output_path}")
    print(f"Drafted: {len(context['scenarios'])} scenario(s) from {len(context['sourceDocs'])} source document(s)")


if __name__ == "__main__":
    main()
