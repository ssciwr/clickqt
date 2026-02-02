from __future__ import annotations

import datetime
import typing as t

import click
from PySide6.QtWidgets import QDateTimeEdit
from PySide6.QtCore import QDateTime, Qt
from PySide6.QtGui import QAction, QActionGroup

from clickqt.widgets.basewidget import BaseWidget


class DateTimeEdit(BaseWidget):
    """Represents a click.types.DateTime object. The format of the datetime displayed in this widget can be changed by opening the context menu.

    :param otype: The type which specifies the clickqt widget type. This type may be different compared to **param**.type when dealing with click.types.CompositeParamType-objects
    :param param: The parameter from which **otype** came from
    :param kwargs: Additionally parameters ('parent', 'widgetsource', 'com', 'label') needed for
                    :class:`~clickqt.widgets.basewidget.MultiWidget`- / :class:`~clickqt.widgets.confirmationwidget.ConfirmationWidget`-widgets
    """

    widget_type = QDateTimeEdit  #: The Qt-type of this widget.

    def __init__(self, otype: click.ParamType, param: click.Parameter, **kwargs):
        super().__init__(otype, param, **kwargs)

        assert isinstance(
            otype, click.DateTime
        ), f"'otype' must be of type '{click.DateTime}', but is '{type(otype)}'."

        self.widget.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)

        #: Contains all available formats in qt_format- and click_format-style. Default format string is the last string in the *click.types.DateTime*\s ``formats`` attribute
        self.format_group: QActionGroup = QActionGroup(self.widget)

        # Add for each format a context menu entry
        for (
            click_format
        ) in self.type.formats:  # click ensures that there is at least one format
            qt_format: str = (
                click_format.replace("%Y", "yyyy")
                .replace("%m", "MM")
                .replace("%d", "dd")
                .replace("%H", "hh")
                .replace("%M", "mm")
                .replace("%S", "ss")
            )
            action = QAction(qt_format, self.widget)
            action.setData(click_format)
            action.setCheckable(True)
            if (
                click_format == self.type.formats[-1]
            ):  # Last format is checked at the beginning
                action.setChecked(True)
                self.widget.setDisplayFormat(qt_format)
            else:
                action.setChecked(False)
            self.widget.addAction(action)
            self.format_group.addAction(action)

        self.format_group.setExclusive(
            True
        )  # Only one format can be checked at the same time
        self.format_group.triggered.connect(
            lambda action: self.widget.setDisplayFormat(action.text())
            or self.container.setFocus()
        )  # Update display format and geometry

        if (
            self.parent_widget is None
            and (default := BaseWidget.get_param_default(param, None)) is not None
        ):
            self.set_value(default)

    def set_value(self, value: t.Any):
        """Sets the value of the Qt-widget according to the selected format stored in :attr:`~clickqt.widgets.datetimeedit.DateTimeEdit.format_group`."""
        from click._utils import Sentinel
        if isinstance(value, Sentinel):
            value = None
        # value -> datetime -> str -> QDateTime
        self.widget.setDateTime(
            QDateTime.fromString(
                self.type.convert(
                    str(value), self.click_command, click.Context(self.click_command)
                ).strftime(self.format_group.checkedAction().data()),
                self.format_group.checkedAction().text(),
            )
        )

    def get_widget_value(self) -> datetime.datetime:
        return self.widget.dateTime().toPython()

    def get_widget_value_cmdline(self) -> str:
        return f"{self.get_preferable_opt()} '{self.get_widget_value()}'"
