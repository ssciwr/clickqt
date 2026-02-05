from __future__ import annotations

import os
import typing as t

import pytest
import click
from click.testing import CliRunner
from pytest import MonkeyPatch
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox, QInputDialog, QSizePolicy

import clickqt.widgets
from clickqt.core.error import ClickQtError
from tests.testutils import ClickAttrs, clcoancl, raise_, wait_process_Events

STATE: dict[str, t.Any] = {"clickqt_res": None}


def callback(p):
    if STATE["clickqt_res"] is None:
        STATE["clickqt_res"] = p
    return p


@pytest.mark.parametrize(
    ("error_type", "trigger", "raw_message", "expected_message"),
    [
        (ClickQtError.ErrorType.NO_ERROR, "value", "x", ""),
        (
            ClickQtError.ErrorType.CONFIRMATION_INPUT_NOT_EQUAL_ERROR,
            "password",
            "x",
            "Confirmation input (password) is not equal",
        ),
        (ClickQtError.ErrorType.ABORTED_ERROR, "value", "x", "Aborted!"),
        (
            ClickQtError.ErrorType.PROCESSING_VALUE_ERROR,
            "value",
            "boom",
            "Processing value error (value): boom",
        ),
        (
            ClickQtError.ErrorType.CONVERTING_ERROR,
            "value",
            "boom",
            "Converting error (value): boom",
        ),
        (
            ClickQtError.ErrorType.REQUIRED_ERROR,
            "value",
            "option",
            "Required error (value): option is empty",
        ),
        (ClickQtError.ErrorType.EXIT_ERROR, "value", "x", ""),
    ],
)
def test_clickqt_error_message_matches_error_intent(
    error_type: ClickQtError.ErrorType,
    trigger: str,
    raw_message: str,
    expected_message: str,
):
    error = ClickQtError(error_type, trigger, raw_message)

    assert error.message() == expected_message


def test_clickqt_error_unknown_type_raises_not_implemented():
    class UnknownErrorType:
        value = 99

    error = ClickQtError(UnknownErrorType())

    with pytest.raises(NotImplementedError) as excinfo:
        error.message()

    assert "99" in str(excinfo.value)


def prepare_execution(
    monkeypatch: MonkeyPatch, value: t.Any, widget: clickqt.widgets.BaseWidget
) -> tuple[str, t.Optional[str]]:
    if isinstance(widget, clickqt.widgets.MessageBox):
        # Mock the QMessageBox.information-function
        # User clicked on button "Yes" or "No"
        monkeypatch.setattr(
            QMessageBox,
            "information",
            lambda *args: QMessageBox.Yes if value else QMessageBox.No,
        )
    elif (
        isinstance(widget, clickqt.widgets.FileField)
        and value in {"-", "--"}
        and "r" in widget.type.mode
    ):  # "-" -> True; "--" -> False
        monkeypatch.setattr(
            QInputDialog,
            "getMultiLineText",
            lambda *args: (value, value == "-"),
        )  # value, ok

    args: str = ""
    user_input = None

    if widget.param.multiple:

        def reduce(value) -> str:
            arg_str = "--p="
            for v in value:
                if isinstance(v, list):
                    return reduce(v)
                if str(v) != "":
                    arg_str += str(v) + " "
            return arg_str if arg_str != "--p=" else ""

        for v in value:
            if isinstance(v, list):
                args += reduce(v)
            elif str(v) != "":
                args += f"--p={str(v)} "
    elif isinstance(widget, clickqt.widgets.ConfirmationWidget):
        values = value.split(";")
        args = "--p=" + values[0]
    elif isinstance(widget, clickqt.widgets.MultiWidget):
        args = "--p=" if len(value) > 0 else ""
        for v in value:
            if str(v) != "":
                args += str(v) + " "
            else:  # Don't pass an argument string if any child is empty
                args = ""
                break
    elif not isinstance(widget, clickqt.widgets.MessageBox):
        if isinstance(value, str) and value == "":
            args = ""
        else:
            args = f"--p={str(value)}"
    else:  # widget is MessageBox
        user_input = "y" if value else "n"

    return (args, user_input)


