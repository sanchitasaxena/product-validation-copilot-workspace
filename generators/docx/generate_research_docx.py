#!/usr/bin/env python3
"""Render schema-backed research artifacts as polished DOCX files with officecli."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import date
from pathlib import Path
from typing import Any


ACCENT = "1F4E79"
MUTED = "666666"


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return value


def run(command: list[str], input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"{' '.join(command)} failed: {detail}")
    return result


def add_paragraph(
    commands: list[dict[str, Any]],
    text: str,
    style: str = "Normal",
    **props: Any,
) -> None:
    paragraph_props = {"text": str(text), "style": style}
    paragraph_props.update(props)
    commands.append(
        {
            "command": "add",
            "parent": "/body",
            "type": "paragraph",
            "props": paragraph_props,
        }
    )


def add_heading(commands: list[dict[str, Any]], text: str, level: int = 1) -> None:
    add_paragraph(commands, text, f"Heading{level}")


def add_bullets(commands: list[dict[str, Any]], values: list[Any]) -> None:
    for value in values:
        add_paragraph(commands, f"• {value}")


def style_commands() -> list[dict[str, Any]]:
    return [
        {
            "command": "add",
            "parent": "/styles",
            "type": "style",
            "props": {
                "id": "Normal",
                "name": "Normal",
                "type": "paragraph",
                "font": "Aptos",
                "size": "11pt",
                "spaceAfter": "6pt",
                "lineSpacing": "1.15x",
                "qFormat": "true",
            },
        },
        {
            "command": "add",
            "parent": "/styles",
            "type": "style",
            "props": {
                "id": "Title",
                "name": "Title",
                "type": "paragraph",
                "basedOn": "Normal",
                "font": "Aptos Display",
                "size": "28pt",
                "bold": "true",
                "color": ACCENT,
                "spaceAfter": "12pt",
            },
        },
        {
            "command": "add",
            "parent": "/styles",
            "type": "style",
            "props": {
                "id": "Subtitle",
                "name": "Subtitle",
                "type": "paragraph",
                "basedOn": "Normal",
                "size": "12pt",
                "italic": "true",
                "color": MUTED,
                "spaceAfter": "18pt",
            },
        },
        {
            "command": "add",
            "parent": "/styles",
            "type": "style",
            "props": {
                "id": "Heading1",
                "name": "Heading 1",
                "type": "paragraph",
                "basedOn": "Normal",
                "size": "20pt",
                "bold": "true",
                "color": ACCENT,
                "outlineLevel": "0",
                "spaceBefore": "16pt",
                "spaceAfter": "8pt",
                "qFormat": "true",
            },
        },
        {
            "command": "add",
            "parent": "/styles",
            "type": "style",
            "props": {
                "id": "Heading2",
                "name": "Heading 2",
                "type": "paragraph",
                "basedOn": "Normal",
                "size": "14pt",
                "bold": "true",
                "color": ACCENT,
                "outlineLevel": "1",
                "spaceBefore": "12pt",
                "spaceAfter": "6pt",
                "qFormat": "true",
            },
        },
    ]


def document_start(commands: list[dict[str, Any]], title: str, subtitle: str) -> None:
    add_paragraph(commands, title, "Title")
    add_paragraph(commands, subtitle, "Subtitle")
    add_paragraph(
        commands,
        f"Draft generated {date.today().isoformat()} • Human review required before use",
        "Normal",
        italic="true",
        color=MUTED,
    )
    commands.append(
        {
            "command": "add",
            "parent": "/body",
            "type": "toc",
            "props": {
                "title": "Contents",
                "levels": "1-2",
                "hyperlinks": "true",
                "pageNumbers": "true",
            },
        }
    )


def render_plan(data: dict[str, Any], commands: list[dict[str, Any]]) -> None:
    document_start(commands, data["title"], "Research plan")
    add_heading(commands, "Decision this research informs")
    add_paragraph(commands, data["decisionInformed"])
    add_heading(commands, "Studies")
    for study in data["studies"]:
        add_heading(commands, study["name"], 2)
        add_paragraph(commands, f"Method: {study['method']}")
        add_paragraph(commands, f"Participants: {study.get('participants', 'Confirm before recruiting.')}")
        add_paragraph(commands, f"Timeline: {study.get('timeline', 'Confirm before scheduling.')}")
        add_heading(commands, "Research questions", 2)
        add_bullets(commands, study["researchQuestions"])
        if study.get("sourceRefs"):
            add_heading(commands, "Source references", 2)
            add_bullets(commands, study["sourceRefs"])
    add_heading(commands, "Out of scope")
    add_bullets(commands, data.get("outOfScope") or ["Confirm during human review."])


def render_testing_guide(data: dict[str, Any], commands: list[dict[str, Any]], unmoderated: bool) -> None:
    subtitle = "Unmoderated usability test" if unmoderated else "Moderated usability testing guide"
    document_start(commands, data["title"], subtitle)
    if unmoderated:
        add_heading(commands, "Participant introduction")
        add_paragraph(commands, data["introduction"])
    else:
        add_heading(commands, "Study setup")
        add_paragraph(commands, f"Product version: {data['productVersion']}")
        add_paragraph(commands, f"Environment: {data['environment']}")
        add_paragraph(
            commands,
            "Facilitator reminder: evaluate the product, not the participant. Avoid leading language.",
        )
    add_heading(commands, "Tasks")
    for index, task in enumerate(data["tasks"], start=1):
        task_title = task.get("title") or task.get("cuj") or task.get("id", f"Task {index}")
        add_heading(commands, f"Task {index}: {task_title}", 2)
        add_paragraph(commands, task["prompt"])
        add_paragraph(commands, f"CUJ: {task.get('cuj', task_title)}", italic="true")
        add_heading(commands, "Observable success criteria", 2)
        add_bullets(commands, task["successCriteria"])
        notes = task.get("facilitatorNotes")
        if notes:
            add_heading(commands, "Facilitator notes", 2)
            add_paragraph(commands, notes)
        if task.get("postTaskQuestions"):
            add_heading(commands, "Post-task questions", 2)
            add_bullets(commands, task["postTaskQuestions"])
    if unmoderated:
        add_heading(commands, "Closing questions")
        add_bullets(commands, data.get("closing", []))


def render_discovery_guide(data: dict[str, Any], commands: list[dict[str, Any]]) -> None:
    document_start(commands, data["title"], "Discovery interview guide")
    add_heading(commands, "Decision this research informs")
    add_paragraph(commands, data.get("decisionInformed", "Confirm before fieldwork."))
    add_heading(commands, "Assumptions to explore")
    for assumption in data["assumptions"]:
        add_paragraph(
            commands,
            f"• [{assumption['status']}] {assumption['text']}",
        )
    add_heading(commands, "Interview questions")
    for index, question in enumerate(data["questions"], start=1):
        add_paragraph(commands, f"{index}. {question}")
    add_heading(commands, "Synthesis prompts")
    add_bullets(commands, data.get("synthesisPrompts", []))


def question_type_label(value: str) -> str:
    return {
        "long-text": "Open text",
        "short-text": "Open text",
        "single-select": "Multiple choice — one answer",
        "multi-select": "Multiple choice — multiple answers",
        "rating": "Rating",
    }.get(value, value)


def render_survey(data: dict[str, Any], commands: list[dict[str, Any]], forms_import: bool) -> None:
    if forms_import:
        add_paragraph(commands, data["title"], "Title")
        add_paragraph(commands, data["introduction"], "Subtitle")
        add_paragraph(commands, f"Consent: {data['consentText']}")
        add_paragraph(commands, f"Privacy: {data['privacyText']}")
        section_by_id = {section["id"]: section for section in data["sections"]}
        current_section = None
        for question in data["questions"]:
            section = section_by_id.get(question.get("sectionId"))
            if section and section["id"] != current_section:
                add_heading(commands, section["title"])
                if section.get("description"):
                    add_paragraph(commands, section["description"])
                current_section = section["id"]
            add_paragraph(commands, question["prompt"], "Heading2")
            if question["responseType"] in {"single-select", "multi-select"}:
                for choice in question.get("answerChoices", []):
                    add_paragraph(commands, choice)
            else:
                add_paragraph(commands, "Open text response")
        return

    document_start(
        commands,
        data["title"],
        "Discovery survey specification",
    )
    add_heading(commands, "Introduction")
    add_paragraph(commands, data["introduction"])
    add_heading(commands, "Consent")
    add_paragraph(commands, data["consentText"])
    add_heading(commands, "Privacy")
    add_paragraph(commands, data["privacyText"])
    section_by_id = {section["id"]: section for section in data["sections"]}
    current_section = None
    for index, question in enumerate(data["questions"], start=1):
        section = section_by_id.get(question.get("sectionId"))
        if section and section["id"] != current_section:
            add_heading(commands, section["title"])
            if section.get("description"):
                add_paragraph(commands, section["description"])
            current_section = section["id"]
        add_heading(commands, f"{index}. {question['prompt']}", 2)
        add_paragraph(commands, f"Question type: {question_type_label(question['responseType'])}")
        add_paragraph(commands, f"Required: {'Yes' if question['required'] else 'No'}")
        if question.get("answerChoices"):
            add_paragraph(commands, "Answer choices:")
            add_bullets(commands, question["answerChoices"])
        if question.get("ratingScale"):
            rating = question["ratingScale"]
            add_paragraph(
                commands,
                f"Rating: {rating['min']} ({rating.get('minLabel', '')}) to "
                f"{rating['max']} ({rating.get('maxLabel', '')})",
            )
        if question.get("branchingRecommendation"):
            add_paragraph(commands, f"Branching: {question['branchingRecommendation']}")


def render_monday_request(data: dict[str, Any], commands: list[dict[str, Any]]) -> None:
    document_start(commands, "Monday.com UXR request draft", "Answer sheet — not submitted")
    add_paragraph(commands, f"Form: {data['formUrl']}")
    add_heading(commands, "Draft answers")
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
    for field, label in labels.items():
        add_heading(commands, label, 2)
        value = data["draftAnswers"].get(field)
        if isinstance(value, list):
            add_bullets(commands, value or ["Not provided"])
        else:
            add_paragraph(commands, value or "Not provided")
    add_heading(commands, "Questions still requiring answers")
    add_bullets(commands, data["missingQuestions"] or ["None"])
    add_heading(commands, "Approval boundary")
    add_paragraph(
        commands,
        "Review these answers before copying them into Monday.com. "
        "This workspace does not fill or submit the form.",
    )


def build_commands(data: dict[str, Any], artifact_type: str, forms_import: bool) -> list[dict[str, Any]]:
    commands = style_commands()
    if artifact_type == "plan":
        render_plan(data, commands)
    elif artifact_type == "testing-guide":
        render_testing_guide(data, commands, unmoderated=False)
    elif artifact_type == "unmoderated-test":
        render_testing_guide(data, commands, unmoderated=True)
    elif artifact_type == "discovery-guide":
        render_discovery_guide(data, commands)
    elif artifact_type == "discovery-survey":
        render_survey(data, commands, forms_import=forms_import)
    elif artifact_type == "monday-request":
        render_monday_request(data, commands)
    else:
        raise ValueError(f"Unsupported artifact type: {artifact_type}")
    if not forms_import:
        commands.append(
            {
                "command": "add",
                "parent": "/",
                "type": "footer",
                "props": {
                    "text": "Product Validation Copilot • Draft • ",
                    "field": "page",
                    "align": "center",
                    "font": "Aptos",
                    "size": "9pt",
                    "color": MUTED,
                },
            }
        )
    return commands


def generate(data: dict[str, Any], artifact_type: str, output: Path, forms_import: bool) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    run(["officecli", "create", str(output)])
    commands = build_commands(data, artifact_type, forms_import)
    run(["officecli", "batch", str(output), "--json"], json.dumps(commands))
    run(["officecli", "close", str(output)])
    run(["officecli", "validate", str(output)])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument(
        "--artifact-type",
        required=True,
        choices=[
            "plan",
            "testing-guide",
            "unmoderated-test",
            "discovery-guide",
            "discovery-survey",
            "monday-request",
        ],
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--forms-import", action="store_true")
    args = parser.parse_args()
    try:
        generate(
            load_json(Path(args.input).expanduser().resolve()),
            args.artifact_type,
            Path(args.output).expanduser().resolve(),
            args.forms_import,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Created DOCX: {Path(args.output).expanduser().resolve()}")


if __name__ == "__main__":
    main()
