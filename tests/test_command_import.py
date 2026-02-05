import io
import typing as t
import click
from PySide6.QtWidgets import QApplication, QTabWidget
import pytest
import clickqt.widgets
from tests.testutils import ClickAttrs


def prepare_execution(cmd: click.Command, cmd_group_name: click.Group):
    return cmd_group_name.name + ":" + cmd.name


def textio_to_str_to_list(vals):
    if isinstance(vals, io.TextIOWrapper):
        return vals.name
    if isinstance(vals, (list, tuple)):
        return [textio_to_str_to_list(v) for v in vals]
    return vals


@pytest.mark.parametrize(
    ("click_attrs", "value", "fake_value"),
    [
        (ClickAttrs.intfield(), 12, 4),
        (ClickAttrs.textfield(), "test", "main --p test"),
        (ClickAttrs.realfield(), 0.8, 1.3),
        (ClickAttrs.passwordfield(), "abc", "main --p abc"),
        (ClickAttrs.checkbox(), True, False),
        (ClickAttrs.checkbox(), False, True),
        (ClickAttrs.intrange(maxval=2, clamp=True), 1, 0),
        (ClickAttrs.floatrange(maxval=2.05, clamp=True), 1.3, 0),
        (
            ClickAttrs.combobox(
                choices=["A", "B", "C"], case_sensitive=False, confirmation_prompt=True
            ),
            "B",
            "A",
        ),
        (
            ClickAttrs.combobox(choices=["A", "B", "C"], case_sensitive=False),
            "B",
            "A",
        ),
        (
            ClickAttrs.checkable_combobox(choices=["A", "B", "C"]),
            ["B", "C"],
            ["A"],
        ),
        (ClickAttrs.checkable_combobox(choices=["A", "B", "C"]), ["A"], ["B"]),
        (
            ClickAttrs.checkable_combobox(choices=["A", "B", "C"]),
            ["A", "B", "C"],
            ["C"],
        ),
        (
            ClickAttrs.tuple_widget(types=(str, int, float)),
            ["t", 1, -2.0],
            ["\n", 3, -1.2],
        ),
        (
            ClickAttrs.nvalue_widget(type=(str, int)),
            [["a", 12], ["b", 11]],
            [["ddd", 22]],
        ),
        (
            (
                ClickAttrs.multi_value_widget(nargs=2),
                ["foo", "t"],
                ["1", "-- ~ \0"],
            )
        ),
        (
            ClickAttrs.multi_value_widget(nargs=2, default=["A", "B"]),
            ["A", "C"],
            ["X", "X"],
        ),
        (
            ClickAttrs.nvalue_widget(type=(click.types.File(), int)),
            [[".gitignore", 12], ["setup.py", -1]],
            [["setup.py", 10], ["README.md", 1]],
        ),
    ],
)
def test_import_ep(click_attrs: dict, value: t.Any, fake_value: t.Any):
    param = click.Option(param_decls=["--p"], required=True, **click_attrs)
    cli = click.Command("main", params=[param])
    control = clickqt.qtgui_from_click(cli)
    control.set_ep_or_path("main")
    control.set_is_ep(True)
    widget = control.widget_registry[cli.name][param.name]
    widget.set_value(value)

    # copy cmd string to clipboard
    control.construct_command_string()

    assert control.is_ep is True
    assert control.ep_or_path == "main"
    assert control.cmd == cli

    widget.set_value(fake_value)
    val, _ = widget.get_value()
    val = textio_to_str_to_list(val)
    assert val == fake_value

    # read the cmd from clipboard
    control.import_cmdline()
    val, _ = widget.get_value()
    val = textio_to_str_to_list(val)
    assert val == value


@pytest.mark.parametrize(
    ("is_ep", "ep_or_path", "clipboard_text", "error_message"),
    [
        (
            True,
            "main",
            "wrong-ep cmd --p 13",
            "missing or wrong entry point name",
        ),
        (
            False,
            "example/example/main.py",
            "cmd --p 13",
            "missing or wrong file/function combination",
        ),
        (
            False,
            "example/example/main.py",
            "python wrong.py cmd --p 13",
            "missing or wrong file/function combination",
        ),
    ],
)
def test_import_cmdline_sanity_errors_do_not_mutate_ui(
    is_ep: bool, ep_or_path: str, clipboard_text: str, error_message: str, capsys
):
    cli = click.Group("cli")
    command = click.Command(
        "cmd", params=[click.Option(param_decls=["--p"], required=True, type=click.INT)]
    )
    cli.add_command(command)
    cli.add_command(click.Command("other"))
    control = clickqt.qtgui_from_click(cli)
    control.set_ep_or_path(ep_or_path)
    control.set_is_ep(is_ep)

    tabs = control.gui.widgets_container
    assert isinstance(tabs, QTabWidget)
    other_idx = [tabs.tabText(i) for i in range(tabs.count())].index("other")
    tabs.setCurrentIndex(other_idx)

    widget = control.widget_registry["cli:cmd"]["p"]
    widget.set_value(99)

    QApplication.clipboard().setText(clipboard_text)
    control.import_cmdline()

    assert tabs.tabText(tabs.currentIndex()) == "other"
    assert widget.get_value()[0] == 99
    assert error_message in capsys.readouterr().err


def test_import_file_mode_for_simple_command_roundtrip():
    param = click.Option(param_decls=["--p"], required=True, type=click.INT)
    cli = click.Command("cli", params=[param])
    control = clickqt.qtgui_from_click(cli)
    control.set_ep_or_path("example/example/main.py")
    control.set_is_ep(False)
    widget = control.widget_registry[cli.name][param.name]
    widget.set_value(12)

    control.construct_command_string()
    widget.set_value(4)
    control.import_cmdline()

    assert widget.get_value()[0] == 12


def test_import_file_mode_for_nested_group_sets_selected_command_widgets():
    shared_name_option = click.Option(
        param_decls=["--name"], required=True, type=click.STRING
    )
    add_cmd = click.Command("add", params=[shared_name_option])
    list_cmd = click.Command(
        "list",
        params=[click.Option(param_decls=["--name"], required=True, type=click.STRING)],
    )
    users_group = click.Group("users", commands=[add_cmd, list_cmd])
    cli = click.Group(
        "cli", commands=[users_group, click.Command("rootcmd", params=[])]
    )
    control = clickqt.qtgui_from_click(cli)
    control.set_ep_or_path("example/example/main.py")
    control.set_is_ep(False)

    add_widget = control.widget_registry["cli:users:add"]["name"]
    list_widget = control.widget_registry["cli:users:list"]["name"]
    add_widget.set_value("before-add")
    list_widget.set_value("before-list")

    QApplication.clipboard().setText(
        "python example/example/main.py users add --name imported-name"
    )
    control.import_cmdline()

    top_tabs = control.gui.widgets_container
    assert isinstance(top_tabs, QTabWidget)
    assert top_tabs.tabText(top_tabs.currentIndex()) == "users"
    user_tabs = top_tabs.currentWidget()
    assert isinstance(user_tabs, QTabWidget)
    assert user_tabs.tabText(user_tabs.currentIndex()) == "add"
    assert add_widget.get_value()[0] == "imported-name"
    assert list_widget.get_value()[0] == "before-list"
