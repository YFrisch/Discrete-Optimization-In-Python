.PHONY: help venv install lab lint format test precommit

help:
	@echo "Targets:"
	@echo "  make venv      - create .venv"
	@echo "  make install   - install deps into .venv"
	@echo "  make lab       - run jupyter lab"
	@echo "  make lint      - ruff + black check"
	@echo "  make format    - ruff fix + black"
	@echo "  make test      - pytest"
	@echo "  make precommit - install pre-commit hooks"

venv:
	python3 -m venv .venv

install: venv
	. .venv/bin/activate && python3 -m pip install -U pip && pip install -r requirements.txt

lab:
	. .venv/bin/activate && jupyter lab

lint:
	. .venv/bin/activate && ruff check . && black --check .

format:
	. .venv/bin/activate && ruff check . --fix && black .

test:
	. .venv/bin/activate && pytest -q

precommit:
	. .venv/bin/activate && pre-commit install