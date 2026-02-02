from __future__ import annotations

import typing as t

import click
from PySide6.QtWidgets import QWidget, QHBoxLayout

from clickqt.widgets.basewidget import BaseWidget
from clickqt.core.error import ClickQtError


class ConfirmationWidget(BaseWidget):
    """Represents a click option with confirmation_prompt==True. It stores two clickqt widgets of the same type.

    :param otype: The type which specifies the clickqt widget type. This type may be different compared to **param**.type when dealing with click.types.CompositeParamType-objects
    :param param: The parameter from which **otype** came from
    :param widgetsource: A reference to :func:`~clickqt.core.gui.GUI.create_widget`
    :param kwargs: Additionally parameters ('parent', 'com', 'label') needed for
                    :class:`~clickqt.widgets.basewidget.MultiWidget`- / :class:`~clickqt.widgets.confirmationwidget.ConfirmationWidget`-widgets
    """

    widget_type = QWidget  #: The Qt-type of this widget. It's a container for storing the two input-widgets

    def __init__(
        self,
        otype: click.ParamType,
        param: click.Parameter,
        widgetsource: t.Callable[[t.Any], BaseWidget],
        **kwargs,
    ):
        super().__init__(otype, param, **kwargs)

        assert (
            hasattr(self.param, "confirmation_prompt")
            and self.param.confirmation_prompt
        ), "'param.confirmation_prompt' should be True"

        self.param.confirmation_prompt = False  # Stop recursion
        self.field: BaseWidget = widgetsource(
            self.type, param, parent=self, vboxlayout=True, **kwargs
        )  #: First input widget.
        kwargs["label"] = "Confirmation "
        self.confirmation_field: BaseWidget = widgetsource(
            self.type, param, parent=self, vboxlayout=True, **kwargs
        )  #: Second (confirmation) input widget.
        self.param.confirmation_prompt = True
        self.layout.setDirection(QHBoxLayout.Direction.LeftToRight)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.field.container)
        self.layout.addWidget(self.confirmation_field.container)
        self.field.headinglayout.insertWidget(0, self.enabled_button)
        self.heading.close()
        self.layout.removeWidget(self.widget)

        if self.parent_widget is None:
            self.set_value(BaseWidget.get_param_default(param, None))

    def set_value(self, value: t.Any):
        """Sets **value** as widget value for :attr:`~clickqt.widgets.confirmationwidget.ConfirmationWidget.field` and
        :attr:`~clickqt.widgets.confirmationwidget.ConfirmationWidget.confirmation_field` according to :func:`~clickqt.widgets.basewidget.BaseWidget.set_value`.
        """

        from click._utils import Sentinel
        if isinstance(value, Sentinel):
            value = None

        if value is not None:
            self.field.set_value(value)
            self.confirmation_field.set_value(value)

    def handle_valid(self, valid: bool):
        """Changes the widget border for :attr:`~clickqt.widgets.confirmationwidget.ConfirmationWidget.field` and
        :attr:`~clickqt.widgets.confirmationwidget.ConfirmationWidget.confirmation_field` according to :func:`~clickqt.widgets.basewidget.BaseWidget.handle_valid`.
        """

        self.field.handle_valid(valid)
        self.confirmation_field.handle_valid(valid)

    def get_value(self) -> tuple[t.Any, ClickQtError]:
        """Calls :func:`~clickqt.widgets.basewidget.BaseWidget.get_value` on :attr:`~clickqt.widgets.confirmationwidget.ConfirmationWidget.field` and
        :attr:`~clickqt.widgets.confirmationwidget.ConfirmationWidget.confirmation_field`, validates the result and returns it.

        :return: Valid: (widget value or the value of a callback, :class:`~clickqt.core.error.ClickQtError.ErrorType.NO_ERROR`)\n
                 Invalid: (None, :class:`~clickqt.core.error.ClickQtError.ErrorType.CONVERTING_ERROR` or
                 :class:`~clickqt.core.error.ClickQtError.ErrorType.PROCESSING_VALUE_ERROR` or :class:`~clickqt.core.error.ClickQtError.ErrorType.CONFIRMATION_INPUT_NOT_EQUAL_ERROR`)
        """

        val1, err1 = self.field.get_value()
        val2, err2 = self.confirmation_field.get_value()

        if (
            err1.type != ClickQtError.ErrorType.NO_ERROR
            or err2.type != ClickQtError.ErrorType.NO_ERROR
        ):
            return (
                None,
                err1 if err1.type != ClickQtError.ErrorType.NO_ERROR else err2,
            )

        if val1 != val2:
            self.handle_valid(False)
            return (
                None,
                ClickQtError(
                    ClickQtError.ErrorType.CONFIRMATION_INPUT_NOT_EQUAL_ERROR,
                    self.widget_name,
                ),
            )
        self.handle_valid(True)
        return (val1, ClickQtError())

    def get_widget_value(self) -> t.Any:
        return self.field.get_widget_value()
