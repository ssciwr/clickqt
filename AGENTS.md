# Repository Guidelines

## Project Mission
- `clickqt` turns `click` CLIs into Qt GUIs while keeping the CLI definition as the source of truth.
- Prefer changes that preserve behavior parity between the original CLI and the generated GUI.

## Project Structure & Module Organization
- Core library code lives in `clickqt/`.
- `clickqt/core/` contains command parsing, execution, and GUI orchestration logic.
- `clickqt/widgets/` contains Qt widget implementations and widget utilities; image assets are in `clickqt/images/`.
- Tests live in `tests/` and are organized by behavior (`test_gui.py`, `test_types.py`, `test_execution.py`, etc.).
- Documentation sources are in `doc/` (Sphinx), and runnable examples are in `example/`.

## Build, Test, and Development Commands
- Install for development: `python -m pip install --editable .[tests]`
- Ensure that pre-commit is installed in the local Git repository: `pre-commit install`
- Run tests: `python -m pytest`
- Run a focused test file: `python -m pytest tests/test_gui.py`
- Build docs locally: `python -m pip install --editable .[docs] && make -C doc html`
- Install the example package (entry-point checks): `python -m pip install --editable ./example`
- Run linting/formatting hooks across files: `pre-commit run --all-files`

## Coding Style & Naming Conventions
- Make sure that any proposed changes pass all pre-commit hooks.
- Target Python `>=3.10`; use 4-space indentation.
- Use `snake_case` for functions/variables and `PascalCase` for classes.
- Keep modules focused by feature area (`core`, `widgets`, `tests`).
- Prefer explicit, readable logic over compact one-liners, especially in GUI/type-mapping paths.

## Testing Guidelines
- Test framework: `pytest` (with `pytest-qt` and `pytest-xvfb` for GUI coverage).
- Place tests in `tests/` and name files/functions with `test_` prefixes.
- Prefer adding tests to existing behavior-focused modules (e.g., `test_execution.py`, `test_types.py`) instead of creating new one-off test files.
- Add regression tests for bug fixes and widget/type mapping changes.
- Run the full suite before opening a PR; use targeted runs while iterating.
- Assert **intent and contract** (user-visible behavior, CLI/GUI parity, error semantics), not incidental implementation details.
- Before adding tests for uncovered code, verify that the functionality is actually used by the project/runtime paths.
  If functionality is unused, prefer removing dead code (and any related tests) instead of adding new tests for it.
- If code behavior appears to violate the likely intent, pause and confirm expected behavior before codifying it in tests.

## Coverage Testing (pytest-cov)
- Run coverage checks for all code changes; do not treat coverage as optional.
- Use `pytest-cov` with branch coverage:
  `python -m pytest --cov=clickqt --cov-branch --cov-report=term-missing --cov-report=xml`
- Review uncovered lines in the terminal report (`term-missing`) and use `coverage.xml` for precise
  line-level analysis in tooling.
- Prioritize tests for changed lines and behavior paths; the goal is very high diff coverage on every
  change.
- If coverage drops, add or update tests before merging unless there is a documented, explicit
  exception.

## Commit & Pull Request Guidelines
- Follow existing history style: short, imperative commit subjects (e.g., `Fix import logic for Python 3.12`).
- Keep commits focused; separate refactors from behavior changes.
- PRs should include: clear description, linked issue (if any), and test updates for behavior changes.
- If UI behavior changes, include screenshots/GIFs (similar to `readme_resources/` usage).
- Ensure CI passes across supported Python versions and OS targets before merge.
- Ensure local changes pass `pre-commit run`; if hooks auto-fix files on first run, re-run until clean.
