ROOT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
VENV_PYTHON := $(ROOT_DIR)/.venv/bin/python

.PHONY: setup

setup:
	@test -x "$$(command -v python3.12)" || (echo "python3.12 is required" >&2; exit 1)
	@test -x "$(VENV_PYTHON)" || python3.12 -m venv "$(ROOT_DIR)/.venv"
	"$(VENV_PYTHON)" -m pip install --upgrade pip
	"$(VENV_PYTHON)" -m pip install --editable "$(ROOT_DIR)/packages/core[dev]"