@pytest.mark.parametrize(
    ("click_attrs", "value", "error"),
    [
        (ClickAttrs.checkbox(), False, ClickQtError()),
        (ClickAttrs.checkbox(), True, ClickQtError()),
        (ClickAttrs.messagebox(prompt="Test"), False, ClickQtError()),
        (ClickAttrs.messagebox(prompt="Test"), True, ClickQtError()),
        (ClickAttrs.intfield(), 12, ClickQtError()),
        (ClickAttrs.realfield(), -123.2, ClickQtError()),
        (ClickAttrs.intrange(maxval=2, clamp=True), 5, ClickQtError()),
        (ClickAttrs.floatrange(minval=2.5, clamp=True), -1, ClickQtError()),
        (ClickAttrs.textfield(), "test123", ClickQtError()),
        (ClickAttrs.passwordfield(), "abc", ClickQtError()),
        (
            ClickAttrs.confirmation_widget(),
            "test;test",
            ClickQtError(),
        ),  # Testing: split on ';'
        (
            ClickAttrs.combobox(choices=["A", "B", "C"], case_sensitive=False),
            "b",
            ClickQtError(),
        ),
        (ClickAttrs.checkable_combobox(choices=["A", "B", "C"]), [], ClickQtError()),
        (
            ClickAttrs.checkable_combobox(choices=["A", "B", "C"]),
            ["B", "C"],
            ClickQtError(),
        ),
        (ClickAttrs.datetime(formats=["%d-%m-%Y"]), "23-06-2023", ClickQtError()),
        (ClickAttrs.filefield(), ".gitignore", ClickQtError()),
        (ClickAttrs.filefield(type_dict={"mode": "rb"}), "-", ClickQtError()),
        (ClickAttrs.filefield(type_dict={"mode": "w"}), "-", ClickQtError()),
        (ClickAttrs.filefield(type_dict={"mode": "wb"}), "-", ClickQtError()),
        (ClickAttrs.filepathfield(), ".", ClickQtError()),
        (
            ClickAttrs.tuple_widget(types=(str, int, float)),
            ("t", 1, -2.0),
            ClickQtError(),
        ),
        (
            ClickAttrs.multi_value_widget(nargs=3, type=float),
            [1.2, "-3.5", -2],
            ClickQtError(),
        ),
        (
            ClickAttrs.nvalue_widget(type=(str, int)),
            [["a", 12], ["c", -1]],
            ClickQtError(),
        ),
        (ClickAttrs.nvalue_widget(type=(str, int)), [], ClickQtError()),
        # Aborted error
        (
            ClickAttrs.messagebox(
                prompt="Test", callback=lambda ctx, param, value: ctx.abort()
            ),
            False,
            ClickQtError(ClickQtError.ErrorType.ABORTED_ERROR),
        ),
        (
            ClickAttrs.filefield(),
            "--",
            ClickQtError(ClickQtError.ErrorType.ABORTED_ERROR),
        ),  # Testing: User wants to input an own message (not from a file) but quits the dialog
        (
            ClickAttrs.nvalue_widget(
                type=(str, int), callback=lambda ctx, param, value: ctx.abort()
            ),
            [["ab", 12]],
            ClickQtError(ClickQtError.ErrorType.ABORTED_ERROR),
        ),
        # Exit error
        (
            ClickAttrs.textfield(callback=lambda ctx, param, value: ctx.exit(1)),
            "abc",
            ClickQtError(ClickQtError.ErrorType.EXIT_ERROR),
        ),
        (
            ClickAttrs.nvalue_widget(
                type=(int, str), callback=lambda ctx, param, value: ctx.exit(1)
            ),
            [[2, "a"]],
            ClickQtError(ClickQtError.ErrorType.EXIT_ERROR),
        ),
        # Converting error (invalid file/path)
        (
            ClickAttrs.filefield(),
            "invalid_file",
            ClickQtError(ClickQtError.ErrorType.CONVERTING_ERROR),
        ),
        (
            ClickAttrs.filepathfield(type_dict={"exists": True}),
            "invalid_path",
            ClickQtError(ClickQtError.ErrorType.CONVERTING_ERROR),
        ),
        (
            ClickAttrs.nvalue_widget(type=(click.types.File(), int)),
            [[".gitignore", 12], ["invalid_file", -1]],
            ClickQtError(ClickQtError.ErrorType.CONVERTING_ERROR),
        ),
        # Processing error (Callback raises an exception)
        (
            ClickAttrs.intfield(
                callback=lambda ctx, param, value: raise_(
                    click.exceptions.BadParameter("...")
                )
            ),
            -3,
            ClickQtError(ClickQtError.ErrorType.PROCESSING_VALUE_ERROR),
        ),
        (
            ClickAttrs.nvalue_widget(
                type=(int, str),
                callback=lambda ctx, param, value: raise_(
                    click.exceptions.BadParameter("...")
                )
                if value[0] != (12, "test")
                else value,
            ),
            [[11, "test"], [231, "abc"]],
            ClickQtError(ClickQtError.ErrorType.PROCESSING_VALUE_ERROR),
        ),
        # With default
        (
            ClickAttrs.textfield(default=""),
            "",
            ClickQtError(),
        ),
    ],
)
def test_execution(
    monkeypatch: MonkeyPatch,
    runner: CliRunner,
    click_attrs: dict,
    value: t.Any,
    error: ClickQtError,
):
    param = click.Option(param_decls=["--p"], **click_attrs)
    cli = click.Command("cli", params=[param], callback=callback)

    control = clickqt.qtgui_from_click(cli)
    widget = control.widget_registry[cli.name][param.name]

    if (
        isinstance(widget, clickqt.widgets.FileField)
        and value == "--"
        and "r" in widget.type.mode
    ):
        widget.set_value("-")
        widget.set_enabled_changeable(enabled=True)
    elif isinstance(widget, clickqt.widgets.ConfirmationWidget):
        values = value.split(";")
        widget.field.set_value(values[0])
        widget.set_enabled_changeable(enabled=True)
        widget.confirmation_field.set_value(values[1])
    elif value is not None:
        widget.set_value(value)
        widget.set_enabled_changeable(enabled=True)

    args, inputs = prepare_execution(monkeypatch, value, widget)
    standalone_mode = False
    if error.type == ClickQtError.ErrorType.EXIT_ERROR:  #  See click/core.py#1082
        standalone_mode = True
    click_res = runner.invoke(cli, args, inputs, standalone_mode=standalone_mode)
    val, err = widget.get_value()

    if (
        isinstance(widget, clickqt.widgets.FileField)
        and "r" in widget.type.mode
        and widget.get_widget_value() == "-"
    ):
        assert callable(val)
        val, err = val()

    # First compare the value from 'widget.get_value()' with the click result
    # then the clickqt result (run_button clicked) with the click result
    for i in range(2):
        if not isinstance(widget, clickqt.widgets.FileField):
            assert val == click_res.return_value
        else:  # IOWrapper-objects can't be compared
            closest_common_ancestor_class = clcoancl(
                type(val), type(click_res.return_value)
            )
            assert closest_common_ancestor_class not in {None, object}

        if i == 0:
            assert err.type == error.type
            if error.type == ClickQtError.ErrorType.ABORTED_ERROR:
                if (
                    isinstance(widget, clickqt.widgets.FileField)
                    and value == "--"
                    and "r" in widget.type.mode
                ):
                    assert (
                        isinstance(click_res.exception, click.exceptions.BadParameter)
                        and "'--': No such file or directory"
                        in click_res.exception.message
                    )
                else:
                    assert isinstance(click_res.exception, click.exceptions.Abort)
            elif error.type == ClickQtError.ErrorType.EXIT_ERROR:
                assert isinstance(
                    click_res.exception, SystemExit
                )  # Not click.exceptions.Exit, see click/core.py#1082
            elif error.type == ClickQtError.ErrorType.REQUIRED_ERROR:
                assert isinstance(
                    click_res.exception, click.exceptions.MissingParameter
                )
            elif error.type in {
                ClickQtError.ErrorType.CONVERTING_ERROR,
                ClickQtError.ErrorType.PROCESSING_VALUE_ERROR,
            }:
                assert isinstance(click_res.exception, click.exceptions.BadParameter)
            else:
                assert click_res.exception is None

            STATE["clickqt_res"] = None  # Reset the stored click result
            control.gui.run_button.click()
            wait_process_Events(1)  # Wait for worker thread to finish the execution
            val = STATE["clickqt_res"]


