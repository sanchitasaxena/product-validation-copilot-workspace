#!/usr/bin/env python3
"""Create schema-backed research artifacts with explicit human-review gates."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

WORKSPACE = Path(__file__).resolve().parents[1]
# No default UXR intake form is bundled. Configure your organization's real
# form URL with --monday-form-url or the MONDAY_FORM_URL environment
# variable; otherwise a clearly-labeled placeholder is used.
MONDAY_FORM_URL_PLACEHOLDER = "https://forms.monday.com/forms/REPLACE-WITH-YOUR-ORG-FORM-ID"


def load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return value


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def build_plan(context: dict[str, Any]) -> dict[str, Any]:
    questions = context.get("researchQuestions") or [
        f"What evidence is needed to inform: {context['decisionInformed']}?"
    ]
    return {
        "title": context.get("title", f"Research plan: {context['productArea']}"),
        "decisionInformed": context["decisionInformed"],
        "audienceResolutionRef": context.get("audienceResolutionRef"),
        "studies": [{
            "name": context.get("studyName", "Primary validation study"),
            "method": context.get("method", "Moderated usability study"),
            "researchQuestions": questions,
            "participants": context.get("participants", "Confirm participant criteria before recruiting."),
            "timeline": context.get("timeline", "Confirm timeline before scheduling."),
            "sourceRefs": context.get("sourceDocs", []),
        }],
        "outOfScope": context.get("outOfScope", []),
        "humanReviewRequired": True,
    }


def build_testing_guide(context: dict[str, Any]) -> dict[str, Any]:
    audience = context.get("audienceContext") or {}
    cujs = [c for c in (audience.get("cuj") or []) if c.get("text")]
    tasks = context.get("tasks")
    if not tasks and cujs:
        tasks = [
            {
                "title": cuj["text"],
                "prompt": f"Show how you would: {cuj['text'].rstrip('.')}.",
                "successCriteria": ["Participant reaches the intended outcome without facilitator instruction."],
                "facilitatorNotes": f"CUJ status: {cuj.get('status', 'unknown')}. Observe strategy, terminology, hesitation, and recovery.",
            }
            for cuj in cujs
        ]
    if not tasks:
        tasks = [{
            "title": "Complete the primary workflow",
            "prompt": "Show how you would accomplish the workflow in your own words.",
            "successCriteria": ["Participant reaches the intended outcome without facilitator instruction."],
            "facilitatorNotes": "Observe strategy, terminology, hesitation, and recovery.",
        }]
    return {
        "title": context.get("title", f"Testing guide: {context['productArea']}"),
        "audienceResolutionRef": context.get("audienceResolutionRef"),
        "productVersion": context.get("productVersion", "Confirm version before testing."),
        "environment": context.get("environment", "Confirm environment before testing."),
        "tasks": tasks,
        "humanReviewRequired": True,
    }


def reviewed_cujs(context: dict[str, Any]) -> list[dict[str, Any]]:
    audience = context.get("audienceContext") or {}
    return [claim for claim in (audience.get("cuj") or []) if claim.get("text")]


def build_unmoderated_test(context: dict[str, Any]) -> dict[str, Any]:
    cujs = reviewed_cujs(context)
    if not cujs:
        cujs = [{"text": "Complete the primary workflow", "status": "to-be-discovered"}]
    tasks = [
        {
            "id": f"TASK-{index:02d}",
            "cuj": claim["text"],
            "prompt": f"Without additional guidance, show how you would: {claim['text'].rstrip('.')}.",
            "successCriteria": ["Participant reaches the intended outcome without assistance."],
            "postTaskQuestions": [
                "How easy or difficult was that task?",
                "What, if anything, was unclear?",
            ],
        }
        for index, claim in enumerate(cujs, start=1)
    ]
    return {
        "title": context.get("title", f"Unmoderated test: {context['productArea']}"),
        "audienceResolutionRef": context.get("audienceResolutionRef"),
        "introduction": (
            "Complete the following activities as you normally would. "
            "The product is being evaluated, not you."
        ),
        "tasks": tasks,
        "closing": [
            "What was the most difficult part of this experience?",
            "What would you change first?",
        ],
        "humanReviewRequired": True,
    }


def build_discovery_guide(context: dict[str, Any]) -> dict[str, Any]:
    audience = context.get("audienceContext") or {}
    assumptions: list[dict[str, Any]] = []
    primary = audience.get("primaryPersona")
    if primary:
        assumptions.append(primary)
    assumptions.extend(audience.get("secondaryPersonas") or [])
    assumptions.extend(audience.get("jtbd") or [])
    assumptions.extend(audience.get("cuj") or [])
    if not assumptions:
        assumptions.append({
            "text": "Persona, JTBD, and CUJ are unknown and are the subject of this discovery research.",
            "status": "to-be-discovered",
            "confidence": "low",
            "sourceRefs": [],
        })
    new_proposals = context.get("newJtbdCujProposals") or [a for a in assumptions if a.get("status") == "proposed-catalog-update"]
    questions = context.get("researchQuestions") or [
        "Walk me through how you currently approach this problem today.",
        "What would make you trust or distrust this workflow?",
    ]
    synthesis_prompts = [
        "For each assumption, note whether the session validated, contradicted, or left it undetermined.",
        "Propose Target Audience Catalog updates only for assumptions with clear, repeated evidence.",
    ]
    if new_proposals:
        synthesis_prompts.append(
            f"{len(new_proposals)} JTBD/CUJ candidate(s) from source documents are new proposals, not confirmed catalog entries; use this session to validate or refute them before proposing a catalog update."
        )
    return {
        "title": context.get("title", f"Discovery guide: {context['productArea']}"),
        "productArea": context["productArea"],
        "decisionInformed": context.get("decisionInformed", ""),
        "audienceResolutionRef": context.get("audienceResolutionRef"),
        "assumptions": assumptions,
        "questions": questions,
        "synthesisPrompts": synthesis_prompts,
        "humanReviewRequired": True,
    }


def build_discovery_survey(context: dict[str, Any]) -> dict[str, Any]:
    assumptions = build_discovery_guide(context)["assumptions"]
    questions = context.get("researchQuestions") or [
        "How do you currently approach this problem?",
        "What is the hardest part of that process?",
        "What outcome matters most to you?",
    ]
    mapped_claims = [claim["text"] for claim in assumptions]
    return {
        "title": context.get("title", f"Discovery survey: {context['productArea']}"),
        "productArea": context["productArea"],
        "decisionInformed": context.get("decisionInformed", ""),
        "introduction": (
            "We are learning how people handle this problem today. "
            "Please answer based on your current experience; do not include secrets or customer data."
        ),
        "consentText": (
            "Participation is voluntary. You may skip any question or stop before submitting."
        ),
        "privacyText": (
            "Do not include credentials, customer data, or other confidential information. "
            "Responses should be handled according to your organization's research and retention policies."
        ),
        "sections": [
            {
                "id": "discovery",
                "title": "Current experience",
                "description": "Questions about current behavior, needs, and outcomes.",
            }
        ],
        "questions": [
            {
                "id": f"Q-{index:02d}",
                "prompt": prompt,
                "responseType": "long-text",
                "required": index == 1,
                "sectionId": "discovery",
                "answerChoices": [],
                "ratingScale": None,
                "branchingRecommendation": "",
                "mapsTo": mapped_claims,
            }
            for index, prompt in enumerate(questions, start=1)
        ],
        "humanReviewRequired": True,
    }


def build_synthesis(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "summary": context.get("summary", "Draft summary requires evidence review."),
        "findings": context.get("findings", []),
        "conflictingSignals": context.get("conflictingSignals", []),
        "nextQuestions": context.get("nextQuestions", []),
        "sources": context.get("sources") or context.get("sourceDocs", []),
        "humanReviewRequired": True,
    }


def build_monday_request(context: dict[str, Any]) -> dict[str, Any]:
    audience = context.get("audienceContext") or {}
    jtbd_texts = [c.get("text") for c in (audience.get("jtbd") or []) if c.get("text")]
    cuj_texts = [c.get("text") for c in (audience.get("cuj") or []) if c.get("text")]
    default_statement = "; ".join(jtbd_texts + cuj_texts)
    primary_persona = context.get("primaryPersona")
    if not primary_persona and audience.get("primaryPersona"):
        primary_persona = audience["primaryPersona"].get("text")
    answers = {
        "studyName": context.get("studyName", f"Study: {context.get('decisionInformed', context.get('productArea', ''))}"),
        "productArea": context["productArea"],
        "researchType": context.get("researchType", ""),
        "decisionInformed": context["decisionInformed"],
        "primaryPersona": primary_persona,
        "jtbdAndCuj": context.get("jtbdOrDiscoveryStatement", default_statement),
        "timeline": context.get("timeline", ""),
        "requester": context.get("pm", ""),
        "primaryContact": context.get("primaryContact", ""),
        "recruitingConstraints": context.get("recruitingConstraints", ""),
        "sourceDocuments": context.get("sourceDocs", []),
    }
    questions = {
        "researchType": "What research method should be requested?",
        "primaryPersona": "Who is the primary audience for this research?",
        "jtbdAndCuj": "Which reviewed JTBDs and CUJs should this research cover?",
        "timeline": "What deadline or timeline should the UXR team plan for?",
        "requester": "Who is the PM or requester?",
        "primaryContact": "Who is the primary contact for this request?",
        "recruitingConstraints": "Are there recruiting, entitlement, geography, or accessibility constraints?",
    }
    form_url = (
        context.get("mondayFormUrl")
        or os.environ.get("MONDAY_FORM_URL")
        or MONDAY_FORM_URL_PLACEHOLDER
    )
    return {
        "formUrl": form_url,
        "draftAnswers": answers,
        "missingQuestions": [question for field, question in questions.items() if not answers[field]],
        "humanReviewRequired": True,
        "submissionStatus": "draft",
        "fieldMappingStatus": "unverified-live-form",
    }


def monday_answer_sheet(artifact: dict[str, Any]) -> str:
    answers = artifact["draftAnswers"]
    labels = {
        "studyName": "Study name",
        "productArea": "Product area",
        "researchType": "Research type",
        "decisionInformed": "Decision this research informs",
        "primaryPersona": "Primary audience",
        "jtbdAndCuj": "JTBDs and CUJs",
        "timeline": "Timeline",
        "requester": "PM or requester",
        "primaryContact": "Primary contact",
        "recruitingConstraints": "Recruiting constraints",
        "sourceDocuments": "Source documents",
    }
    sections = []
    for field, label in labels.items():
        value = answers.get(field)
        if isinstance(value, list):
            rendered = "\n".join(f"- {item}" for item in value) or "_Not provided_"
        else:
            rendered = str(value).strip() if value else "_Not provided_"
        sections.append(f"## {label}\n\n{rendered}")
    missing = "\n".join(f"- {question}" for question in artifact["missingQuestions"]) or "- None"
    return (
        "# Monday.com UXR request draft\n\n"
        f"Form: {artifact['formUrl']}\n\n"
        "> Review these answers before copying them into Monday.com. "
        "This workspace never submits the form.\n\n"
        + "\n\n".join(sections)
        + f"\n\n## Questions still requiring answers\n\n{missing}\n"
    )


BUILDERS = {
    "plan": build_plan,
    "testing-guide": build_testing_guide,
    "unmoderated-test": build_unmoderated_test,
    "discovery-guide": build_discovery_guide,
    "discovery-survey": build_discovery_survey,
    "synthesis": build_synthesis,
    "monday-request": build_monday_request,
    "uxr-intake": build_monday_request,
}
VALIDATE_TYPE = {
    "plan": "research-plan",
    "testing-guide": "testing-guide",
    "unmoderated-test": "unmoderated-test",
    "discovery-guide": "discovery-guide",
    "discovery-survey": "discovery-survey",
    "synthesis": "synthesis-report",
    "monday-request": "monday-request",
    "uxr-intake": "monday-request",
}

WORKSPACE_TOOLS = WORKSPACE / "tools"
SOURCE_BUILDER = WORKSPACE_TOOLS / "build_research_context_from_sources.py"
VALIDATOR = WORKSPACE_TOOLS / "validate_context.py"
DOCX_GENERATOR = WORKSPACE / "generators" / "docx" / "generate_research_docx.py"
FORMS_EXPORTER = WORKSPACE_TOOLS / "export_microsoft_forms_package.py"
PYTHON = sys.executable


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=WORKSPACE, text=True, capture_output=True, check=False)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {result.returncode}: {' '.join(command)}")
    return result


def build_review_summary(args: argparse.Namespace, context: dict[str, Any], artifact: dict[str, Any], validation_errors: int, validation_warnings: int) -> str:
    intake = context.get("sourceDocumentIntake", {})
    new_proposals = context.get("newJtbdCujProposals", [])
    proposal_lines = "\n".join(f"- {p['text']}" for p in new_proposals) or "- None"
    return f"""# Research Workflow Review Summary

