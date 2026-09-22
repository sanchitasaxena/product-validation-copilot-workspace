import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


class WorkspaceSmokeTests(unittest.TestCase):
    def test_research_plan_workflow_creates_reviewable_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "plan.json"
            result = subprocess.run(
                [PYTHON, "tools/run_research_workflow.py", "--workflow", "plan",
                 "--input", "tests/fixtures/research-context.json", "--output", str(output)],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            artifact = json.loads(output.read_text())
            self.assertTrue(artifact["humanReviewRequired"])
            self.assertEqual(artifact["studies"][0]["researchQuestions"][0],
                             "Can administrators identify the approval state?")

    def test_schema_validator_accepts_research_context(self):
        result = subprocess.run(
            [PYTHON, "tools/validate_context.py", "--input", "tests/fixtures/research-context.json",
             "--type", "research-context", "--json"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_prd_source_ingestion_distinguishes_existing_and_new_jtbd_cuj(self):
        with tempfile.TemporaryDirectory() as directory:
            context_path = Path(directory) / "research-context.json"
            audience_path = Path(directory) / "audience-proposal.json"
            result = subprocess.run(
                [PYTHON, "tools/build_research_context_from_sources.py",
                 "--source-doc", "examples/research-source-intake/sources/registry-audit-trail-prd.md",
                 "--product-area", "HCP Terraform Registry",
                 "--feature", "Registry artifact approval workflow",
                 "--catalog-source", "examples/research-source-intake/sources/target-audience-catalog.synthetic.json",
                 "--include-synthetic-catalog",
                 "--output", str(context_path),
                 "--audience-proposal-output", str(audience_path)],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            context = json.loads(context_path.read_text())
            jtbd = context["audienceContext"]["jtbd"]
            existing = [c for c in jtbd if not c["newProposal"]]
            new = [c for c in jtbd if c["newProposal"]]
            self.assertEqual(len(existing), 1)
            self.assertEqual(len(new), 1)
            self.assertIn("audit trail", new[0]["text"])
            self.assertEqual(context["targetAudienceMode"], "catalog-grounded")

    def test_source_doc_chain_produces_valid_testing_guide_and_discovery_guide(self):
        with tempfile.TemporaryDirectory() as directory:
            for workflow in ("testing-guide", "discovery-guide"):
                output_dir = Path(directory) / workflow
                result = subprocess.run(
                    [PYTHON, "tools/run_research_workflow.py",
                     "--workflow", workflow,
                     "--source-doc", "examples/research-source-intake/sources/registry-audit-trail-prd.md",
                     "--product-area", "HCP Terraform Registry",
                     "--feature", "Registry artifact approval workflow",
                     "--catalog-source", "examples/research-source-intake/sources/target-audience-catalog.synthetic.json",
                     "--include-synthetic-catalog",
                     "--output-dir", str(output_dir)],
                    cwd=ROOT, capture_output=True, text=True, check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                artifact = json.loads((output_dir / f"{workflow}.json").read_text())
                self.assertTrue(artifact["humanReviewRequired"])
                validation = json.loads((output_dir / f"{workflow}.validation.json").read_text())
                self.assertEqual(validation["errors"], [])
                self.assertTrue((output_dir / "review-summary.md").exists())


if __name__ == "__main__":
    unittest.main()
