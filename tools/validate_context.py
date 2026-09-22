#!/usr/bin/env python3
"""Validate all schema-backed Product Validation Copilot Workspace contexts."""

from __future__ import annotations

import argparse
import json
import re
import sys
import warnings
from pathlib import Path
from typing import Any

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message="jsonschema.RefResolver is deprecated.*",
)
from jsonschema import Draft7Validator, FormatChecker, RefResolver


WORKSPACE = Path(__file__).resolve().parents[1]
SCHEMAS = WORKSPACE / "schemas"
SCHEMA_FILES = {
    "target-audience": "target-audience.schema.json",
    "qa-context": "qa-context.schema.json",
    "qa-scenario": "qa-scenario.schema.json",
    "bug-report": "bug-report.schema.json",
    "research-context": "research-context.schema.json",
    "research-plan": "research-plan.schema.json",
    "synthesis-report": "synthesis-report.schema.json",
    "uxr-intake": "uxr-intake.schema.json",
    "testing-guide": "testing-guide.schema.json",
    "discovery-guide": "discovery-guide.schema.json",
    "discovery-survey": "discovery-survey.schema.json",
    "unmoderated-test": "unmoderated-test.schema.json",
    "monday-request": "monday-request.schema.json",
}
QA_GOALS = {"bug-bash", "release-readiness", "regression", "exploratory"}
SCENARIO_STATUSES = {"Pending", "In Progress", "Passed", "Failed", "Blocked"}
SCENARIO_TYPES = {"UI", "API", "CLI", "Permissions", "Data", "Regression", "Edge Case", "Setup", "Exploratory"}
SOURCE_STATUSES = {"source-backed", "inferred", "regression", "edge-case", "exploratory"}
BUG_TYPES = {"Bug", "Friction", "Improvement"}
BUG_STATUSES = {"New", "In Progress", "QA", "Resolved", "Deferred"}
SEVERITIES = {"1-Critical", "2-High", "3-Medium", "4-Low", "Unrated"}
AUDIENCE_MODES = {"catalog-grounded", "discovery"}
RESOLUTION_STATUSES = {"confirmed", "needs-confirmation", "discovery-required"}
CLAIM_STATUSES = {
    "catalog-backed",
    "source-backed",
    "user-provided-assumption",
    "ai-inferred-assumption",
    "to-be-discovered",
    "validated-finding",
    "proposed-catalog-update",
}
CONFIDENCE = {"high", "medium", "low"}
TARGET_AUDIENCE_MODES = {"catalog-grounded", "discovery"}
SCENARIO_ID_RE = re.compile(r"^T-[0-9]+$")


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} is not valid JSON: {exc}") from exc


def issue(severity: str, path: str, message: str) -> dict[str, str]:
    return {"severity": severity, "path": path, "message": message}


def schema_path(parts: Any) -> str:
    path = "$"
    for part in parts:
        path += f"[{part}]" if isinstance(part, int) else f".{part}"
    return path


def validate_schema(value: Any, context_type: str) -> list[dict[str, str]]:
    filename = SCHEMA_FILES.get(context_type)
    if not filename:
        return []
    schema_file = SCHEMAS / filename
    schema = load_json(schema_file)
    resolver = RefResolver(base_uri=schema_file.as_uri(), referrer=schema)
    validator = Draft7Validator(schema, resolver=resolver, format_checker=FormatChecker())
    return [
        issue("error", schema_path(error.absolute_path), f"Schema: {error.message}")
        for error in sorted(validator.iter_errors(value), key=lambda item: list(item.absolute_path))
    ]


def require_object(value: Any, path: str, issues: list[dict[str, str]]) -> bool:
    if not isinstance(value, dict):
        issues.append(issue("error", path, "Expected JSON object."))
        return False
    return True


def require_array(value: Any, path: str, issues: list[dict[str, str]]) -> bool:
    if not isinstance(value, list):
        issues.append(issue("error", path, "Expected array."))
        return False
    return True


