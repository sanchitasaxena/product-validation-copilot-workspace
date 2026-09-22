#!/usr/bin/env python3
"""Export a survey JSON artifact as a Microsoft Forms transfer package."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


WORKSPACE = Path(__file__).resolve().parents[1]
DOCX_GENERATOR = WORKSPACE / "generators" / "docx" / "generate_research_docx.py"


def load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return data


def write_csv(path: Path, survey: dict[str, Any]) -> None:
    sections = {item["id"]: item["title"] for item in survey["sections"]}
    fields = [
        "section",
        "order",
        "question",
        "response_type",
        "required",
        "answer_choices",
        "rating_min",
        "rating_max",
        "rating_min_label",
        "rating_max_label",
        "branching_recommendation",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for index, question in enumerate(survey["questions"], start=1):
            rating = question.get("ratingScale") or {}
            writer.writerow({
                "section": sections.get(question.get("sectionId"), ""),
                "order": index,
                "question": question["prompt"],
                "response_type": question["responseType"],
                "required": question["required"],
                "answer_choices": " | ".join(question.get("answerChoices") or []),
                "rating_min": rating.get("min", ""),
                "rating_max": rating.get("max", ""),
                "rating_min_label": rating.get("minLabel", ""),
                "rating_max_label": rating.get("maxLabel", ""),
                "branching_recommendation": question.get("branchingRecommendation", ""),
            })


def write_instructions(path: Path, files: dict[str, Path]) -> None:
    path.write_text(
        f"""# Microsoft Forms import instructions

This package is a draft. Review all questions, consent language, privacy language, required settings, and routing before sharing it.

## Quick Import

1. Open Microsoft Forms and select **Quick Import**.
2. Select **Upload from this device**.
3. Upload `{files['import_docx'].name}` (must remain under 10 MB).
4. Choose **Form** and let Microsoft Forms convert it.
5. Review every converted question before distributing the form.

Quick Import supports titles/subtitles, multiple-choice questions, and open-text questions. It does not reliably create ratings, branching, or other complex settings. The import DOCX therefore represents unsupported question types as open text.

## Manual review and completion

- Use `{files['spec_docx'].name}` as the human-readable survey specification.
- Use `{files['json'].name}` or `{files['csv'].name}` to configure required status, ratings, answer choices, sections, and branching.
- Confirm organizational consent, privacy, retention, and accessibility requirements.
- Do not publish or distribute the form until a human has approved it.

This workspace does not publish a form and does not claim that a live Microsoft Forms URL has been created.
""",
        encoding="utf-8",
    )


def export(input_path: Path, prefix: Path) -> list[Path]:
    survey = load(input_path)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    files = {
        "spec_docx": prefix.with_suffix(".docx"),
        "import_docx": prefix.parent / f"{prefix.name}.forms-import.docx",
        "json": prefix.parent / f"{prefix.name}.forms.json",
        "csv": prefix.parent / f"{prefix.name}.forms.csv",
        "instructions": prefix.parent / f"{prefix.name}.forms-import.md",
    }
    files["json"].write_text(json.dumps(survey, indent=2) + "\n", encoding="utf-8")
    write_csv(files["csv"], survey)
    for output, extra in ((files["spec_docx"], []), (files["import_docx"], ["--forms-import"])):
        result = subprocess.run(
            [
                sys.executable,
                str(DOCX_GENERATOR),
                "--input",
                str(input_path),
                "--artifact-type",
                "discovery-survey",
                "--output",
                str(output),
                *extra,
            ],
            cwd=WORKSPACE,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    write_instructions(files["instructions"], files)
    return list(files.values())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Discovery survey JSON.")
    parser.add_argument("--output-prefix", required=True, help="Output path without an extension.")
    args = parser.parse_args()
    try:
        outputs = export(
            Path(args.input).expanduser().resolve(),
            Path(args.output_prefix).expanduser().resolve(),
        )
    except (OSError, ValueError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from exc
    for output in outputs:
        print(f"Created Microsoft Forms package file: {output}")


if __name__ == "__main__":
    main()
