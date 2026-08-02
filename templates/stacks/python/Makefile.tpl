.PHONY: test lint

test:
	python -m pytest tests -q

lint:
	ruff check src tests
