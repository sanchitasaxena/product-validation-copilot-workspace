#!/usr/bin/env python3
"""
Resolve local Target Audience / JTBD / CUJ fixtures into a generator-ready context block.

V1 is intentionally local-only:
- reads JSON fixtures from target-audience/source, target-audience/index, or target-audience/examples;
- never calls SharePoint, Microsoft Graph, or other network services;
- returns catalog-grounded matches when local fixtures exist;
- returns discovery-mode scaffolding when no useful match exists.

Usage:
    python3 target-audience/resolve_target_audience.py \
        --feature "Registry artifact approval workflow" \
        --product-area "HCP Terraform Registry" \
        --persona "platform admin" \
        --artifact qa \
        --confirm-best-match \
        --output target-audience/out/resolved-context.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE_DIRS = [
    Path("target-audience/source"),
    Path("target-audience/index"),
    Path("target-audience/examples"),
]
TOKEN_RE = re.compile(r"[a-z0-9]+")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "by",
    "for",
    "from",
    "i",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "so",
    "that",
    "the",
    "to",
    "when",
    "with",
}


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def tokens(value: Any) -> Counter[str]:
    text = flatten_text(value).lower()
    return Counter(token for token in TOKEN_RE.findall(text) if token not in STOPWORDS and len(token) > 1)


def flatten_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(flatten_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(flatten_text(item) for item in value)
    return str(value)


def fixture_text(fixture: dict[str, Any]) -> str:
    fields = [
        fixture.get("productArea"),
        fixture.get("featureOrProblemSpace"),
        fixture.get("audienceContext"),
        fixture.get("allowedArtifacts"),
    ]
    return flatten_text(fields)


def query_text(args: argparse.Namespace) -> str:
    return " ".join(
        part
        for part in [
            args.product_area,
            args.feature,
            args.persona,
            args.jtbd,
            args.cuj,
            args.problem_space,
        ]
        if part
    )


def score_fixture(fixture: dict[str, Any], query: str, args: argparse.Namespace) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    fixture_tokens = tokens(fixture_text(fixture))
    query_tokens = tokens(query)
    overlap = sorted((fixture_tokens & query_tokens).elements())
    if overlap:
        overlap_score = len(set(overlap))
        score += overlap_score
        reasons.append(f"token overlap: {', '.join(sorted(set(overlap))[:12])}")

    product_area = str(fixture.get("productArea", "")).strip().lower()
    if args.product_area and product_area == args.product_area.strip().lower():
        score += 10
        reasons.append("exact product area match")

    feature = str(fixture.get("featureOrProblemSpace", "")).strip().lower()
    if args.feature and feature == args.feature.strip().lower():
        score += 12
        reasons.append("exact feature/problem-space match")
    elif args.feature and args.feature.strip().lower() in feature:
        score += 6
        reasons.append("partial feature/problem-space match")

    primary = claim_text(fixture, "primaryPersona").lower()
    if args.persona and args.persona.strip().lower() in primary:
        score += 8
        reasons.append("primary persona match")

    return score, reasons


def claim_text(fixture: dict[str, Any], key: str) -> str:
    claim = fixture.get("audienceContext", {}).get(key)
    if isinstance(claim, dict):
        return str(claim.get("text", ""))
    return ""


def find_fixtures(paths: list[Path]) -> list[Path]:
    fixture_paths: list[Path] = []
    for path in paths:
        resolved = resolve_workspace_path(path)
        if resolved.is_file() and resolved.suffix == ".json":
            fixture_paths.append(resolved)
        elif resolved.is_dir():
            fixture_paths.extend(sorted(resolved.rglob("*.json")))
    return sorted(set(fixture_paths))


def resolve_workspace_path(path: Path) -> Path:
    expanded = path.expanduser()
    if expanded.is_absolute():
        return expanded
    return ROOT / expanded


def confidence(score: int, top_score: int, tied: bool) -> str:
    if tied or score < 8:
        return "low"
    if score >= 20 and score >= top_score:
        return "high"
    if score >= 12:
        return "medium"
    return "low"


def status_label(fixture: dict[str, Any]) -> str:
    if fixture.get("syntheticTestData"):
        return "synthetic-test-data"
    primary = fixture.get("audienceContext", {}).get("primaryPersona", {})
    if isinstance(primary, dict):
        return str(primary.get("status", "unknown"))
    return "unknown"


def summarize_claims(fixture: dict[str, Any]) -> dict[str, Any]:
    audience = fixture.get("audienceContext", {})
    primary = audience.get("primaryPersona") or {}
    jtbd = audience.get("jtbd") or []
    cuj = audience.get("cuj") or []
    return {
        "primaryPersona": primary.get("text", "") if isinstance(primary, dict) else "",
        "jtbd": [item.get("text", "") for item in jtbd if isinstance(item, dict) and item.get("text")],
        "cuj": [item.get("text", "") for item in cuj if isinstance(item, dict) and item.get("text")],
    }


def result_for_match(
    fixture_path: Path,
    fixture: dict[str, Any],
    match_score: int,
    match_reasons: list[str],
    alternatives: list[dict[str, Any]],
    args: argparse.Namespace,
) -> dict[str, Any]:
    tied = bool(alternatives and alternatives[0]["score"] == match_score)
    result_confidence = confidence(match_score, match_score, tied)
    source_ref = str(fixture_path.relative_to(ROOT)) if fixture_path.is_relative_to(ROOT) else str(fixture_path)
    confirmed = args.confirm_best_match and not tied
    needs_review = not confirmed or tied or fixture.get("humanReviewRequired", False)
    claim_summary = summarize_claims(fixture)
    mode = fixture.get("mode", "catalog-grounded")

    ambiguities = list(fixture.get("ambiguities", []))
    if tied:
        ambiguities.append("Multiple local target audience fixtures have the same top match score.")
    if not confirmed:
        ambiguities.append("Best local match has not been explicitly confirmed by a human/operator.")

    return {
        "resolutionStatus": "confirmed" if confirmed else "needs-confirmation",
        "mode": mode,
        "requestedArtifact": args.artifact,
        "productArea": fixture.get("productArea", args.product_area),
        "featureOrProblemSpace": fixture.get("featureOrProblemSpace", args.feature or args.problem_space),
        "selectedSource": source_ref,
        "match": {
            "score": match_score,
            "confidence": result_confidence,
            "reasons": match_reasons,
            "dataStatus": status_label(fixture),
        },
        "audienceContext": fixture.get("audienceContext", {}),
        "ambiguities": ambiguities,
        "missingContext": fixture.get("missingContext", []),
        "allowedArtifacts": fixture.get("allowedArtifacts", []),
        "blockedArtifacts": fixture.get("blockedArtifacts", []),
        "humanReviewRequired": needs_review,
        "alternatives": alternatives[:5],
        "generatorContext": {
            "targetAudienceRef": source_ref,
            "targetAudienceSummary": {
                "dataStatus": status_label(fixture),
                "resolutionStatus": "confirmed" if confirmed else "needs-confirmation",
                "mode": mode,
                "confidence": result_confidence,
                "primaryPersona": claim_summary["primaryPersona"],
                "jtbd": claim_summary["jtbd"][0] if claim_summary["jtbd"] else "",
                "jtbdList": claim_summary["jtbd"],
                "cujUsedForQA": claim_summary["cuj"],
                "cujUsedForResearch": claim_summary["cuj"],
                "sourceRefs": [source_ref],
                "humanReviewRequired": needs_review,
            },
        },
    }


def discovery_result(args: argparse.Namespace, fixture_count: int) -> dict[str, Any]:
    product_area = args.product_area or "Unknown product area"
    problem_space = args.feature or args.problem_space or "Unknown feature/problem space"
    persona = args.persona or "Target audience to be discovered"
    jtbd = args.jtbd or "JTBD to be discovered through research."
    cuj = args.cuj or "CUJ to be discovered through research."
    return {
        "resolutionStatus": "discovery-required",
        "mode": "discovery",
        "requestedArtifact": args.artifact,
        "productArea": product_area,
        "featureOrProblemSpace": problem_space,
        "selectedSource": None,
        "match": {
            "score": 0,
            "confidence": "low",
            "reasons": [f"No local fixture matched above threshold. Fixtures scanned: {fixture_count}."],
            "dataStatus": "to-be-discovered",
        },
        "audienceContext": {
            "primaryPersona": {
                "text": persona,
                "status": "to-be-discovered",
                "confidence": "low",
                "sourceRefs": [],
            },
            "secondaryPersonas": [],
            "jtbd": [
                {
                    "text": jtbd,
                    "status": "to-be-discovered",
                    "confidence": "low",
                    "sourceRefs": [],
                }
            ],
            "cuj": [
                {
                    "text": cuj,
                    "status": "to-be-discovered",
                    "confidence": "low",
                    "sourceRefs": [],
                }
            ],
        },
        "ambiguities": ["No local catalog-grounded match was found."],
        "missingContext": [
            "Confirmed persona",
            "Confirmed JTBD",
            "Confirmed CUJ",
            "Source references",
        ],
        "allowedArtifacts": [
            "discovery research plan",
            "discovery interview guide",
            "contextual inquiry guide",
            "exploratory QA checklist",
        ],
        "blockedArtifacts": [
            "official persona/JTBD/CUJ claims",
            "catalog-backed usability validation plan",
            "Target Audience Catalog update without human review",
        ],
        "humanReviewRequired": True,
        "alternatives": [],
        "generatorContext": {
            "targetAudienceRef": None,
            "targetAudienceSummary": {
                "dataStatus": "to-be-discovered",
                "resolutionStatus": "discovery-required",
                "mode": "discovery",
                "confidence": "low",
                "primaryPersona": persona,
                "jtbd": jtbd,
                "jtbdList": [jtbd],
                "cujUsedForQA": [cuj],
                "cujUsedForResearch": [cuj],
                "sourceRefs": [],
                "humanReviewRequired": True,
            },
        },
    }


def resolve(args: argparse.Namespace) -> dict[str, Any]:
    fixture_dirs = [Path(item) for item in args.fixture_dir] if args.fixture_dir else DEFAULT_FIXTURE_DIRS
    fixture_paths = find_fixtures(fixture_dirs)
    query = query_text(args)
    scored: list[dict[str, Any]] = []

    for fixture_path in fixture_paths:
        fixture = load_json(fixture_path)
        score, reasons = score_fixture(fixture, query, args)
        if score > 0:
            source_ref = str(fixture_path.relative_to(ROOT)) if fixture_path.is_relative_to(ROOT) else str(fixture_path)
            scored.append({"path": source_ref, "score": score, "reasons": reasons, "fixture": fixture, "pathObj": fixture_path})

    scored.sort(key=lambda item: (-item["score"], item["path"]))
    if not scored or scored[0]["score"] < args.min_score:
        return discovery_result(args, len(fixture_paths))

    best = scored[0]
    alternatives = [
        {"path": item["path"], "score": item["score"], "reasons": item["reasons"]}
        for item in scored[1:]
        if item["score"] >= max(args.min_score, best["score"] - 3)
    ]
    return result_for_match(best["pathObj"], best["fixture"], best["score"], best["reasons"], alternatives, args)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Resolve local Target Audience/JTBD/CUJ context.")
    parser.add_argument("--feature", help="Feature name to match.")
    parser.add_argument("--product-area", help="Product area to match.")
    parser.add_argument("--persona", help="User-described persona or role.")
    parser.add_argument("--jtbd", help="Known or suspected JTBD text.")
    parser.add_argument("--cuj", help="Known or suspected CUJ text.")
    parser.add_argument("--problem-space", help="Problem space when feature name is not known.")
    parser.add_argument("--artifact", choices=["qa", "research", "uxr-intake", "document-edit"], default="qa")
    parser.add_argument(
        "--fixture-dir",
        action="append",
        help="Fixture directory or JSON file to scan. May be repeated. Defaults to target-audience/source,index,examples.",
    )
    parser.add_argument("--min-score", type=int, default=8, help="Minimum match score before discovery fallback.")
    parser.add_argument(
        "--confirm-best-match",
        action="store_true",
        help="Mark the best non-tied local match as confirmed for downstream generator context.",
    )
    parser.add_argument("--output", help="Optional path for resolved context JSON.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        result = resolve(args)
    except ValueError as exc:
        sys.exit(str(exc))

    if args.output:
        output_path = resolve_workspace_path(Path(args.output))
        write_json(output_path, result)
        print(f"Done: {output_path}")
    else:
        print(json.dumps(result, indent=2))

    print(
        "Resolution: "
        f"{result['resolutionStatus']} "
        f"({result['mode']}, confidence={result['match']['confidence']}, score={result['match']['score']})",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