def require_field(obj: dict[str, Any], field: str, path: str, issues: list[dict[str, str]]) -> bool:
    if field not in obj or obj[field] in (None, "", []):
        issues.append(issue("error", f"{path}.{field}", "Missing required field."))
        return False
    return True


def check_enum(value: Any, allowed: set[str], path: str, issues: list[dict[str, str]], required: bool = False) -> None:
    if value in (None, ""):
        if required:
            issues.append(issue("error", path, "Missing required enum value."))
        return
    if value not in allowed:
        issues.append(issue("error", path, f"Unsupported value '{value}'. Expected one of: {', '.join(sorted(allowed))}."))


def validate_audience_claim(value: Any, path: str, issues: list[dict[str, str]]) -> None:
    if not require_object(value, path, issues):
        return
    require_field(value, "text", path, issues)
    require_field(value, "status", path, issues)
    require_field(value, "confidence", path, issues)
    check_enum(value.get("status"), CLAIM_STATUSES, f"{path}.status", issues)
    check_enum(value.get("confidence"), CONFIDENCE, f"{path}.confidence", issues)
    if "sourceRefs" in value and not isinstance(value["sourceRefs"], list):
        issues.append(issue("error", f"{path}.sourceRefs", "Expected array."))


def validate_target_audience(value: Any) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not require_object(value, "$", issues):
        return issues

    for field in ["mode", "productArea", "audienceContext", "humanReviewRequired"]:
        require_field(value, field, "$", issues)
    check_enum(value.get("mode"), AUDIENCE_MODES, "$.mode", issues)
    check_enum(value.get("resolutionStatus"), RESOLUTION_STATUSES, "$.resolutionStatus", issues)
    if not isinstance(value.get("humanReviewRequired"), bool):
        issues.append(issue("error", "$.humanReviewRequired", "Expected boolean."))

    audience = value.get("audienceContext")
    if require_object(audience, "$.audienceContext", issues):
        if "primaryPersona" in audience:
            validate_audience_claim(audience["primaryPersona"], "$.audienceContext.primaryPersona", issues)
        for field in ["secondaryPersonas", "jtbd", "cuj"]:
            if field in audience:
                if require_array(audience[field], f"$.audienceContext.{field}", issues):
                    for idx, claim in enumerate(audience[field]):
                        validate_audience_claim(claim, f"$.audienceContext.{field}[{idx}]", issues)

    generator = value.get("generatorContext", {})
    if generator and require_object(generator, "$.generatorContext", issues):
        summary = generator.get("targetAudienceSummary")
        if summary and require_object(summary, "$.generatorContext.targetAudienceSummary", issues):
            require_field(summary, "primaryPersona", "$.generatorContext.targetAudienceSummary", issues)
            require_field(summary, "humanReviewRequired", "$.generatorContext.targetAudienceSummary", issues)

    return issues


def validate_scenario(value: Any, path: str = "$") -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not require_object(value, path, issues):
        return issues
    for field in ["id", "feature", "description", "expectedResult", "status"]:
        require_field(value, field, path, issues)
    scenario_id = str(value.get("id", ""))
    if scenario_id and not SCENARIO_ID_RE.match(scenario_id):
        issues.append(issue("error", f"{path}.id", "Scenario ID must use T-### format."))
    check_enum(value.get("status"), SCENARIO_STATUSES, f"{path}.status", issues)
    check_enum(value.get("scenarioType"), SCENARIO_TYPES, f"{path}.scenarioType", issues)
    check_enum(value.get("sourceStatus"), SOURCE_STATUSES, f"{path}.sourceStatus", issues)
    for field in ["testers", "dependsOn", "relatedBugIds", "sourceRefs", "styleWarnings"]:
        if field in value and not isinstance(value[field], list):
            issues.append(issue("error", f"{path}.{field}", "Expected array."))
    if "needsEngineeringReview" in value and not isinstance(value["needsEngineeringReview"], bool):
        issues.append(issue("error", f"{path}.needsEngineeringReview", "Expected boolean."))
    return issues


def validate_evidence_link(value: Any, path: str, issues: list[dict[str, str]]) -> None:
    if not require_object(value, path, issues):
        return
    require_field(value, "type", path, issues)
    require_field(value, "uri", path, issues)