@pytest.mark.parametrize(
    ("click_attrs", "value1", "value2", "error"),
    [
        (
            ClickAttrs.confirmation_widget(),
            "a",
            "b",
            ClickQtError(ClickQtError.ErrorType.CONFIRMATION_INPUT_NOT_EQUAL_ERROR),
        ),
    ],
)
def test_execution_confirmation_widget_fail(
    click_attrs: dict, value1: str, value2: str, error: ClickQtError
):
    param = click.Option(param_decls=["--p"], **click_attrs)
    cli = click.Command("cli", params=[param])

    control = clickqt.qtgui_from_click(cli)
    widget: clickqt.widgets.ConfirmationWidget = control.widget_registry[cli.name][
        param.name
    ]

    widget.field.set_value(value1)
    widget.confirmation_field.set_value(value2)

    val, err = widget.get_value()

    assert val is None and err.type == error.type


def test_confirmation_widget_returns_deterministic_conversion_error(tmp_path):
    valid_path = tmp_path / "valid.txt"
    valid_path.write_text("ok", encoding="utf-8")
    invalid_first = str(tmp_path / "missing-first")
    invalid_second = str(tmp_path / "missing-second")

    param = click.Option(
        ["--p"], type=click.Path(exists=True), **ClickAttrs.confirmation_widget()
    )
    cli = click.Command("cli", params=[param])

    control = clickqt.qtgui_from_click(cli)
    widget: clickqt.widgets.ConfirmationWidget = control.widget_registry[cli.name][
        param.name
    ]

    widget.field.set_value(str(valid_path))
    widget.confirmation_field.set_value(invalid_second)
    val, err = widget.get_value()
    assert val is None
    assert err.type == ClickQtError.ErrorType.CONVERTING_ERROR
    assert os.path.basename(invalid_second) in err.message()

    widget.field.set_value(invalid_first)
    widget.confirmation_field.set_value(invalid_second)
    val, err = widget.get_value()
    assert val is None
    assert err.type == ClickQtError.ErrorType.CONVERTING_ERROR
    assert os.path.basename(invalid_first) in err.message()


