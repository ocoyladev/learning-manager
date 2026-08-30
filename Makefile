ROOT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
VENV_PYTHON := $(ROOT_DIR)/.venv/bin/python

.PHONY: setup up down check test stub-api eval-replay eval-live record simulate trajectories

setup:
	@test -x "$$(command -v python3.12)" || (echo "python3.12 is required" >&2; exit 1)
	@test -x "$(VENV_PYTHON)" || python3.12 -m venv "$(ROOT_DIR)/.venv"
	"$(VENV_PYTHON)" -m pip install --upgrade pip
	"$(VENV_PYTHON)" -m pip install --editable "$(ROOT_DIR)/packages/core[dev]"

up:
	docker compose up -d --build
	docker compose ps

down:
	docker compose down

check:
	cd "$(ROOT_DIR)/packages/core" && "$(VENV_PYTHON)" -m mypy learning_manager
	cd "$(ROOT_DIR)/packages/core" && "$(VENV_PYTHON)" -m ruff check .
	cd "$(ROOT_DIR)/packages/core" && "$(VENV_PYTHON)" -m ruff format --check .
	cd "$(ROOT_DIR)/packages/core" && "$(VENV_PYTHON)" -m pytest

test:
	cd "$(ROOT_DIR)/packages/core" && "$(VENV_PYTHON)" -m pytest

stub-api:
	cd "$(ROOT_DIR)" && PYTHONPATH="$(ROOT_DIR)/packages/core" "$(VENV_PYTHON)" -m learning_manager.api.stub --port 8001

eval-replay:
	cd "$(ROOT_DIR)" && PYTHONPATH="$(ROOT_DIR)/packages/core" LLM_MODE=replay "$(VENV_PYTHON)" -m eval.runner --name $(or $(NAME),replay)

eval-live:
	cd "$(ROOT_DIR)" && PYTHONPATH="$(ROOT_DIR)/packages/core" LLM_MODE=live "$(VENV_PYTHON)" -m eval.runner --name $(or $(NAME),live)

record:
	cd "$(ROOT_DIR)" && PYTHONPATH="$(ROOT_DIR)/packages/core" LLM_MODE=live "$(VENV_PYTHON)" -m learning_manager.cli record-cassettes

simulate:
	cd "$(ROOT_DIR)" && PYTHONPATH="$(ROOT_DIR)/packages/core" "$(VENV_PYTHON)" -m learning_manager.cli simulate-day --days $(or $(DAYS),5)

trajectories:
	cd "$(ROOT_DIR)" && PYTHONPATH="$(ROOT_DIR)/packages/core" "$(VENV_PYTHON)" -m learning_manager.cli export-trajectories --out trajectories/