def validate_bug(value: Any, path: str = "$") -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not require_object(value, path, issues):
        return issues
    for field in ["id", "type", "description", "status"]:
        require_field(value, field, path, issues)
    check_enum(value.get("type"), BUG_TYPES, f"{path}.type", issues)
    check_enum(value.get("status"), BUG_STATUSES, f"{path}.status", issues)
    check_enum(value.get("severity"), SEVERITIES, f"{path}.severity", issues)
    for field in ["scenarioIds", "evidenceLinks", "validationWarnings"]:
        if field in value and not isinstance(value[field], list):
            issues.append(issue("error", f"{path}.{field}", "Expected array."))
    for idx, evidence in enumerate(value.get("evidenceLinks") or []):
        validate_evidence_link(evidence, f"{path}.evidenceLinks[{idx}]", issues)
    if "releaseBlocking" in value and not isinstance(value["releaseBlocking"], bool):
        issues.append(issue("error", f"{path}.releaseBlocking", "Expected boolean."))
    return issues


def validate_research_context(value: Any) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not require_object(value, "$", issues):
        return issues
    for field in ["workflow", "productArea", "decisionInformed", "targetAudienceMode"]:
        require_field(value, field, "$", issues)
    check_enum(value.get("targetAudienceMode"), TARGET_AUDIENCE_MODES, "$.targetAudienceMode", issues)
    for field in ["sourceDocs", "researchQuestions", "missingContext"]:
        if field in value and not isinstance(value[field], list):
            issues.append(issue("error", f"$.{field}", "Expected array."))
    return issues


def validate_research_plan(value: Any) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not require_object(value, "$", issues):
        return issues
    for field in ["title", "decisionInformed", "studies"]:
        require_field(value, field, "$", issues)
    studies = value.get("studies", [])
    if require_array(studies, "$.studies", issues):
        for idx, study in enumerate(studies):
            path = f"$.studies[{idx}]"
            if not require_object(study, path, issues):
                continue
            for field in ["name", "method", "researchQuestions"]:
                require_field(study, field, path, issues)
            if "researchQuestions" in study and not isinstance(study["researchQuestions"], list):
                issues.append(issue("error", f"{path}.researchQuestions", "Expected array."))
    return issues


def validate_synthesis_report(value: Any) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not require_object(value, "$", issues):
        return issues
    for field in ["summary", "findings", "sources"]:
        require_field(value, field, "$", issues)
    if require_array(value.get("findings"), "$.findings", issues):
        for idx, finding in enumerate(value["findings"]):
            path = f"$.findings[{idx}]"
            if require_object(finding, path, issues):
                require_field(finding, "title", path, issues)
                require_field(finding, "evidence", path, issues)
                if not isinstance(finding.get("evidence"), list):
                    issues.append(issue("error", f"{path}.evidence", "Expected array."))
    if not isinstance(value.get("sources"), list):
        issues.append(issue("error", "$.sources", "Expected array."))
    return issues


def validate_uxr_intake(value: Any) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not require_object(value, "$", issues):
        return issues
    for field in ["studyName", "productArea", "researchType", "decisionInformed", "timeline", "humanApproved"]:
        require_field(value, field, "$", issues)
    check_enum(value.get("targetAudienceMode"), TARGET_AUDIENCE_MODES, "$.targetAudienceMode", issues)
    if not isinstance(value.get("humanApproved"), bool):
        issues.append(issue("error", "$.humanApproved", "Expected boolean."))
    if value.get("humanApproved") and value.get("approvalStatus") != "approved":
        issues.append(issue("error", "$.approvalStatus", "Approved intake must have approvalStatus=approved."))
    if value.get("approvalStatus") == "approved" and not value.get("humanApproved"):
        issues.append(issue("error", "$.humanApproved", "Approved intake must be human approved."))
    if "sourceDocs" in value and not isinstance(value["sourceDocs"], list):
        issues.append(issue("error", "$.sourceDocs", "Expected array."))
    return issues