@pytest.mark.parametrize(
    ("click_attrs", "value", "envvar_values"),
    [
        (ClickAttrs.nvalue_widget(), [], []),
        (ClickAttrs.nvalue_widget(), [], ["test1", "test2"]),
        (ClickAttrs.nvalue_widget(), ["a", "b"], []),
        (ClickAttrs.nvalue_widget(required=True), ["a", "b"], ["test1", "test2"]),
        (ClickAttrs.nvalue_widget(default=["x", "y"]), [], []),
        (ClickAttrs.nvalue_widget(default=["x", "y"]), [], ["test1", "test2"]),
        (ClickAttrs.nvalue_widget(default=["x", "y"]), ["a", "b"], []),
        (ClickAttrs.nvalue_widget(default=["x", "y"]), ["a", "b"], ["test1", "test2"]),
    ],
)
def test_execution_nvalue_widget(
    runner: CliRunner,
    click_attrs: dict,
    value: t.Sequence[str],
    envvar_values: t.Sequence[str],
):
    os.environ["TEST_CLICKQT_ENVVAR"] = os.path.pathsep.join(envvar_values)

    param = click.Option(
        param_decls=["--p"], envvar="TEST_CLICKQT_ENVVAR", **click_attrs
    )
    cli = click.Command("cli", params=[param], callback=callback)

    control = clickqt.qtgui_from_click(cli)
    widget: clickqt.widgets.NValueWidget = control.widget_registry[cli.name][param.name]

    widget.set_value(value)

    val, err = widget.get_value()
    args, user_input = prepare_execution(monkeypatch=None, value=value, widget=widget)
    click_res = runner.invoke(cli, args, user_input, standalone_mode=False)
    for i in range(2):
        assert val == click_res.return_value

        if i == 0:
            assert err.type == ClickQtError.ErrorType.NO_ERROR

            STATE["clickqt_res"] = None  # Reset the stored click result
            control.gui.run_button.click()
            wait_process_Events(1)  # Wait for worker thread to finish the execution
            val = STATE["clickqt_res"]


def test_nvalue_widget_add_button_reenables_disabled_widget():
    param = click.Option(["--p"], **ClickAttrs.nvalue_widget())
    cli = click.Command("cli", params=[param])

    control = clickqt.qtgui_from_click(cli)
    widget: clickqt.widgets.NValueWidget = control.widget_registry[cli.name][param.name]

    assert widget.is_enabled is False
    add_button = widget.vbox.layout().itemAt(0).widget()
    add_button.click()

    assert len(widget.children) == 1
    assert widget.is_enabled is True


def test_nvalue_widget_add_pair_calls_reenable_branch(monkeypatch: MonkeyPatch):
    param = click.Option(["--p"], **ClickAttrs.nvalue_widget())
    cli = click.Command("cli", params=[param])

    control = clickqt.qtgui_from_click(cli)
    widget: clickqt.widgets.NValueWidget = control.widget_registry[cli.name][param.name]

    calls: list[bool | None] = []
    original_set_enabled_changeable = widget.set_enabled_changeable

    def set_enabled_changeable_stub(enabled=None, changeable=None):
        calls.append(enabled)
        if len(calls) == 1:
            return
        original_set_enabled_changeable(enabled=enabled, changeable=changeable)

    monkeypatch.setattr(widget, "set_enabled_changeable", set_enabled_changeable_stub)

    widget.add_pair()

    assert len(widget.children) == 1
    assert calls == [True, True]
    assert widget.is_enabled is True


