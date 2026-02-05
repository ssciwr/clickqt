from __future__ import annotations

import typing as t

import click
import pytest
from PySide6.QtCore import QEvent
from PySide6.QtGui import QFocusEvent

import clickqt.widgets
from tests.testutils import ClickAttrs, raise_


def evaluate(
    clickqt_widget: clickqt.widgets.BaseWidget,
    clickqt_child_widget: clickqt.widgets.BaseWidget,
    invalid_value: t.Any,
    valid_value: t.Any,
):
    value = [invalid_value, valid_value]
    border: list[t.Callable] = [
        lambda widget: f"QWidget#{clickqt_widget.widget_name}{{ border: 1px solid red }}"
        in widget.styleSheet(),  # red border
        lambda widget: f"QWidget#{clickqt_widget.widget_name}{{ }}"
        == widget.styleSheet(),
    ]  # normal border

    for i in range(2):
        clickqt_widget.set_value(value[i])
        clickqt_child_widget.focus_out_validator.eventFilter(
            clickqt_child_widget.widget, QEvent(QEvent.Type.FocusOut)
        )  # widget goes out of focus
        if (
            clickqt_widget == clickqt_child_widget
            and isinstance(clickqt_widget, clickqt.widgets.MultiWidget)
        ) or (
            clickqt_widget != clickqt_child_widget
            and isinstance(
                clickqt_widget,
                (clickqt.widgets.MultiValueWidget, clickqt.widgets.TupleWidget),
            )
        ):  # NValueWidget: Every child can be checked individually
            for child in clickqt_widget.children:
                assert border[i](child.widget)
        else:
            assert border[i](clickqt_child_widget.widget)


@pytest.mark.parametrize(
    ("click_attrs", "invalid_value", "valid_value"),
    [
        (
            ClickAttrs.intfield(
                callback=lambda ctx, param, value: raise_(Exception("..."))
                if value < 5
                else value
            ),
            0,
            10,
        ),
        (ClickAttrs.filepathfield(type_dict={"exists": True}), "invalid_path", "tests"),
        (
            ClickAttrs.tuple_widget(
                types=(str, float),
                callback=lambda ctx, param, value: raise_(Exception("..."))
                if value[0] != "abc"
                else value,
            ),
            ["a", 0],
            ["abc", 2.2],
        ),
        (
            ClickAttrs.multi_value_widget(
                nargs=3,
                type=int,
                callback=lambda ctx, param, value: raise_(Exception("..."))
                if value != (0, 1, 2)
                else value,
            ),
            [0, 0, 0],
            [0, 1, 2],
        ),
        (
            ClickAttrs.nvalue_widget(
                callback=lambda ctx, param, value: raise_(Exception("..."))
                if len(value) == 0
                else value
            ),
            [],
            ["abc"],
        ),
    ],
)
def test_focus_out_validation(
    click_attrs: dict, invalid_value: t.Any, valid_value: t.Any
):
    param = click.Option(param_decls=["--test"], **click_attrs)
    cli = click.Command("cli", params=[param])

    control = clickqt.qtgui_from_click(cli)
    clickqt_widget = control.widget_registry[cli.name][param.name]

    evaluate(clickqt_widget, clickqt_widget, invalid_value, valid_value)


@pytest.mark.parametrize(
    ("click_attrs", "invalid_value", "valid_value"),
    [
        (
            ClickAttrs.tuple_widget(types=(str, click.types.Path(exists=True))),
            ["a", "invalid_path"],
            ["abc", "tests"],
        ),
        (
            ClickAttrs.multi_value_widget(nargs=2, type=click.types.Path(exists=True)),
            ["invalid_path", "invalid_path"],
            ["tests", "tests"],
        ),  # Both children have to be valid
        (
            ClickAttrs.nvalue_widget(type=click.types.Path(exists=True)),
            ["invalid_path", "invalid_path"],
            ["invalid_path", "tests"],
        ),  # We check only children[1], so children[0] can be still invalid
    ],
)
def test_focus_out_validation_child(
    click_attrs: dict, invalid_value: t.Any, valid_value: t.Any
):
    param = click.Option(param_decls=["--test"], **click_attrs)
    cli = click.Command("cli", params=[param])

    control = clickqt.qtgui_from_click(cli)
    clickqt_widget = control.widget_registry[cli.name][param.name]

    clickqt_widget.set_value(
        invalid_value
    )  # Create the children for the NValueWidget-object

    evaluate(
        clickqt_widget, list(clickqt_widget.children)[1], invalid_value, valid_value
    )  # We check the first child


def test_basewidget_focus_and_wheel_handlers_respect_focus_state(
    monkeypatch: pytest.MonkeyPatch,
):
    param = click.Option(param_decls=["--test"], **ClickAttrs.intfield())
    cli = click.Command("cli", params=[param])
    control = clickqt.qtgui_from_click(cli)
    widget: clickqt.widgets.IntField = control.widget_registry[cli.name][param.name]

    calls = {"wheel": 0, "focus_in": 0}

    class DummyWidgetType:
        @staticmethod
        def wheelEvent(_widget, _event):
            calls["wheel"] += 1

        @staticmethod
        def focusInEvent(_widget, _event):
            calls["focus_in"] += 1

    class DummyWheelEvent:
        def __init__(self):
            self.ignored = False

        def ignore(self):
            self.ignored = True

    widget.widget_type = DummyWidgetType

    monkeypatch.setattr(widget.widget, "hasFocus", lambda: False)
    wheel_event_unfocused = DummyWheelEvent()
    widget.widget.wheelEvent(wheel_event_unfocused)
    assert wheel_event_unfocused.ignored is True
    assert calls["wheel"] == 0

    monkeypatch.setattr(widget.widget, "hasFocus", lambda: True)
    wheel_event_focused = DummyWheelEvent()
    widget.widget.wheelEvent(wheel_event_focused)
    assert wheel_event_focused.ignored is False
    assert calls["wheel"] == 1

    widget.set_enabled_changeable(enabled=False, changeable=True)
    widget.widget.focusInEvent(QFocusEvent(QEvent.Type.FocusIn))
    assert calls["focus_in"] == 1
    assert widget.is_enabled is True