DISCOVERY_ASSUMPTION_STATUSES = {"source-backed", "to-be-discovered", "proposed-catalog-update", "user-provided-assumption"}


def validate_discovery_guide(value: Any) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not require_object(value, "$", issues):
        return issues
    for field in ["title", "productArea", "assumptions", "questions", "humanReviewRequired"]:
        require_field(value, field, "$", issues)
    if not isinstance(value.get("humanReviewRequired"), bool):
        issues.append(issue("error", "$.humanReviewRequired", "Expected boolean."))
    if require_array(value.get("assumptions"), "$.assumptions", issues):
        for idx, assumption in enumerate(value["assumptions"]):
            path = f"$.assumptions[{idx}]"
            if require_object(assumption, path, issues):
                require_field(assumption, "text", path, issues)
                require_field(assumption, "status", path, issues)
                check_enum(assumption.get("status"), DISCOVERY_ASSUMPTION_STATUSES, f"{path}.status", issues)
    if not isinstance(value.get("questions"), list):
        issues.append(issue("error", "$.questions", "Expected array."))
    return issues


def validate_testing_guide(value: Any) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not require_object(value, "$", issues):
        return issues
    for field in ["title", "productVersion", "environment", "tasks", "humanReviewRequired"]:
        require_field(value, field, "$", issues)
    if not isinstance(value.get("humanReviewRequired"), bool):
        issues.append(issue("error", "$.humanReviewRequired", "Expected boolean."))
    if require_array(value.get("tasks"), "$.tasks", issues):
        for idx, task in enumerate(value["tasks"]):
            path = f"$.tasks[{idx}]"
            if require_object(task, path, issues):
                for field in ["title", "prompt", "successCriteria"]:
                    require_field(task, field, path, issues)
                if "successCriteria" in task and not isinstance(task["successCriteria"], list):
                    issues.append(issue("error", f"{path}.successCriteria", "Expected array."))
    return issues


def validate_qa_context(value: Any) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not require_object(value, "$", issues):
        return issues
    for field in ["feature", "productArea", "qaGoal", "scenarioStyleSource"]:
        require_field(value, field, "$", issues)
    check_enum(value.get("qaGoal"), QA_GOALS, "$.qaGoal", issues)

    scenarios = value.get("scenarios", [])
    bugs = value.get("bugs", [])
    if not require_array(scenarios, "$.scenarios", issues):
        scenarios = []
    if not require_array(bugs, "$.bugs", issues):
        bugs = []

    seen_ids: set[str] = set()
    for idx, scenario in enumerate(scenarios):
        scenario_issues = validate_scenario(scenario, f"$.scenarios[{idx}]")
        issues.extend(scenario_issues)
        if isinstance(scenario, dict):
            scenario_id = scenario.get("id")
            if scenario_id in seen_ids:
                issues.append(issue("error", f"$.scenarios[{idx}].id", f"Duplicate scenario ID: {scenario_id}."))
            if scenario_id:
                seen_ids.add(str(scenario_id))

    for idx, bug in enumerate(bugs):
        issues.extend(validate_bug(bug, f"$.bugs[{idx}]"))

    intake = value.get("sourceDocumentIntake")
    if intake is not None and require_object(intake, "$.sourceDocumentIntake", issues):
        check_enum(intake.get("status"), {"draft", "reviewed", "approved"}, "$.sourceDocumentIntake.status", issues, required=True)
        documents = intake.get("documents")
        if require_array(documents, "$.sourceDocumentIntake.documents", issues):
            for idx, document in enumerate(documents):
                if require_object(document, f"$.sourceDocumentIntake.documents[{idx}]", issues):
                    for field in ["path", "type", "extractionMethod", "sha256"]:
                        require_field(document, field, f"$.sourceDocumentIntake.documents[{idx}]", issues)
        if intake.get("scenarioCount") != len(scenarios):
            issues.append(
                issue(
                    "error",
                    "$.sourceDocumentIntake.scenarioCount",
                    f"Expected {len(scenarios)} to match scenarios array.",
                )
            )
        for idx, scenario in enumerate(scenarios):
            if isinstance(scenario, dict) and not scenario.get("needsEngineeringReview"):
                issues.append(
                    issue(
                        "error",
                        f"$.scenarios[{idx}].needsEngineeringReview",
                        "Source-derived scenarios must require engineering review.",
                    )
                )
            if isinstance(scenario, dict) and not scenario.get("sourceRefs"):
                issues.append(issue("warning", f"$.scenarios[{idx}].sourceRefs", "Source-derived scenario has no source reference."))

    return issues


