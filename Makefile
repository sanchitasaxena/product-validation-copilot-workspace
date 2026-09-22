.PHONY: install test smoke

PYTHON ?= .venv/bin/python

install:
	./setup.sh

test:
	$(PYTHON) -m unittest discover -s tests -v

smoke:
	$(PYTHON) tools/validate_context.py --input generators/xlsx/examples/synthetic_registry_artifact_approval_qa_context.json --type qa-context
	$(PYTHON) tools/run_research_workflow.py --workflow plan --input tests/fixtures/research-context.json --output /tmp/product-validation-research-plan.json