## Workflow inputs

- Workflow: {args.workflow}
- Product area: {context.get('productArea', args.product_area)}
- Source docs: {", ".join(context.get('sourceDocs', [])) or "None (manually authored context)"}

## Audience resolution

- Target audience mode: {context.get('targetAudienceMode', 'unknown')}
- Existing catalog matches: {intake.get('existingMatchCount', 'n/a')}
- New JTBD/CUJ/persona proposals requiring review: {intake.get('newProposalCount', len(new_proposals))}

### New JTBD/CUJ/persona proposals (not yet in the Target Audience Catalog)

{proposal_lines}

## Artifact validation

- Errors: {validation_errors}
- Warnings: {validation_warnings}

## Next review actions

- Confirm or reject each new JTBD/CUJ/persona proposal before treating it as catalog data.
- Human review is required before this artifact is used with participants or stakeholders.
- Fix validation errors before treating this artifact as final.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow", choices=sorted(BUILDERS), required=True)
    parser.add_argument("--input", help="Pre-authored research context or workflow input JSON.")
    parser.add_argument("--source-doc", action="append", help="PRD/RFC Markdown, text, or DOCX source. May be repeated.")
    parser.add_argument("--product-area", help="Required when using --source-doc.")
    parser.add_argument("--feature", help="Feature or problem space, if known.")
    parser.add_argument("--decision-informed", help="Override the decision this research informs.")
    parser.add_argument("--output", help="Output path for the artifact. Required when using --input.")
    parser.add_argument("--output-dir", help="Output directory. Required when using --source-doc.")
    parser.add_argument(
        "--approve",
        action="store_true",
        help="Mark a Monday request as approved for copying; this never submits the form.",
    )
    parser.add_argument("--study-name", help="Override studyName for uxr-intake.")
    parser.add_argument("--research-type", help="Override researchType for uxr-intake.")
    parser.add_argument("--timeline", help="Override timeline.")
    parser.add_argument(
        "--monday-form-url",
        help=(
            "Your organization's real UXR-intake form URL for monday-request/uxr-intake. "
            "Falls back to the MONDAY_FORM_URL environment variable, then a placeholder."
        ),
    )
    parser.add_argument(
        "--catalog-source",
        action="append",
        help="Approved Target Audience Catalog JSON file or directory. May be repeated.",
    )
    parser.add_argument(
        "--include-synthetic-catalog",
        action="store_true",
        help="Allow synthetic catalog fixtures for tests/demos only.",
    )
    args = parser.parse_args()
    if bool(args.input) == bool(args.source_doc):
        parser.error("Provide exactly one of --input or --source-doc.")
    if args.source_doc and not (args.product_area and args.output_dir):
        parser.error("--source-doc requires --product-area and --output-dir.")
    if args.input and not args.output:
        parser.error("--input requires --output.")
    if args.source_doc and args.workflow == "synthesis":
        parser.error(
            "Raw transcript/note synthesis is not implemented. "
            "Use --input with a structured synthesis context."
        )
    return args