def detect_type(value: Any) -> str:
    if isinstance(value, dict) and "qaGoal" in value:
        return "qa-context"
    if isinstance(value, dict) and "audienceContext" in value and "mode" in value:
        return "target-audience"
    if isinstance(value, dict) and {"feature", "expectedResult", "status"}.issubset(value):
        return "qa-scenario"
    if isinstance(value, dict) and {"type", "description", "status"}.issubset(value):
        return "bug-report"
    if isinstance(value, dict) and {"workflow", "decisionInformed", "targetAudienceMode"}.issubset(value):
        return "research-context"
    if isinstance(value, dict) and {"title", "decisionInformed", "studies"}.issubset(value):
        return "research-plan"
    if isinstance(value, dict) and {"summary", "findings", "sources"}.issubset(value):
        return "synthesis-report"
    if isinstance(value, dict) and {"studyName", "researchType", "humanApproved"}.issubset(value):
        return "uxr-intake"
    if isinstance(value, dict) and {"title", "assumptions", "questions"}.issubset(value):
        return "discovery-guide"
    if isinstance(value, dict) and {"title", "productVersion", "tasks"}.issubset(value):
        return "testing-guide"
    if isinstance(value, dict) and {"title", "introduction", "questions"}.issubset(value):
        return "discovery-survey"
    if isinstance(value, dict) and {"title", "introduction", "tasks", "closing"}.issubset(value):
        return "unmoderated-test"
    if isinstance(value, dict) and {"formUrl", "draftAnswers", "missingQuestions"}.issubset(value):
        return "monday-request"
    return "unknown"


def validate(value: Any, context_type: str) -> list[dict[str, str]]:
    detected = detect_type(value) if context_type == "auto" else context_type
    semantic_validators = {
        "target-audience": validate_target_audience,
        "qa-context": validate_qa_context,
        "qa-scenario": validate_scenario,
        "bug-report": validate_bug,
        "research-context": validate_research_context,
        "research-plan": validate_research_plan,
        "synthesis-report": validate_synthesis_report,
        "uxr-intake": validate_uxr_intake,
        "discovery-guide": validate_discovery_guide,
        "testing-guide": validate_testing_guide,
    }
    if detected not in SCHEMA_FILES:
        return [issue("error", "$", "Could not determine context type. Pass --type explicitly.")]
    issues = validate_schema(value, detected)
    semantic_validator = semantic_validators.get(detected)
    if semantic_validator:
        issues.extend(semantic_validator(value))
    deduplicated = {
        (item["severity"], item["path"], item["message"]): item
        for item in issues
    }
    return list(deduplicated.values())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Product Validation Copilot Workspace context JSON.")
    parser.add_argument("--input", required=True, help="Path to JSON file.")
    parser.add_argument(
        "--type",
        default="auto",
        choices=[
            "auto", "target-audience", "qa-context", "qa-scenario", "bug-report",
            "research-context", "research-plan", "synthesis-report", "uxr-intake",
            "discovery-guide", "testing-guide", "discovery-survey",
            "unmoderated-test", "monday-request",
        ],
        help="Context type to validate.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable validation result.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    path = Path(args.input).expanduser().resolve()
    try:
        value = load_json(path)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    issues = validate(value, args.type)
    errors = [item for item in issues if item["severity"] == "error"]
    warnings = [item for item in issues if item["severity"] == "warning"]

    if args.json:
        print(json.dumps({"errors": errors, "warnings": warnings}, indent=2))
    else:
        print(f"Validation: {len(errors)} error(s), {len(warnings)} warning(s)")
        for item in issues:
            print(f"{item['severity'].upper()} {item['path']}: {item['message']}")

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
