# clickqt

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/dokempf/clickqt/ci.yml?branch=main)](https://github.com/dokempf/clickqt/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/clickqt)](https://pypi.org/project/clickqt/)

`clickqt` generates Qt GUIs from `click` commands. Your `click` CLI remains the single source of truth, your users get the benefit from a GUI.

## Feature List

- Build a GUI automatically from `click` CLIs
- Launch GUIs for already installed CLIs (or from a Python file) via `clickqtfy`.
- Ship a GUI for your Python package with three lines of code
- Map common `click` types to Qt widgets, including `bool`, `int`, `float`, `str`, `Choice`, `DateTime`, `Path`, `File`, tuple, `nargs`, and `multiple`.
- Support for hierarchically nested `click.Group`s
- Carry over defaults, required flags, callbacks, and envvar-based initialization.
- Execute your command from the GUI and stream stdout/stderr to an in-app terminal panel.
- Export the current GUI state as a shell command and import command lines from the clipboard.
- Support option grouping headers from `click-option-group`.

## Installation instructions

`clickqt` requires Python `>=3.10`.

Install from PyPI:

```bash
python -m pip install clickqt
```

Install from conda-forge:

```bash
conda install -c conda-forge clickqt
```

Install for local development:

```bash
python -m pip install --editable .[tests]
pre-commit install
```

## Usage for end users (via `clickqtfy`)

Generate a GUI from an installed entry point:

```bash
clickqtfy ENTRYPOINT
```

Generate a GUI from a Python file and a `click` command object name:

```bash
clickqtfy path/to/module.py COMMAND_FUNCTION
```

In the generated GUI:

- `Run` executes the current command.
- `Stop` requests interruption of a running command.
- `Copy-To-Clipboard` exports the current command line.
- `Import-From-Clipboard` parses a command line and updates widgets.

## Usage for library maintainers

Expose a GUI to your users via the `qtgui_from_click` function:

```python
import click
from clickqt import qtgui_from_click


@click.command()
@click.option("--count", default=1, type=int)
@click.argument("name")
def greet(count: int, name: str) -> None:
    for _ in range(count):
        click.echo(f"Hello {name}")


greet_gui = qtgui_from_click(
    greet,
    application_name="Greeter",
    invocation_command="greet",
)
```

Publish CLI and GUI entry points in `pyproject.toml`:

```toml
[project.scripts]
greet = "yourpkg.cli:greet"

[project.gui-scripts]
greet_gui = "yourpkg.cli:greet_gui"
```

For custom `click.ParamType`, provide a widget/getter/setter mapping:

```python
from PySide6.QtWidgets import QLineEdit

custom_mapping = {
    MyParamType: (
        QLineEdit,
        lambda w: w.widget.text(),
        lambda w, v: w.widget.setText(str(v)),
    )
}
gui = qtgui_from_click(cmd, custom_mapping=custom_mapping)
```

## Constraints

- Unknown custom `click.ParamType` falls back to a text field unless you provide `custom_mapping`.
- `click-option-group` is displayed visually, but group relationship rules are not enforced by `clickqt`.
- Parameters with `hidden=True` are currently still rendered in the GUI.
- `clickqt` executes command callbacks directly; advanced custom `click.Command`/`click.Context` behavior may differ from CLI invocation.
- Multi-value envvar handling can differ from Click's type-specific envvar splitting behavior.

## Licensing

MIT License. See `LICENSE.md`.
