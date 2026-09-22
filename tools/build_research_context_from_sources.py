#!/usr/bin/env python3
"""
Extract Markdown, text, and DOCX PRD/RFC sources into a draft research context.

PRDs and RFCs are where new JTBDs and CUJs typically originate. This tool
extracts JTBD/CUJ/persona/decision/question candidates from source documents,
then cross-references each JTBD/CUJ/persona candidate directly against local
Target Audience Catalog fixtures (`target-audience/source`, `/index`,
`/examples`) using token-overlap similarity, to determine whether it already
exists in the catalog or is a new proposal that requires human review before
being added.

Recognized labels (case-insensitive), one per line:

    Persona: Platform admin
    JTBD: When ..., I want ..., so that ...
    CUJ: Admin reviews and approves a registry artifact.
    Decision: Whether the approval workflow is understandable.
    Research Question: Can admins recover from a blocked artifact?

Bulleted lines under a heading containing "job(s) to be done"/"jtbd",
"critical user journey"/"cuj", or "open question(s)"/"research question(s)"
are accepted as a lower-confidence fallback.

This uses deterministic labels plus conservative prose heuristics, not
semantic understanding. Every JTBD/CUJ candidate is either matched to an existing catalog
fixture (source-backed, needs human confirmation) or flagged as a new
proposed catalog update (must not be treated as official until reviewed).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


WORKSPACE = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE_DIRS = [
    WORKSPACE / "target-audience" / "source",
    WORKSPACE / "target-audience" / "index",
]
SUPPORTED_SUFFIXES = {".md", ".markdown", ".txt", ".docx"}
TOKEN_RE = re.compile(r"[a-z0-9]+")
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "for",
    "from", "have", "i", "in", "is", "it", "of", "on", "or", "so", "that",
    "the", "this", "to", "when", "will", "with",
}
# A candidate is treated as an existing catalog JTBD/CUJ/persona when its
# token-overlap (Jaccard similarity) with a catalog claim meets this bar.
MATCH_THRESHOLD = 0.35

HEADING_RE = re.compile(r"^\s*#{1,6}\s+(.+?)\s*$")
LABEL_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(persona|jtbd|cuj|decision|research question|open question)\s*:\s*(.+)$",
    re.IGNORECASE,
)
BULLET_RE = re.compile(r"^\s*[-*]\s+(.+?)\s*$")
OFFICECLI_PATH_RE = re.compile(r"^\[.*\]\s*")

JTBD_HEADING_WORDS = ("job to be done", "jobs to be done", "jtbd")
CUJ_HEADING_WORDS = ("critical user journey", "cuj")
QUESTION_HEADING_WORDS = ("open question", "research question")
DECISION_HEADING_WORDS = ("decision", "problem statement")


@dataclass
class ExtractedSource:
    path: Path
    display_path: str
    source_type: str
    extraction_method: str
    text: str
    sha256: str
    warnings: list[str] = field(default_factory=list)


@dataclass
class Candidate:
    kind: str  # "persona" | "jtbd" | "cuj" | "decision" | "question" | "requirement"
    text: str
    source_ref: str
    extraction_status: str
    source_excerpt: str


def workspace_display_path(path: Path) -> str:
    try:
        return str(path.relative_to(WORKSPACE))
    except ValueError:
        return str(path)


def load_source(path: Path) -> ExtractedSource:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ValueError(f"Unsupported source format '{suffix}' for {path}. Supported: .md, .markdown, .txt, .docx.")
    raw_bytes = path.read_bytes()
    sha256 = hashlib.sha256(raw_bytes).hexdigest()
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
            text = raw_bytes.decode("utf-8")
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
        sha256=sha256,
    )


def source_ref(source: ExtractedSource, line_number: int) -> str:
    return f"{source.display_path}#text-line-{line_number}"


def parse_source(source: ExtractedSource) -> list[Candidate]:
    candidates: list[Candidate] = []
    current_heading = ""
    lines = source.text.splitlines()
    for line_number, raw_line in enumerate(lines, start=1):
        heading = HEADING_RE.match(raw_line)
        if heading:
            current_heading = heading.group(1).strip().lower()
            continue

        label = LABEL_RE.match(raw_line)
        if label:
            key = label.group(1).strip().lower()
            text = label.group(2).strip()
            if not text:
                continue
            kind = {
                "persona": "persona",
                "jtbd": "jtbd",
                "cuj": "cuj",
                "decision": "decision",
                "research question": "question",
                "open question": "question",
            }[key]
            candidates.append(Candidate(kind, text, source_ref(source, line_number), "explicit", raw_line.strip()))
            continue

        bullet = BULLET_RE.match(raw_line)
        if bullet:
            text = bullet.group(1).strip()
            if not text:
                continue
            if any(word in current_heading for word in JTBD_HEADING_WORDS):
                candidates.append(Candidate("jtbd", text, source_ref(source, line_number), "explicit", raw_line.strip()))
            elif any(word in current_heading for word in CUJ_HEADING_WORDS):
                candidates.append(Candidate("cuj", text, source_ref(source, line_number), "explicit", raw_line.strip()))
            elif any(word in current_heading for word in QUESTION_HEADING_WORDS):
                candidates.append(Candidate("question", text, source_ref(source, line_number), "explicit", raw_line.strip()))
            continue

        if any(word in current_heading for word in DECISION_HEADING_WORDS) and raw_line.strip():
            candidates.append(Candidate("decision", raw_line.strip(), source_ref(source, line_number), "explicit", raw_line.strip()))

    candidates.extend(parse_normal_prose(source, candidates))
    return deduplicate_candidates(candidates)


def parse_normal_prose(source: ExtractedSource, existing: list[Candidate]) -> list[Candidate]:
    candidates: list[Candidate] = []
    explicit_refs = {candidate.source_ref for candidate in existing}
    role_pattern = re.compile(
        r"\b(admin(?:istrator)?s?|developers?|maintainers?|operators?|reviewers?|"
        r"customers?|users?|engineers?|managers?|requesters?|approvers?)\b",
        re.IGNORECASE,
    )
    action_pattern = re.compile(
        r"\b(review|approve|create|submit|find|compare|configure|complete|publish|"
        r"share|resolve|recover|track|manage|use|verify|inspect|export|import)\w*\b",
        re.IGNORECASE,
    )
    for line_number, raw_line in enumerate(source.text.splitlines(), start=1):
        stripped = raw_line.strip()
        ref = source_ref(source, line_number)
        if not stripped or ref in explicit_refs or HEADING_RE.match(raw_line) or BULLET_RE.match(raw_line):
            continue
        for sentence in re.split(r"(?<=[.!?])\s+", stripped):
            text = sentence.strip()
            if len(text.split()) < 4:
                continue
            excerpt = text[:500]
            lowered = text.lower()
            if text.endswith("?"):
                candidates.append(Candidate("question", text, ref, "explicit", excerpt))
            if re.search(r"\b(decide|determine|evaluate|understand|learn|validate)\s+whether\b", lowered):
                candidates.append(Candidate("decision", text, ref, "inferred", excerpt))
            if re.search(r"\b(need(?:s)? to|want(?:s)? to|must be able to|so that)\b", lowered):
                candidates.append(Candidate("jtbd", text, ref, "inferred", excerpt))
            role_match = role_pattern.search(text)
            if role_match and re.search(r"\b(for|used by|designed for|primary users? (?:are|include))\b", lowered):
                candidates.append(Candidate("persona", role_match.group(1), ref, "inferred", excerpt))
            if role_match and action_pattern.search(text):
                candidates.append(Candidate("cuj", text, ref, "uncertain", excerpt))
            if re.search(r"\b(must|shall|required to|should support|system will)\b", lowered):
                candidates.append(Candidate("requirement", text, ref, "inferred", excerpt))
    return candidates


def deduplicate_candidates(candidates: list[Candidate]) -> list[Candidate]:
    results: list[Candidate] = []
    seen: set[tuple[str, str]] = set()
    for candidate in candidates:
        key = (candidate.kind, re.sub(r"\W+", " ", candidate.text.lower()).strip())
        if key not in seen:
            results.append(candidate)
            seen.add(key)
    return results


def tokenize(text: str) -> Counter[str]:
    return Counter(t for t in TOKEN_RE.findall(text.lower()) if t not in STOPWORDS and len(t) > 1)


def jaccard(a: Counter[str], b: Counter[str]) -> float:
    a_set, b_set = set(a), set(b)
    if not a_set or not b_set:
        return 0.0
    return len(a_set & b_set) / len(a_set | b_set)


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def catalog_paths(values: list[str] | None) -> list[Path]:
    if not values:
        return DEFAULT_FIXTURE_DIRS
    return [Path(value).expanduser().resolve() for value in values]


def load_catalog_fixtures(
    product_area: str,
    paths: list[Path],
    include_synthetic: bool = False,
) -> list[tuple[str, dict[str, Any]]]:
    """Load local Target Audience Catalog fixtures scoped to a product area.

    This is the reference set used to determine whether a PRD/RFC's JTBD or
    CUJ already exists in the catalog, or is a new proposal.
    """
    fixtures: list[tuple[str, dict[str, Any]]] = []
    for catalog_path in paths:
        candidates = [catalog_path] if catalog_path.is_file() else sorted(catalog_path.rglob("*.json"))
        for path in candidates:
            try:
                fixture = load_json(path)
            except (json.JSONDecodeError, OSError):
                continue
            if not isinstance(fixture, dict):
                continue
            if fixture.get("syntheticTestData") and not include_synthetic:
                continue
            if str(fixture.get("productArea", "")).strip().lower() != product_area.strip().lower():
                continue
            fixtures.append((workspace_display_path(path), fixture))
    return fixtures


def catalog_claims(
    fixtures: list[tuple[str, dict[str, Any]]],
    kind: str,
) -> list[tuple[str, str, str, bool]]:
    """Return fixture path, claim text/status, and synthetic-data flag."""
    key = {"persona": "primaryPersona", "jtbd": "jtbd", "cuj": "cuj"}[kind]
    results: list[tuple[str, str, str, bool]] = []
    for fixture_path, fixture in fixtures:
        audience = fixture.get("audienceContext", {})
        if kind == "persona":
            claims = [audience.get("primaryPersona")] + list(audience.get("secondaryPersonas") or [])
        else:
            claims = audience.get(key) or []
        for claim in claims:
            if (
                isinstance(claim, dict)
                and claim.get("text")
                and claim.get("status") in {"catalog-backed", "validated-finding", "source-backed"}
            ):
                results.append(
                    (
                        fixture_path,
                        str(claim["text"]),
                        str(claim.get("status", "unknown")),
                        bool(fixture.get("syntheticTestData")),
                    )
                )
    return results


def best_catalog_match(
    candidate_text: str,
    claims: list[tuple[str, str, str, bool]],
) -> tuple[str, str, float, bool] | None:
    candidate_tokens = tokenize(candidate_text)
    best: tuple[str, str, float, bool] | None = None
    for fixture_path, claim_text, _status, is_synthetic in claims:
        score = jaccard(candidate_tokens, tokenize(claim_text))
        if score >= MATCH_THRESHOLD and (best is None or score > best[2]):
            best = (fixture_path, claim_text, score, is_synthetic)
    return best


def claim_from_candidate(
    candidate: Candidate,
    claims: list[tuple[str, str, str, bool]],
) -> dict[str, Any]:
    match = best_catalog_match(candidate.text, claims)
    if match:
        fixture_path, matched_text, score, is_synthetic = match
        confidence = "high" if score >= 0.7 else "medium"
        return {
            "text": candidate.text,
            "status": "source-backed",
            "confidence": confidence,
            "sourceRefs": [candidate.source_ref, fixture_path],
            "matchedCatalogSource": fixture_path,
            "matchedCatalogText": matched_text,
            "matchSimilarity": round(score, 2),
            "matchDataStatus": "synthetic-test-data" if is_synthetic else "catalog-reference",
            "newProposal": False,
            "extractionStatus": candidate.extraction_status,
            "sourceExcerpt": candidate.source_excerpt,
        }
    return {
        "text": candidate.text,
        "status": "proposed-catalog-update",
        "confidence": "low",
        "sourceRefs": [candidate.source_ref],
        "matchedCatalogSource": None,
        "newProposal": True,
        "extractionStatus": candidate.extraction_status,
        "sourceExcerpt": candidate.source_excerpt,
    }


def build_context(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    sources = [load_source(Path(p).expanduser().resolve()) for p in args.source_doc]

    persona_candidates: list[Candidate] = []
    jtbd_candidates: list[Candidate] = []
    cuj_candidates: list[Candidate] = []
    decision_candidates: list[Candidate] = []
    question_candidates: list[Candidate] = []
    requirement_candidates: list[Candidate] = []

    for source in sources:
        for candidate in parse_source(source):
            {
                "persona": persona_candidates,
                "jtbd": jtbd_candidates,
                "cuj": cuj_candidates,
                "decision": decision_candidates,
                "question": question_candidates,
                "requirement": requirement_candidates,
            }[candidate.kind].append(candidate)

    fixtures = load_catalog_fixtures(
        args.product_area,
        catalog_paths(args.catalog_source),
        include_synthetic=args.include_synthetic_catalog,
    )
    persona_reference = catalog_claims(fixtures, "persona")
    jtbd_reference = catalog_claims(fixtures, "jtbd")
    cuj_reference = catalog_claims(fixtures, "cuj")

    persona_claims = [claim_from_candidate(c, persona_reference) for c in persona_candidates]
    jtbd_claims = [claim_from_candidate(c, jtbd_reference) for c in jtbd_candidates]
    cuj_claims = [claim_from_candidate(c, cuj_reference) for c in cuj_candidates]

    all_claims = persona_claims + jtbd_claims + cuj_claims
    new_proposals = [claim for claim in all_claims if claim["newProposal"]]
    existing_matches = [claim for claim in all_claims if not claim["newProposal"]]
    target_audience_mode = "catalog-grounded" if existing_matches else "discovery"

    decision_informed = args.decision_informed or (decision_candidates[0].text if decision_candidates else
        f"Confirm the product decision this research informs for {args.feature or args.product_area}.")
    research_questions = [c.text for c in question_candidates] or [
        f"What evidence is needed to inform: {decision_informed}?"
    ]

    missing_context: list[str] = []
    if not persona_claims:
        missing_context.append("No persona candidate found in source documents; persona must be confirmed manually.")
    if new_proposals:
        missing_context.append(
            f"{len(new_proposals)} JTBD/CUJ/persona candidate(s) are new proposals and are not yet part of the approved Target Audience Catalog."
        )
    if not decision_candidates and not args.decision_informed:
        missing_context.append("Decision informed was not explicit in source documents; confirm before finalizing.")

    research_context: dict[str, Any] = {
        "workflow": args.workflow_hint,
        "productArea": args.product_area,
        "decisionInformed": decision_informed,
        "targetAudienceMode": target_audience_mode,
        "audienceResolutionRef": None,
        "sourceDocs": [s.display_path for s in sources],
        "researchQuestions": research_questions,
        "requirements": [
            {
                "text": candidate.text,
                "sourceRef": candidate.source_ref,
                "extractionStatus": candidate.extraction_status,
                "sourceExcerpt": candidate.source_excerpt,
            }
            for candidate in requirement_candidates
        ],
        "missingContext": missing_context,
        "audienceContext": {
            "primaryPersona": persona_claims[0] if persona_claims else None,
            "secondaryPersonas": persona_claims[1:],
            "jtbd": jtbd_claims,
            "cuj": cuj_claims,
        },
        "newJtbdCujProposals": new_proposals,
        "sourceDocumentIntake": {
            "status": "draft",
            "documents": [
                {"path": s.display_path, "type": s.source_type, "extractionMethod": s.extraction_method, "sha256": s.sha256}
                for s in sources
            ],
            "personaCandidateCount": len(persona_claims),
            "jtbdCandidateCount": len(jtbd_claims),
            "cujCandidateCount": len(cuj_claims),
            "newProposalCount": len(new_proposals),
            "existingMatchCount": len(existing_matches),
            "limitations": [
                "Extraction uses deterministic labels/headings and conservative prose heuristics; inferred and uncertain claims require review.",
                "New JTBD/CUJ/persona proposals must be reviewed before being added to the Target Audience Catalog.",
                "Existing matches are still needs-confirmation until a human explicitly confirms them.",
                "Synthetic example fixtures are never treated as approved catalog data.",
            ],
        },
    }

    audience_proposal: dict[str, Any] = {
        "mode": target_audience_mode,
        "productArea": args.product_area,
        "featureOrProblemSpace": args.feature or args.product_area,
        "audienceContext": {
            "primaryPersona": persona_claims[0] if persona_claims else {
                "text": "Persona to be discovered.",
                "status": "to-be-discovered",
                "confidence": "low",
                "sourceRefs": [],
            },
            "secondaryPersonas": persona_claims[1:],
            "jtbd": jtbd_claims,
            "cuj": cuj_claims,
        },
        "ambiguities": [],
        "missingContext": missing_context,
        "allowedArtifacts": ["discovery guide", "research plan (draft)"] if new_proposals else ["research plan", "testing guide"],
        "blockedArtifacts": ["official Target Audience Catalog update without human review"],
        "humanReviewRequired": True,
        "proposedFromSourceDocs": [s.display_path for s in sources],
    }

    return research_context, audience_proposal


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a draft research context from PRD/RFC source documents.")
    parser.add_argument("--source-doc", action="append", required=True, help="Markdown, text, or DOCX source. May be repeated.")
    parser.add_argument("--product-area", required=True)
    parser.add_argument("--feature", help="Feature or problem space, if known.")
    parser.add_argument("--decision-informed", help="Override the extracted/inferred decision statement.")
    parser.add_argument("--workflow-hint", default="research-plan", help="Downstream workflow this context is intended for.")
    parser.add_argument(
        "--catalog-source",
        action="append",
        help=(
            "Approved catalog JSON file or directory. May be repeated. "
            "Defaults to target-audience/source and target-audience/index; examples are excluded."
        ),
    )
    parser.add_argument(
        "--include-synthetic-catalog",
        action="store_true",
        help="Allow synthetic fixtures for tests/demos. Never use this for real catalog decisions.",
    )
    parser.add_argument("--output", required=True, help="Path to write the draft research context JSON.")
    parser.add_argument("--audience-proposal-output", required=True, help="Path to write the audience proposal JSON.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        research_context, audience_proposal = build_context(args)
    except (OSError, ValueError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from exc

    audience_path = Path(args.audience_proposal_output).expanduser().resolve()
    write_json(audience_path, audience_proposal)
    research_context["audienceResolutionRef"] = workspace_display_path(audience_path)

    output_path = Path(args.output).expanduser().resolve()
    write_json(output_path, research_context)

    intake = research_context["sourceDocumentIntake"]
    print(f"Drafted research context: {output_path}")
    print(f"Audience proposal: {audience_path}")
    print(
        f"JTBD/CUJ/persona candidates: {intake['jtbdCandidateCount'] + intake['cujCandidateCount'] + intake['personaCandidateCount']} "
        f"({intake['existingMatchCount']} existing match(es), {intake['newProposalCount']} new proposal(s) requiring review)"
    )


if __name__ == "__main__":
    main()
