# Contributing to clickqt

Thanks for your interest in improving `clickqt`.

## Start with an issue

Before implementing non-trivial changes, please open (or comment on) a GitHub issue first.
This helps us align on behavior, scope, and CLI/GUI parity expectations before coding starts.

## Development installation

```bash
git clone git@github.com:dokempf/clickqt.git
cd clickqt
python -m pip install --editable .[tests]
pre-commit install
```

If you also want to verify example entry points locally:

```bash
python -m pip install --editable ./example
```

## Run checks

```bash
python -m pytest
python -m pytest --cov=clickqt --cov-branch --cov-report=term-missing --cov-report=xml
pre-commit run --all-files
```

## Contribution expectations

- Keep pull requests focused on one behavior change
- Add regression tests for bug fixes and mapping/GUI behavior changes
- Preserve CLI/GUI behavior parity unless a limitation is explicitly documented
