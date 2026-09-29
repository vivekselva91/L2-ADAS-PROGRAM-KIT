.PHONY: install dev test lint validate trace gate reports clean

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check src tests

validate:
	adaskit validate

trace:
	adaskit trace

gate:
	adaskit gate

reports:
	adaskit all --out out/

clean:
	rm -rf out .pytest_cache .ruff_cache build dist *.egg-info
	find . -name __pycache__ -type d -exec rm -rf {} +
