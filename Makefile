.PHONY: help venv install lab lint format test precommit

VENV := .venv
PYTHON := $(VENV)/bin/python

help:
	@echo "Targets:"
	@echo "  make venv      - create .venv"
	@echo "  make install   - install deps into .venv"
	@echo "  make lab       - run jupyter lab"
	@echo "  make lint      - ruff + black check"
	@echo "  make format    - ruff fix + black"
	@echo "  make test      - pytest"
	@echo "  make precommit - install pre-commit hooks"

venv: $(PYTHON)

$(PYTHON):
	python3 -m venv $(VENV)

install: venv
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev,docs]"

lab:
	$(PYTHON) -m jupyter lab

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m black --check .

format:
	$(PYTHON) -m ruff check . --fix
	$(PYTHON) -m black .

test:
	$(PYTHON) -m pytest -q

precommit:
	$(PYTHON) -m pre_commit install
