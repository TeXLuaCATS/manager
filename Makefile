test:
	uv run --isolated --python=3.12 pytest -vv
.PHONY: test

install:
	uv sync
	uv pip install --editable .
.PHONY: install
