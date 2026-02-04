from __future__ import annotations

import typing as t
import click
from PySide6.QtWidgets import QVBoxLayout, QScrollArea, QPushButton, QWidget
from PySide6.QtCore import Qt

from clickqt.widgets.basewidget import BaseWidget, MultiWidget
from clickqt.core.error import ClickQtError


class NValueWidget(MultiWidget):
    """Represents a multiple click.Parameter-object.
    The child widgets are set according to :func:`~clickqt.widgets.basewidget.MultiWidget.init`.

    :param otype: The type which specifies the clickqt widget type. This type may be different compared to **param**.type when dealing with click.types.CompositeParamType-objects
    :param param: The parameter from which **otype** came from
    :param widgetsource: A reference to :func:`~clickqt.core.gui.GUI.create_widget`
    :param parent: The parent BaseWidget of **otype**, defaults to None. Needed for :class:`~clickqt.widgets.basewidget.MultiWidget`-widgets
    :param kwargs: Additionally parameters ('com', 'label') needed for
                    :class:`~clickqt.widgets.basewidget.MultiWidget`- / :class:`~clickqt.widgets.confirmationwidget.ConfirmationWidget`-widgets
    """

    widget_type = QScrollArea  #: The Qt-type of this widget.

    def __init__(
        self,
        otype: click.ParamType,
        param: click.Parameter,
        widgetsource: t.Callable[[t.Any], BaseWidget],
        parent: t.Optional[BaseWidget] = None,
        **kwargs,
    ):
        super().__init__(otype, param, parent=parent, **kwargs)

        assert not isinstance(
            otype, click.Choice
        ), f"'otype' is of type '{click.Choice}', but there is a better version for this type"
        assert param.multiple, "'param.multiple' should be True"

        self.widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.optkwargs = kwargs
        self.widgetsource = widgetsource
        self.vbox = QWidget()
        self.vbox.setLayout(QVBoxLayout())
        self.widget.setWidgetResizable(True)
        addfieldbtn = QPushButton("+", self.widget)

        def add_empty_widget():
            self.add_pair()

        # Add an empty widget
        addfieldbtn.clicked.connect(add_empty_widget)
        self.vbox.layout().addWidget(addfieldbtn)
        self.widget.setWidget(self.vbox)
        self.buttondict: dict[QPushButton, BaseWidget] = {}

        self.children = self.buttondict.values()

        self.init()
        if len(self.children) == 0 and self.can_change_enabled:
            self.set_enabled_changeable(enabled=False)

    def add_pair(self, value: t.Any = None):
        """Adds a new (child-)widget of type **otype** with a remove button to this widget.
        If **value** is not None, it will be the initial value of the new added widget.

        :param value: The initial value of the new widget, defaults to None (=widget will be zero initialized)
        """

        if len(self.children) == 0:
            self.handle_valid(True)

        self.param.multiple = (
            False  # nargs cannot be nested, so it is safe to turn this off for children
        )
        clickqtwidget: BaseWidget = self.widgetsource(
            self.type,
            self.param,
            widgetsource=self.widgetsource,
            parent=self,
            **self.optkwargs,
        )
        self.param.multiple = True  # click needs this for a correct conversion
        if value is not None:
            clickqtwidget.set_value(value)
        clickqtwidget.layout.removeWidget(clickqtwidget.label)
        clickqtwidget.label.deleteLater()
        removebtn = QPushButton("-", clickqtwidget.widget)
        clickqtwidget.layout.addWidget(removebtn)
        removebtn.clicked.connect(lambda: self.remove_button_pair(removebtn))
        self.vbox.layout().addWidget(clickqtwidget.container)
        self.buttondict[removebtn] = clickqtwidget
        self.widget.setWidget(self.vbox)
        if not self.is_enabled and self.can_change_enabled:
            self.set_enabled_changeable(enabled=True)

    def remove_button_pair(self, btn_to_remove: QPushButton):
        """Removes the widget assoziated with **btn_to_remove**.

        :param btn_to_remove: The remove-button that was clicked
        """

        if btn_to_remove in self.buttondict:
            cqtwidget = self.buttondict.pop(btn_to_remove)
            self.vbox.layout().removeWidget(cqtwidget.container)
            cqtwidget.layout.removeWidget(cqtwidget.widget)
            cqtwidget.container.deleteLater()
            btn_to_remove.deleteLater()
            QScrollArea.updateGeometry(self.widget)

    def get_value(self) -> tuple[t.Any, ClickQtError]:
        """Validates the value of the children-widgets and returns the result. If multiple errors occured then they will be concatenated and returned.

        :return: Valid: (children-widget values or the value of a callback, :class:`~clickqt.core.error.ClickQtError.ErrorType.NO_ERROR`)\n
                 Invalid: (None, :class:`~clickqt.core.error.ClickQtError.ErrorType.CONVERTING_ERROR` or
                 :class:`~clickqt.core.error.ClickQtError.ErrorType.PROCESSING_VALUE_ERROR` or :class:`~clickqt.core.error.ClickQtError.ErrorType.REQUIRED_ERROR`)
        """

        value_missing = False
        if len(self.children) == 0 or not self.is_enabled:
            default = BaseWidget.get_param_default(self.param, None)

            if self.param.required and default is None:
                self.handle_valid(False)
                return (
                    None,
                    ClickQtError(
                        ClickQtError.ErrorType.REQUIRED_ERROR,
                        self.widget_name,
                        self.param.param_type_name,
                    ),
                )
            if (
                envvar_values := self.param.value_from_envvar(
                    click.Context(self.click_command)
                )
            ) is not None:
                for ev in envvar_values:
                    self.add_pair(ev)
            elif default is not None:  # Add new pairs
                for (
                    value
                ) in (
                    default
                ):  # All defaults will be considered if len(self.children)) == 0
                    self.add_pair(value)
            else:  # param is not required and there is no default -> value is None
                value_missing = True  # But callback should be considered

        values: t.Optional[t.Iterable] = None

        if not value_missing:
            values = []
            err_messages: list[str] = []
            default = BaseWidget.get_param_default(self.param, None)

            # len(self.children)) < len(default): We set at most len(self.children)) defaults
            # len(self.children)) >= len(default): All defaults will be considered
            for child in self.children:
                try:  # Try to convert the provided value into the corresponding click object type
                    values.append(
                        self.type.convert(
                            value=child.get_widget_value(),
                            param=self.param,
                            ctx=click.Context(self.click_command),
                        )
                    )
                    child.handle_valid(True)
                except Exception as e:  # pylint: disable=broad-exception-caught
                    child.handle_valid(False)
                    err_messages.append(str(e))

            if len(err_messages) > 0:  # Join all error messages and return them
                messages = ", ".join(err_messages)
                return (
                    None,
                    ClickQtError(
                        ClickQtError.ErrorType.CONVERTING_ERROR,
                        self.widget_name,
                        messages
                        if len(err_messages) == 1
                        else messages.join(["[", "]"]),
                    ),
                )
            if len(values) == 0:  # All widgets are empty
                values = None

        return self.handle_callback(values)

    def set_value(self, value: t.Iterable[t.Any]):
        """Sets the values of the (child-)widgets.
        The number of (child-)widgets are adjusted to the length of **value**. This means that (child-)widgets may be added, but also removed.

        :param value: The list of new values that should be stored in the (child-)widgets
        """
        if value is None:
            value = []

        if len(value) < len(self.children):  # Remove pairs
            for btns in list(self.buttondict.keys())[len(value) :]:
                self.remove_button_pair(btns)
        if len(value) > len(self.children):  # Add pairs
            for i in range(len(value) - len(self.children)):
                self.add_pair()

        for i, c in enumerate(self.children):  # Set the value
            c.set_value(value[i])

    def handle_valid(self, valid: bool):
        if len(self.children) == 0:
            BaseWidget.handle_valid(self, valid)
        else:
            super().handle_valid(valid)

    def get_widget_value_cmdline(self) -> str:
        cmdstr = "".join([c.get_widget_value_cmdline() for c in self.children])
        return cmdstr
