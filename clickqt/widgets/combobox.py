from __future__ import annotations

import typing as t
import click
from PySide6.QtWidgets import QComboBox

from clickqt.widgets.basewidget import ComboBoxBase, BaseWidget
from clickqt.widgets.core.QCheckableCombobox import QCheckableComboBox


class ComboBox(ComboBoxBase):
    """Represents a click.types.Choice object.

    :param otype: The type which specifies the clickqt widget type. This type may be different compared to **param**.type when dealing with click.types.CompositeParamType-objects
    :param param: The parameter from which **otype** came from
    :param kwargs: Additionally parameters ('parent', 'widgetsource', 'com', 'label') needed for
                    :class:`~clickqt.widgets.basewidget.MultiWidget`- / :class:`~clickqt.widgets.confirmationwidget.ConfirmationWidget`-widgets
    """

    widget_type = QComboBox  #: The Qt-type of this widget.

    def __init__(self, otype: click.ParamType, param: click.Parameter, **kwargs):
        super().__init__(otype, param, **kwargs)

        if (
            self.parent_widget is None
            and (default := BaseWidget.get_param_default(param, None)) is not None
        ):
            self.set_value(default)

    def set_value(self, value: t.Any):
        from click._utils import Sentinel
        if isinstance(value, Sentinel):
            value = None
    
        self.widget.setCurrentText(
            str(
                self.type.convert(
                    str(value), self.click_command, click.Context(self.click_command)
                )
            )
        )

    def add_items(self, items: t.Iterable[str]):
        self.widget.addItems(items)

    def get_widget_value(self) -> str:
        return self.widget.currentText()


class CheckableComboBox(ComboBoxBase):
    """Represents a multiple click.types.Choice object.

    :param otype: The type which specifies the clickqt widget type. This type may be different compared to **param**.type when dealing with click.types.CompositeParamType-objects
    :param param: The parameter from which **otype** came from
    :param kwargs: Additionally parameters ('parent', 'widgetsource', 'com', 'label') needed for
                    :class:`~clickqt.widgets.basewidget.MultiWidget`- / :class:`~clickqt.widgets.confirmationwidget.ConfirmationWidget`-widgets
    """

    widget_type = QCheckableComboBox  #: The Qt-type of this widget.

    def __init__(self, otype: click.ParamType, param: click.Parameter, **kwargs):
        super().__init__(otype, param, **kwargs)

        assert param.multiple, "'param.multiple' should be True"

        if self.parent_widget is None:
            self.set_value(BaseWidget.get_param_default(param, []))

    def set_value(self, value: t.Iterable[t.Any]):
        from click._utils import Sentinel
        if isinstance(value, Sentinel):
            value = []

        check_values: list[str] = []
        for v in value:
            check_values.append(
                str(
                    self.type.convert(
                        str(v), self.click_command, click.Context(self.click_command)
                    )
                )
            )

        self.widget.checkItems(check_values)

    def add_items(self, items: t.Iterable[str]):
        self.widget.addItems(items)

    def get_widget_value(self) -> t.Iterable[str]:
        return self.widget.getData()

    def get_widget_value_cmdline(self) -> str:
        optname = self.get_preferable_opt() + " "
        optvals = list(self.get_widget_value())
        return (optname + f" {optname}".join(optvals) + " ") if len(optvals) > 0 else ""
