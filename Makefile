# MaskPersona AI: human entry points. Both `make install` and INSTALL.md (agent path)
# run the SAME ordered installer steps, so the result is identical on every machine.

PY ?= python3

.PHONY: help install new demo demo-visual ingest eval audit verify clean

help:
	@echo "MaskPersona AI"
	@echo "  make install   deterministic setup (deps only; no account or access token)"
	@echo "  make new       create a new persona (you give a name)"
	@echo "  make demo      run the fictional John Doe demo offline (no downloads)"
	@echo "  make demo-visual [NAME=... IMAGE=photo.jpg]   animated terminal face demo"
	@echo "  make ingest    run/resume the ingestion pipeline for the current persona"
	@echo "  make eval      generate domain-adapted questions and score the persona"
	@echo "  make audit     run genericity + GDPR + legal + text-classifier audits"
	@echo "  make verify    run the test suite"

install:
	$(PY) -m installer.bootstrap

new:
	$(PY) -m installer.bootstrap --onboard

demo:
	$(PY) -m installer.bootstrap --demo

demo-visual:
	pip install "rich>=13,<15" -q
	$(PY) demo/visual_demo.py "$(or $(NAME),John Doe)" $(if $(IMAGE),--image $(IMAGE),)

ingest:
	@test -n "$(PERSONA)" || { echo "usage: make ingest PERSONA=path/to/persona.yaml (offline demo: make demo)"; exit 1; }
	$(PY) -m pipeline.run_ingest --persona "$(PERSONA)" --resume

eval:
	@test -n "$(PERSONA)" || { echo "usage: make eval PERSONA=path/to/persona.yaml"; exit 1; }
	$(PY) -m eval.run_eval --persona "$(PERSONA)"

audit:
	$(PY) -m audit.run_audits

verify:
	$(PY) -m pytest -q

clean:
	rm -rf work/* && touch work/.gitkeep
