import typing as t
import enum
import pytest
import click
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QClipboard
import clickqt.widgets
from tests.testutils import ClickAttrs


class EPTYPE(enum.Enum):
    EP = 0
    FILE = 1
    EPGROUP = 2
    FILEGROUP = 3


def prepare_execution(cmd: click.Command, cmd_group_name: click.Group):
    return cmd_group_name.name + ":" + cmd.name


@pytest.mark.parametrize(
    "eptype", [EPTYPE.EP, EPTYPE.FILE, EPTYPE.EPGROUP, EPTYPE.FILEGROUP]
)
@pytest.mark.parametrize(
    ("click_attrs", "value", "expected_params"),
    [
        (ClickAttrs.intfield(), 12, "--p 12"),
        (ClickAttrs.textfield(), "test", "--p test"),
        (ClickAttrs.realfield(), 0.8, "--p 0.8"),
        (ClickAttrs.passwordfield(), "abc", "--p abc"),
        (ClickAttrs.checkbox(), True, "--p True"),
        (ClickAttrs.checkbox(), False, "--p False"),
        (ClickAttrs.intrange(maxval=2, clamp=True), 5, "--p 2"),
        (ClickAttrs.floatrange(maxval=2.05, clamp=True), 5, "--p 2.05"),
        (
            ClickAttrs.combobox(
                choices=["A", "B", "C"], case_sensitive=False, confirmation_prompt=True
            ),
            "B",
            "--p B",
        ),
        (
            ClickAttrs.combobox(choices=["A", "B", "C"], case_sensitive=False),
            "B",
            "--p B",
        ),
        (ClickAttrs.checkable_combobox(choices=["A", "B", "C"]), [], ""),
        (
            ClickAttrs.checkable_combobox(choices=["A", "B", "C"]),
            ["B", "C"],
            "--p B --p C",
        ),
        (ClickAttrs.checkable_combobox(choices=["A", "B", "C"]), ["A"], "--p A"),
        (
            ClickAttrs.checkable_combobox(choices=["A", "B", "C"]),
            ["A", "B", "C"],
            "--p A --p B --p C",
        ),
        (
            ClickAttrs.tuple_widget(types=(str, int, float)),
            ("t", 1, -2.0),
            "--p t 1 -2.0",
        ),
        (
            ClickAttrs.nvalue_widget(type=(str, int)),
            [["a", 12], ["b", 11]],
            "--p a 12 --p b 11",
        ),
        (
            ClickAttrs.multi_value_widget(nargs=2),
            ["foo", "bar"],
            "--p foo bar",
        ),
        (
            ClickAttrs.multi_value_widget(nargs=2, default=["A", "B"]),
            ["A", "C"],
            "--p A C",
        ),
        (
            ClickAttrs.nvalue_widget(type=(click.types.File(), int)),
            [[".gitignore", 12], ["setup.py", -1]],
            "--p .gitignore 12 --p setup.py -1",
        ),
        (ClickAttrs.countwidget(), 3, "--p --p --p"),
    ],
)
def test_command(eptype: EPTYPE, click_attrs: dict, value: t.Any, expected_params: str):
    is_ep = eptype in [EPTYPE.EP, EPTYPE.EPGROUP]
    is_group = eptype in [EPTYPE.EPGROUP, EPTYPE.FILEGROUP]
    param = click.Option(param_decls=["--p"], required=True, **click_attrs)
    if eptype == EPTYPE.EP:
        cli = click.Command("main", params=[param])
        ep_or_path = "main"
        prefix = ep_or_path
    elif eptype == EPTYPE.FILE:
        cli = click.Command("cli", params=[param])
        ep_or_path = "example/example/main.py"
        prefix = f"python {ep_or_path} {cli.name}"
    elif eptype == EPTYPE.EPGROUP:
        cli = click.Group("cli")
        cmd = click.Command("cmd", params=[param])
        cli.add_command(cmd)
        ep_or_path = "main"
        prefix = ep_or_path + " cmd"
    elif eptype == EPTYPE.FILEGROUP:
        cli = click.Group("cli")
        cmd = click.Command("cmd", params=[param])
        cli.add_command(cmd)
        ep_or_path = "example/example/main.py"
        prefix = f"python {ep_or_path} {cmd.name}"
    else:
        raise ValueError(f"Unknown ep type: '{eptype}'")
    expected_output = (prefix + " " + expected_params).rstrip()
    control = clickqt.qtgui_from_click(cli)
    control.set_ep_or_path(ep_or_path)
    control.set_is_ep(is_ep)
    widget_registry_key = prepare_execution(cmd, cli) if is_group else cli.name
    widget = control.widget_registry[widget_registry_key][param.name]
    widget.set_value(value)

    control.construct_command_string()

    assert control.is_ep is is_ep
    assert control.ep_or_path == ep_or_path
    assert control.cmd == cli

    # Simulate clipboard behavior using QApplication.clipboard()
    clipboard = QApplication.clipboard()
    assert clipboard.text(QClipboard.Clipboard) == expected_output


def test_command_uses_explicit_invocation_command():
    param = click.Option(param_decls=["--p"], required=True, type=click.STRING)
    cli = click.Command("main", params=[param])
    control = clickqt.qtgui_from_click(cli, invocation_command="uv run bio-cli")
    control.set_is_ep(True)

    widget = control.widget_registry[cli.name][param.name]
    widget.set_value("value")
    control.construct_command_string()

    clipboard = QApplication.clipboard()
    assert clipboard.text(QClipboard.Clipboard) == "uv run bio-cli --p value"
