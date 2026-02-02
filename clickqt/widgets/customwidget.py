from __future__ import annotations
from typing import Any, TYPE_CHECKING
from click import ParamType, Parameter

from clickqt.widgets import BaseWidget

if TYPE_CHECKING:
    from clickqt.core.gui import CustomBindingType


class WidgetNotSupported(Exception):
    """Exception stating that the a widget is not supported by clickqt yet for user defined click types."""

    def __init__(self, widget_name):
        super().__init__(f"{widget_name} not supported.")
        self.widget_name = widget_name


class CustomWidget(BaseWidget):
    """The CustomWidget class is used as a means to display and interact with custom, user-defined click data types.
    :param widget_class: The kind of widget the user wants to map his user defined click type.
    :param bindings: The class of the widget to be constructed and ways to read/write data
    :param otype: The type which specifies the clickqt widget type. This type may be different compared to **param**.type when dealing with click.types.CompositeParamType-objects
    :param param: The parameter from which **otype** came from
    :param parent: The parent BaseWidget of **otype**, defaults to None. Needed for :class:`~clickqt.widgets.basewidget.MultiWidget`-widgets
    :param kwargs: Additionally parameters ('widgetsource', 'com', 'label') needed for
                    :class:`~clickqt.widgets.basewidget.MultiWidget`- / :class:`~clickqt.widgets.confirmationwidget.ConfirmationWidget`-widgets
    """

    def __init__(
        self,
        binding: "CustomBindingType",
        otype: ParamType,
        param: Parameter,
        parent: BaseWidget | None = None,
        **kwargs,
    ):
        self.widget_type, self.getter, self.setter = binding
        super().__init__(otype, param, parent, **kwargs)

    def get_widget_value(self) -> Any:
        return self.getter(self)

    def set_value(self, value: Any):
        from click._utils import Sentinel
        if isinstance(value, Sentinel):
            value = None
        return self.setter(self, value)
