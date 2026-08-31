# Contributing

Thank you for considering a contribution to Mini Search Engine.

## Local setup

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
```

## Quality checks

Run the same checks used in CI before opening a pull request:

```bash
ruff check .
pytest --cov=mini_search_engine --cov-report=term-missing
```

Please keep changes focused, add tests for new behavior, and update the documentation when a public
interface changes.
