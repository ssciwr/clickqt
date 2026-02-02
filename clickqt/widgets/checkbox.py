""" Contains the checkbox widget """
from __future__ import annotations

import typing as t

from PySide6.QtWidgets import QCheckBox
import click

from clickqt.widgets.basewidget import BaseWidget


class CheckBox(BaseWidget):
    """Represents a click.types.BoolParamType object.

    :param otype: The type which specifies the clickqt widget type.
        This type may be different compared to **param**.type when dealing with click.types.CompositeParamType-objects
    :param param: The parameter from which **otype** came from
    :param kwargs: Additionally parameters ('parent', 'widgetsource', 'com', 'label') needed for
        :class:`~clickqt.widgets.basewidget.MultiWidget`- /
        :class:`~clickqt.widgets.confirmationwidget.ConfirmationWidget`- widgets
    """

    widget_type = QCheckBox  #: The Qt-type of this widget.

    def __init__(self, otype: click.ParamType, param: click.Parameter, **kwargs):
        super().__init__(otype, param, **kwargs)
        default = self._cast_bool(self.get_param_default(param, False))
        assert isinstance(
            otype, type(click.BOOL)
        ), f"'otype' must be of type '{type(click.BOOL)}', but is '{type(otype)}'."
        is_flag = self.param.to_info_dict().get("is_flag", False)
        if is_flag:
            self.widget.hide()
            self.set_enabled_changeable(default)
        else:
            self.widget.setChecked(default)
            if hasattr(self, "help_label"):
                self.layout.removeWidget(self.help_label)
                self.help_label.setText(
                    self.help_label.text()
                )  # Set text of checkbox to help text
        if self.parent_widget is None:
            self.set_enabled_changeable(default, changeable=True)

    def _cast_bool(self, value: t.Any):
        return bool(
            self.type.convert(
                str(value), self.click_command, click.Context(self.click_command)
            )
        )

    def set_value(self, value: t.Any):
        from click._utils import Sentinel
        if isinstance(value, Sentinel):
            value = None

        if self.param.to_info_dict().get("is_flag", False):
            self.set_enabled_changeable(value)
        else:
            self.widget.setChecked(self._cast_bool(value))

    def get_widget_value(self) -> bool:
        return (
            self.is_enabled
            if self.param.to_info_dict().get("is_flag", False)
            else self.widget.isChecked()
        )
