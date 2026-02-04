from __future__ import annotations

import os
import typing as t

import click
import pytest

from tests.testutils import ClickAttrs
import clickqt.widgets


@pytest.mark.parametrize(
    ("click_attrs", "envvar_values", "expected"),
    [
        (ClickAttrs.textfield(), "test123", "test123"),
        (
            ClickAttrs.textfield(),
            ["test1", "test2"],
            os.path.pathsep.join(["test1", "test2"]),
        ),
        (ClickAttrs.filefield(), "test", "test"),
        (
            ClickAttrs.filefield(),
            ["test1", "test2"],
            os.path.pathsep.join(["test1", "test2"]),
        ),
        (ClickAttrs.filepathfield(), "test", "test"),
        (
            ClickAttrs.filepathfield(),
            ["test1", "test2"],
            os.path.pathsep.join(["test1", "test2"]),
        ),
        (
            ClickAttrs.multi_value_widget(nargs=2, type=click.types.Path()),
            ["a", "b"],
            ["a", "b"],
        ),
        (
            ClickAttrs.multi_value_widget(nargs=2, type=click.types.File()),
            ["a", "b"],
            ["a", "b"],
        ),
        (
            ClickAttrs.intfield(),
            "test123",
            0,
        ),  # envvars are only considered for string based widgets
        (
            ClickAttrs.multi_value_widget(nargs=2, type=int),
            ["2", "3"],
            [2, 3],
        ),  # and for multi widgets
        (ClickAttrs.tuple_widget(types=(float, str)), ["2.3", "3"], [2.3, "3"]),
        (ClickAttrs.nvalue_widget(), ["2.3", "3", "av"], ["2.3", "3", "av"]),
    ],
)
def test_set_envvar(
    click_attrs: dict,
    envvar_values: "str| t.Sequence[str]",
    expected: "str| t.Sequence[t.Any]",
):
    os.environ["TEST_CLICKQT_ENVVAR"] = os.path.pathsep.join(
        envvar_values
        if isinstance(envvar_values, t.Sequence) and not isinstance(envvar_values, str)
        else [envvar_values]
    )

    param = click.Option(
        param_decls=["--test"], envvar="TEST_CLICKQT_ENVVAR", **click_attrs
    )
    cli = click.Command("cli", params=[param])

    control = clickqt.qtgui_from_click(cli)
    assert control.widget_registry[cli.name][param.name].get_widget_value() == expected


@pytest.mark.parametrize(
    ("click_attrs", "envvar_values", "expected"),
    [
        (
            ClickAttrs.multi_value_widget(nargs=3, type=click.types.Path()),
            ["a", "b"],
            "Takes 3 values but 2 were given.",
        ),
        (
            ClickAttrs.multi_value_widget(nargs=2, type=click.types.File()),
            ["a", "b", "c"],
            "Takes 2 values but 3 were given.",
        ),
        (
            ClickAttrs.tuple_widget(types=(click.types.Path(), click.types.Path())),
            ["a", "b", "c"],
            "Takes 2 values but 3 were given.",
        ),
        (
            ClickAttrs.tuple_widget(types=(click.types.Path(), click.types.File())),
            ["a"],
            "Takes 2 values but 1 was given.",
        ),
        (
            ClickAttrs.tuple_widget(types=(click.types.File(), click.types.Path())),
            ["a", "c", "b"],
            "Takes 2 values but 3 were given.",
        ),
        (
            ClickAttrs.tuple_widget(types=(click.types.File(), click.types.File())),
            ["a", "b", "c", "d"],
            "Takes 2 values but 4 were given.",
        ),
    ],
)
def test_set_envvar_fail(
    click_attrs: dict,
    envvar_values: t.Union[str, t.Sequence[str]],
    expected: t.Union[str, t.Sequence[str]],
):
    os.environ["TEST_CLICKQT_ENVVAR"] = os.path.pathsep.join(
        envvar_values if isinstance(envvar_values, t.Sequence) else [envvar_values]
    )

    param = click.Option(
        param_decls=["--test"], envvar="TEST_CLICKQT_ENVVAR", **click_attrs
    )
    cli = click.Command("cli", params=[param])

    with pytest.raises(click.exceptions.BadParameter) as exc_info:
        # pylint: disable=expression-not-assigned
        clickqt.qtgui_from_click(cli).widget_registry[cli.name][param.name]

    assert expected == exc_info.value.message
