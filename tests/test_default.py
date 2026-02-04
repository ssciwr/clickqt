"""
Contains tests for widget default values
"""
from __future__ import annotations

import datetime
import typing as t

import click
import pytest

from tests.testutils import ClickAttrs
import clickqt.widgets


@pytest.mark.parametrize(
    ("click_attrs", "default", "expected"),
    [
        (ClickAttrs.checkbox(), True, True),
        (ClickAttrs.checkbox(), 1, True),
        (ClickAttrs.checkbox(), "yes", True),
        (ClickAttrs.checkbox(), False, False),
        (ClickAttrs.checkbox(), 0, False),
        (ClickAttrs.checkbox(), "no", False),
        (ClickAttrs.intfield(), 12, 12),
        (ClickAttrs.intfield(), -1322, -1322),
        (ClickAttrs.intfield(), "-31", -31),
        (ClickAttrs.realfield(), 152.31, 152.31),
        (ClickAttrs.realfield(), -123.2, -123.2),
        (ClickAttrs.realfield(), "1.23", 1.23),
        (ClickAttrs.intrange(), "1", 1),
        (ClickAttrs.intrange(maxval=2, clamp=True), 5, 2),
        (ClickAttrs.intrange(minval=2, clamp=True), -1, 2),
        (ClickAttrs.floatrange(), "1.23", 1.23),
        (ClickAttrs.floatrange(maxval=2.5, clamp=True), 5.2, 2.5),
        (ClickAttrs.floatrange(minval=2.5, clamp=True), -1, 2.5),
        (ClickAttrs.textfield(), "test123", "test123"),
        (ClickAttrs.textfield(), 12.2, "12.2"),
        (ClickAttrs.passwordfield(), "abc", "abc"),
        (ClickAttrs.confirmation_widget(), "test321", "test321"),
        (ClickAttrs.messagebox(prompt="Test"), True, True),
        (ClickAttrs.messagebox(prompt="Test"), "y", True),
        (ClickAttrs.messagebox(prompt="Test"), "on", True),
        (ClickAttrs.messagebox(prompt="Test"), False, False),
        (ClickAttrs.messagebox(prompt="Test"), "n", False),
        (ClickAttrs.messagebox(prompt="Test"), "off", False),
        (ClickAttrs.combobox(choices=["A", "B", "C"]), "B", "B"),
        (ClickAttrs.combobox(choices=["A", "B", "C"], case_sensitive=False), "b", "B"),
        (
            ClickAttrs.checkable_combobox(choices=["A", "B", "C"]),
            ["B", "C"],
            ["B", "C"],
        ),
        (
            ClickAttrs.checkable_combobox(
                choices=["A", "B", "C"], case_sensitive=False
            ),
            ["a", "c"],
            ["A", "C"],
        ),
        (
            ClickAttrs.datetime(),
            "2023-06-23",
            datetime.datetime.strptime("2023-06-23 00:00:00", "%Y-%m-%d %H:%M:%S"),
        ),  # Use the default formats
        (
            ClickAttrs.datetime(),
            "2023-06-23 15:14:20",
            datetime.datetime.strptime("2023-06-23 15:14:20", "%Y-%m-%d %H:%M:%S"),
        ),
        (
            ClickAttrs.datetime(formats=["%d-%m-%Y"]),
            "23-06-2023",
            datetime.datetime.strptime("23-06-2023", "%d-%m-%Y"),
        ),
        (
            ClickAttrs.datetime(formats=["%d-%m-%Y %H:%M:%S", "%d-%m-%Y"]),
            "23-06-2023 12:30:20",
            datetime.datetime.strptime("23-06-2023", "%d-%m-%Y"),
        ),  # Default: Use the last format
        (ClickAttrs.filefield(), "test.abc", "test.abc"),
        (ClickAttrs.filefield(), 123.2, "123.2"),
        (ClickAttrs.filepathfield(), ".", "."),
        (ClickAttrs.filepathfield(), 92.3, "92.3"),
        (ClickAttrs.tuple_widget(types=(str, int)), ["s", "1"], ["s", 1]),
        (
            ClickAttrs.tuple_widget(types=(str, int, float)),
            ["t", 1, "-2."],
            ["t", 1, -2.0],
        ),
        (ClickAttrs.multi_value_widget(nargs=3), ["a", "b", "c"], ["a", "b", "c"]),
        (
            ClickAttrs.multi_value_widget(nargs=3, type=float),
            [1.2, "-3.5", -2],
            [1.2, -3.5, -2],
        ),
        (ClickAttrs.nvalue_widget(type=int), [1, -2, 5], [1, -2, 5]),
        (
            ClickAttrs.nvalue_widget(type=(str, float)),
            [["a", 12.2], ["b", -873.21]],
            [["a", 12.2], ["b", -873.21]],
        ),
        (
            ClickAttrs.nvalue_widget(type=(str, (int, str))),
            [["a", [12, "b"]], ["c", [-1, "d"]]],
            [["a", [12, "b"]], ["c", [-1, "d"]]],
        ),
        (
            ClickAttrs.nvalue_widget(type=(str, (int, float))),
            lambda: [["a", [1, 2.1]], ["b", [3, -4.2]]],
            [["a", [1, 2.1]], ["b", [3, -4.2]]],
        ),  # callable as default
    ],
)
def test_set_default(click_attrs: dict, default: t.Any, expected: t.Any):
    """Shorthand to check that the correct default is set"""
    param = click.Option(param_decls=["--test"], default=default, **click_attrs)
    cli = click.Command("cli", params=[param])

    control = clickqt.qtgui_from_click(cli)
    assert control.widget_registry[cli.name][param.name].get_widget_value() == expected


