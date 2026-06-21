# Contributing to squidrouter-py

Thanks for your interest in improving `squidrouter-py`!

## Development setup

The project uses a `src/` layout and the `dev` optional-dependency group for
tooling.

```bash
git clone https://github.com/robertruben98/squidrouter-py.git
cd squidrouter-py
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Quality gates

All of these must pass before a change is merged. They are also enforced in CI
across Python 3.9–3.13.

```bash
ruff check .          # lint
mypy                  # static types (strict)
pytest                # tests (respx-mocked, no network)
```

## Test-driven development

This project is developed test-first:

1. Write a failing test that describes the desired behavior.
2. Watch it fail for the expected reason.
3. Write the minimal code to make it pass.
4. Refactor while keeping everything green.

Unit tests must not hit the network — use `respx` to mock the Squid API. The
live integration test in `tests/test_live_integration.py` is skipped by default
and only runs when `SQUID_INTEGRATOR_ID` is set in the environment.

## Conventions

- Python **3.9** is a supported runtime. Do not use PEP 604 `X | None` syntax in
  runtime annotations; use `typing.Optional` / `typing.Union`. Bare `list[...]`
  / `dict[...]` are fine because every module uses
  `from __future__ import annotations`.
- Public methods and models carry Google-style docstrings and pydantic
  `Field(description=...)`.
- Keep `CHANGELOG.md` up to date under the `Unreleased` heading.

## Releasing

Releases are published to PyPI via OIDC Trusted Publishing when a GitHub Release
is published. Bump the version in `pyproject.toml` and `squidrouter.__version__`,
move the changelog entries under a new version heading, then create the release.
