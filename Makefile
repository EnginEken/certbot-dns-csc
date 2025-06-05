.PHONY: help install install-dev test test-verbose test-coverage clean build upload upload-test lint format check integration-test

help:
	@echo "Available commands:"
	@echo "  install        Install the package"
	@echo "  install-dev    Install the package in development mode with dev dependencies"
	@echo "  test           Run unit tests"
	@echo "  test-verbose   Run unit tests with verbose output"
	@echo "  test-coverage  Run tests with coverage report"
	@echo "  clean          Clean build artifacts"
	@echo "  build          Build the package"
	@echo "  upload-test    Upload to Test PyPI"
	@echo "  upload         Upload to PyPI"
	@echo "  lint           Run linting checks"
	@echo "  format         Format code with black"
	@echo "  check          Run all checks (lint, format, test)"
	@echo "  integration-test  Run integration tests"

install:
	pip install .

install-dev:
	pip install -e .[dev]

test:
	python3 -m pytest tests/

test-verbose:
	python3 -m pytest -v tests/

test-coverage:
	python3 -m pytest --cov=certbot_dns_csc --cov-report=html --cov-report=term tests/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	rm -rf */__pycache__/
	rm -rf */*/__pycache__/
	rm -rf htmlcov/
	rm -rf .coverage

build: clean
	python3 -m build

upload-test: build
	python3 -m twine upload --repository testpypi dist/*

upload: build
	python3 -m twine upload dist/*

lint:
	python3 -m flake8 certbot_dns_csc tests
	python3 -m pylint certbot_dns_csc

format:
	python3 -m black certbot_dns_csc tests

check: lint test

integration-test:
	python3 test_integration.py