def main() -> None:
    args = parse_args()

    if args.source_doc:
        output_dir = Path(args.output_dir).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        context_path = output_dir / "research-context.normalized.json"
        audience_path = output_dir / "audience-proposal.json"
        command = [
            PYTHON, str(SOURCE_BUILDER),
            "--product-area", args.product_area,
            "--workflow-hint", args.workflow,
            "--output", str(context_path),
            "--audience-proposal-output", str(audience_path),
        ]
        for doc in args.source_doc:
            command += ["--source-doc", doc]
        if args.feature:
            command += ["--feature", args.feature]
        if args.decision_informed:
            command += ["--decision-informed", args.decision_informed]
        for catalog_source in args.catalog_source or []:
            command += ["--catalog-source", catalog_source]
        if args.include_synthetic_catalog:
            command.append("--include-synthetic-catalog")
        run_command(command)
        context = load(context_path)
        output = Path(args.output).expanduser().resolve() if args.output else output_dir / f"{args.workflow}.json"
    else:
        context = load(Path(args.input).expanduser().resolve())
        output = Path(args.output).expanduser().resolve()

    for override_field, value in (("studyName", args.study_name), ("researchType", args.research_type), ("timeline", args.timeline), ("decisionInformed", args.decision_informed), ("mondayFormUrl", args.monday_form_url)):
        if value:
            context[override_field] = value

    artifact = BUILDERS[args.workflow](context)
    if args.workflow in {"monday-request", "uxr-intake"} and args.approve:
        artifact["submissionStatus"] = "approved-for-copy"

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(f"Created {args.workflow}: {output}")
    if args.workflow in {"monday-request", "uxr-intake"}:
        answer_sheet_path = output.with_suffix(".md")
        answer_sheet_path.write_text(monday_answer_sheet(artifact), encoding="utf-8")
        print(f"Monday answer sheet: {answer_sheet_path}")

    validation_path = output.with_suffix(".validation.json")
    validate_command = [PYTHON, str(VALIDATOR), "--input", str(output), "--type", VALIDATE_TYPE[args.workflow], "--json"]
    validate_result = subprocess.run(validate_command, cwd=WORKSPACE, text=True, capture_output=True, check=False)
    validation = json.loads(validate_result.stdout) if validate_result.stdout.strip() else {"errors": [], "warnings": []}
    write_json(validation_path, validation)
    errors, warnings = len(validation.get("errors", [])), len(validation.get("warnings", []))
    print(f"Validation: {errors} error(s), {warnings} warning(s)")

    if args.source_doc:
        summary_path = output_dir / "review-summary.md"
        summary_path.write_text(build_review_summary(args, context, artifact, errors, warnings), encoding="utf-8")
        print(f"Review summary: {summary_path}")

    if errors:
        sys.exit(1)

    if args.workflow != "synthesis":
        if args.workflow == "discovery-survey":
            run_command([
                PYTHON,
                str(FORMS_EXPORTER),
                "--input",
                str(output),
                "--output-prefix",
                str(output.with_suffix("")),
            ])
        else:
            docx_type = "monday-request" if args.workflow == "uxr-intake" else args.workflow
            docx_output = output.with_suffix(".docx")
            run_command([
                PYTHON,
                str(DOCX_GENERATOR),
                "--input",
                str(output),
                "--artifact-type",
                docx_type,
                "--output",
                str(docx_output),
            ])


if __name__ == "__main__":
    main()