@pytest.mark.parametrize(
    ("click_attrs", "default", "expected"),
    [
        (ClickAttrs.checkbox(), 12, "'12' is not a valid boolean."),
        (ClickAttrs.checkbox(), "ok", "'ok' is not a valid boolean."),
        (ClickAttrs.checkbox(), "-1.0", "'-1.0' is not a valid boolean."),
        (ClickAttrs.intfield(), -2.12, "'-2.12' is not a valid integer."),
        (ClickAttrs.intfield(), "True", "'True' is not a valid integer."),
        (ClickAttrs.intfield(), "-1.0", "'-1.0' is not a valid integer."),
        (ClickAttrs.realfield(), "no", "'no' is not a valid float."),
        (ClickAttrs.intrange(minval=0), -1, "-1 is not in the range x>=0."),
        (ClickAttrs.intrange(minval=1, min_open=True), 1, "1 is not in the range x>1."),
        (ClickAttrs.intrange(maxval=1), 2, "2 is not in the range x<=1."),
        (ClickAttrs.intrange(maxval=1, max_open=True), 1, "1 is not in the range x<1."),
        (ClickAttrs.intrange(), -2.12, "'-2.12' is not a valid integer range."),
        (ClickAttrs.floatrange(minval=0.5), -1.2, "-1.2 is not in the range x>=0.5."),
        (
            ClickAttrs.floatrange(minval=1.2, min_open=True),
            1.2,
            "1.2 is not in the range x>1.2.",
        ),
        (ClickAttrs.floatrange(maxval=1.0), 2.2, "2.2 is not in the range x<=1.0."),
        (
            ClickAttrs.floatrange(maxval=1.0, max_open=True),
            1,
            "1.0 is not in the range x<1.0.",
        ),
        (ClickAttrs.floatrange(), "y", "'y' is not a valid float range."),
        (ClickAttrs.combobox(choices=["A", "B"]), "b", "'b' is not one of 'A', 'B'."),
        (
            ClickAttrs.combobox(choices=["A", "B"], case_sensitive=False),
            "C",
            "'C' is not one of 'A', 'B'.",
        ),
        (
            ClickAttrs.checkable_combobox(choices=["A", "B", "C"]),
            ["b", "C"],
            "'b' is not one of 'A', 'B', 'C'.",
        ),
        (
            ClickAttrs.checkable_combobox(
                choices=["A", "B", "C"], case_sensitive=False
            ),
            ["a", "t", "c"],
            "'t' is not one of 'A', 'B', 'C'.",
        ),
        (
            ClickAttrs.datetime(),
            "23-06-2023",
            "'23-06-2023' does not match the formats '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S'.",
        ),
        (
            ClickAttrs.datetime(formats=["%d-%m-%Y", "%d-%m-%Y %H:%M:%S"]),
            "23-066-2023",
            "'23-066-2023' does not match the formats '%d-%m-%Y', '%d-%m-%Y %H:%M:%S'.",
        ),  # User defined formats
        (
            ClickAttrs.multi_value_widget(nargs=3, type=int),
            ["1", 2, 3.2],
            "'3.2' is not a valid integer.",
        ),
        (
            ClickAttrs.multi_value_widget(nargs=2, type=float),
            ["yes", "y"],
            "'yes' is not a valid float.",
        ),  # First wrong value fails the test
        (
            ClickAttrs.tuple_widget(types=(str, int)),
            ["s", 12.3],
            "'12.3' is not a valid integer.",
        ),
        (
            ClickAttrs.nvalue_widget(type=(str, float)),
            [["a", "set"], ["b", "t"]],
            "'set' is not a valid float.",
        ),  # First wrong value fails the test
    ],
)
def test_set_default_fail(click_attrs: dict, default: t.Any, expected: t.Any):
    """Shorthand to check that the correct error is returned"""
    param = click.Option(param_decls=["--test"], default=default, **click_attrs)
    cli = click.Command("cli", params=[param])

    with pytest.raises(click.exceptions.BadParameter) as exc_info:
        # pylint: disable=expression-not-assigned
        clickqt.qtgui_from_click(cli).widget_registry[cli.name][param.name]

    message = exc_info.value.message
    if message == expected:
        return
    if "is not a valid boolean." in expected:
        assert message.startswith(expected + " Recognized values:")
        return
    if "is not one of" in expected:
        assert message.lower() == expected.lower()
        return
    assert expected == message