def test_nvalue_widget_required_without_values_returns_required_error():
    param = click.Option(["--p"], **ClickAttrs.nvalue_widget(required=True))
    cli = click.Command("cli", params=[param])

    control = clickqt.qtgui_from_click(cli)
    widget: clickqt.widgets.NValueWidget = control.widget_registry[cli.name][param.name]

    value, error = widget.get_value()

    assert value is None
    assert error.type == ClickQtError.ErrorType.REQUIRED_ERROR


def test_nvalue_widget_empty_default_and_none_set_value_mean_no_values():
    param = click.Option(["--p"], **ClickAttrs.nvalue_widget(default=[]))
    cli = click.Command("cli", params=[param])

    control = clickqt.qtgui_from_click(cli)
    widget: clickqt.widgets.NValueWidget = control.widget_registry[cli.name][param.name]

    value, error = widget.get_value()
    assert value == ()
    assert error.type == ClickQtError.ErrorType.NO_ERROR

    widget.add_pair("value")
    assert len(widget.children) == 1

    widget.set_value(None)
    assert len(widget.children) == 0


def test_multiwidget_metavar_updates_child_labels_and_none_disables_widget():
    param = click.Option(["--pair"], nargs=2, metavar=("left", "right"))
    cli = click.Command("cli", params=[param])

    control = clickqt.qtgui_from_click(cli)
    widget: clickqt.widgets.MultiValueWidget = control.widget_registry[cli.name][
        param.name
    ]

    assert [child.label.text() for child in widget.children] == ["left:", "right:"]
    for child in widget.children:
        assert child.layout.alignment() == Qt.AlignmentFlag.AlignLeft
        policy = child.widget.sizePolicy()
        assert policy.horizontalPolicy() == QSizePolicy.Policy.Expanding
        assert policy.verticalPolicy() == QSizePolicy.Policy.Fixed

    widget.set_enabled_changeable(enabled=True)
    widget.set_value(None)
    assert widget.is_enabled is False


def test_multiwidget_with_no_metavar_removes_child_labels():
    param = click.Option(["--pair"], **ClickAttrs.tuple_widget(types=(str, int)))
    cli = click.Command("cli", params=[param])

    control = clickqt.qtgui_from_click(cli)
    widget: clickqt.widgets.TupleWidget = control.widget_registry[cli.name][param.name]

    assert all(child.layout.indexOf(child.label) == -1 for child in widget.children)


def test_multiwidget_is_empty_reflects_child_values():
    param = click.Option(["--value"], **ClickAttrs.nvalue_widget())
    cli = click.Command("cli", params=[param])

    control = clickqt.qtgui_from_click(cli)
    widget: clickqt.widgets.NValueWidget = control.widget_registry[cli.name][param.name]

    assert widget.is_empty() is True

    widget.add_pair("abc")
    assert widget.is_empty() is False

    widget.add_pair("")
    assert widget.is_empty() is True


def test_execution_context():
    clickqt_res: list = []

    @click.group()
    @click.pass_context
    def cli(ctx):
        nonlocal clickqt_res
        ctx.obj = "test1"
        clickqt_res.append(ctx)

    @cli.command()
    @click.pass_obj
    def test(obj):
        nonlocal clickqt_res
        clickqt_res.append(obj)

    control = clickqt.qtgui_from_click(cli)
    control.gui.run_button.click()

    wait_process_Events(200)  # Wait for worker thread to finish the execution

    assert (
        len(clickqt_res) == 2
        and isinstance(clickqt_res[0], click.Context)
        and clickqt_res[1] == "test1"
    )


def test_execution_expose_value_kwargs():
    clickqt_res: dict = None

    def f(p1, **kwargs):
        _ = p1
        nonlocal clickqt_res
        clickqt_res = kwargs

    cli = click.Command(
        "cli",
        params=[
            click.Option(["--p1"], default="a"),
            click.Option(["--p2"], default="b", expose_value=False),
            click.Option(["--p3"], default="c"),
        ],
        callback=f,
    )

    control = clickqt.qtgui_from_click(cli)
    control.gui.run_button.click()

    wait_process_Events(100)  # Wait for worker thread to finish the execution

    assert len(clickqt_res.values()) == 1
    assert clickqt_res.get("p3") == "c"
