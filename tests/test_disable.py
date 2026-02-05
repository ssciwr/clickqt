import enum
import click
import pytest
from click_option_group import OptionGroup
import clickqt.widgets
from clickqt import qtgui_from_click
from clickqt.core.control import Control
from clickqt.core.error import ClickQtError
from clickqt.widgets.styles import (
    BLOB_BUTTON_STYLE_DISABLED,
    BLOB_BUTTON_STYLE_DISABLED_FORCED,
    BLOB_BUTTON_STYLE_ENABLED,
    BLOB_BUTTON_STYLE_ENABLED_FORCED,
)
from tests.testutils import ClickAttrs


class EPTYPE(enum.Enum):
    OPT_GROUPS = 0
    STANDARD = 1


def ensure_cmdstr(control: Control, template: str):
    control.construct_command_string()
    cmdstr = control.get_clipboard()
    assert cmdstr == template


@pytest.mark.parametrize(
    ("style_factory", "base_color", "hover_color"),
    [
        (BLOB_BUTTON_STYLE_ENABLED, "#0f0", "#9f9"),
        (BLOB_BUTTON_STYLE_DISABLED, "#f00", "#f99"),
        (BLOB_BUTTON_STYLE_ENABLED_FORCED, "#696", "#898"),
        (BLOB_BUTTON_STYLE_DISABLED_FORCED, "#966", "#988"),
    ],
)
def test_blob_button_styles_embed_palette_and_geometry(
    style_factory, base_color: str, hover_color: str
):
    radius = 7
    stylesheet = style_factory(radius)

    assert "QToolButton" in stylesheet
    assert f"background-color: {base_color}" in stylesheet
    assert f"background-color: {hover_color}" in stylesheet
    assert f"border-radius: {radius}px" in stylesheet


@pytest.mark.parametrize("eptype", [EPTYPE.OPT_GROUPS, EPTYPE.STANDARD])
@pytest.mark.parametrize(
    ["attrs", "value", "template"],
    [
        (ClickAttrs.checkbox(), "True", "--opt True"),
        (ClickAttrs.checkbox(is_flag=True), "True", "--opt"),
        (
            ClickAttrs.checkable_combobox(["A1", "B2", "C3"]),
            ["B2", "C3"],
            "--opt B2 --opt C3",
        ),
        (ClickAttrs.filefield(), "/home", "--opt /home"),
        (ClickAttrs.datetime(), "2001-1-1", "--opt '2001-01-01 00:00:00'"),
        (ClickAttrs.floatrange(minval=-10), "-2.03", "--opt -2.03"),
        (ClickAttrs.countwidget(), 3, "--opt --opt --opt"),
        (
            ClickAttrs.nvalue_widget(type=(str, int)),
            [["a", 12], ["b", 11]],
            "--opt a 12 --opt b 11",
        ),
        (
            ClickAttrs.tuple_widget(types=(str, int, float)),
            ("t", 1, -2.0),
            "--opt t 1 -2.0",
        ),
        (
            ClickAttrs.multi_value_widget(nargs=2),
            ["A", "C"],
            "--opt A C",
        ),
    ],
)
def test_disable(eptype, attrs, value, template):
    standard_opt = click.Option(["--standard"], default="te st")
    if eptype == EPTYPE.STANDARD:
        opt = click.Option(["--opt"], **attrs, default=value)
        cmd = click.Command("cmd", params=[standard_opt, opt])
        control = qtgui_from_click(cmd)
        widget = control.widget_registry[cmd.name][opt.name]

        expected_enabled = "--standard 'te st' " + template
        expected_disabled = "--standard 'te st'"
    elif eptype == EPTYPE.OPT_GROUPS:
        group = OptionGroup("Server configuration")

        @click.command("main")
        @group.option("--opt1", default="test")
        def cli(**params):
            print(params)

        opt = click.Option(["--opt"], **attrs, default=value)
        cli.params.append(standard_opt)
        cli.params.append(opt)
        cmd = cli
        control = qtgui_from_click(cmd)
        widget = control.widget_registry[cmd.name]["opt1"]

        expected_enabled = "--opt1 test --standard 'te st' " + template
        expected_disabled = "--standard 'te st' " + template

    ensure_cmdstr(control, expected_enabled)
    widget.set_enabled_changeable(enabled=False)
    ensure_cmdstr(control, expected_disabled)
    widget.set_enabled_changeable(enabled=True)
    ensure_cmdstr(control, expected_enabled)


def test_required_widget_disabled_state_reports_required_error():
    param = click.Option(["--count"], **ClickAttrs.intfield(required=True))
    cli = click.Command("cli", params=[param])

    control = qtgui_from_click(cli)
    widget: clickqt.widgets.IntField = control.widget_registry[cli.name][param.name]

    assert widget.is_empty() is False

    widget.set_enabled_changeable(enabled=False)
    value, error = widget.get_value()

    assert value is None
    assert error.type == ClickQtError.ErrorType.REQUIRED_ERROR
    assert widget.enabled_button.toolTip() == "Disabled: This option cannot be used."


def test_checkbox_with_help_removes_help_label_from_layout():
    param = click.Option(
        ["--check"], help="Displayed as checkbox help", **ClickAttrs.checkbox()
    )
    cli = click.Command("cli", params=[param])

    control = qtgui_from_click(cli)
    widget: clickqt.widgets.CheckBox = control.widget_registry[cli.name][param.name]

    assert hasattr(widget, "help_label")
    assert widget.layout.indexOf(widget.help_label) == -1
    assert widget.help_label.text() == "Displayed as checkbox help"


def test_checkbox_flag_set_value_toggles_enabled_state():
    param = click.Option(["--flag"], **ClickAttrs.checkbox(is_flag=True))
    cli = click.Command("cli", params=[param])

    control = qtgui_from_click(cli)
    widget: clickqt.widgets.CheckBox = control.widget_registry[cli.name][param.name]

    widget.set_value(True)
    assert widget.is_enabled is True
    assert widget.get_widget_value() is True

    widget.set_value(False)
    assert widget.is_enabled is False
    assert widget.get_widget_value() is False
