.PHONY: all install install-dev format lint clean check help venv venv-create venv-remove venv-activate

all: help

PYTHON := python
PIP := $(PYTHON) -m pip
VENV_NAME := .venv
VENV_BIN := $(VENV_NAME)/bin
VENV_PYTHON := $(VENV_BIN)/python
VENV_PIP := $(VENV_PYTHON) -m pip

help:
	@echo "Available targets:"
	@echo "  install       - Install dependencies"
	@echo "  install-dev   - Install development dependencies"
	@echo "  format        - Format code using ruff"
	@echo "  lint          - Run linting checks"
	@echo "  check         - Run all code quality checks"
	@echo "  clean         - Remove generated files"
	@echo "  venv-create   - Create virtual environment"
	@echo "  venv-remove   - Remove virtual environment"
	@echo "  venv-activate - Print commands to activate virtual environment"
	@echo "  help          - Show the help message"

venv-create:
	@echo ">> Creating virtual environment..."
	@rm -rf $(VENV_NAME)
	$(PYTHON) -m venv $(VENV_NAME)
	@echo ">> Virtual environment created at $(VENV_NAME)"
	@echo ">> To activate, run: source $(VENV_NAME)/bin/activate"

venv-remove:
	@echo ">> Removing virtual environment..."
	@rm -rf $(VENV_NAME)
	@echo ">> Virtual environment removed."

venv-activate:
	@echo ">> To activate the virtual environment, run:"
	@echo "source $(VENV_NAME)/bin/activate"
	@echo
	@echo ">> To deactivate, run:"
	@echo "deactivate"

install:
	@echo ">> Installing dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install -e .

install-dev: venv-create
	@echo ">> Installing development dependencies..."
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -e ".[dev]"
	@echo
	@echo ">> Development environment setup complete."
	@echo ">> To activate the virtual environment, run: source $(VENV_NAME)/bin/activate"

check: lint
	@echo ">> Running code quality checks..."
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

format:
	@echo ">> Formatting code..."
	$(PYTHON) -m ruff check . --fix
	$(PYTHON) -m ruff format .

lint:
	@echo ">> Running linter..."
	$(PYTHON) -m ruff check .

clean: venv-remove
	@echo ">> Cleaning generated files..."
	@rm -rf .ipynb_checkpoints
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.py[cod]" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@find . -type d -name "*.egg" -exec rm -rf {} +
	@find . -type d -name ".ruff_cache" -exec rm -rf {} +
	@find . -type d -name ".coverage" -delete
	@find . -type d -name "htmlcov" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type f -name ".coverage" -delete


# test:
#   @echo ">> Running tests..."
#   $(PYTHON) -m pytest


# coverage:
#   @echo ">> Running tests with coverage..."
#   $(PYTHON) -m pytest --cov=here_is_package_name --cov-report=html
