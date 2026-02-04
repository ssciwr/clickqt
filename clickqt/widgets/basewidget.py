from __future__ import annotations

from abc import ABC, abstractmethod
import os
import typing as t
from gettext import ngettext
import shlex

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
    QToolButton,
)
from PySide6.QtCore import Qt
import click
from clickqt.widgets.styles import (
    BLOB_BUTTON_STYLE_ENABLED,
    BLOB_BUTTON_STYLE_DISABLED,
    BLOB_BUTTON_STYLE_ENABLED_FORCED,
    BLOB_BUTTON_STYLE_DISABLED_FORCED,
)

from clickqt.core.error import ClickQtError
from clickqt.core.defaults import normalize_default, is_unset
import clickqt.core  # FocusOutValidator


class BaseWidget(ABC):  # pylint: disable=too-many-instance-attributes
    """Provides basic functionalities and initializes the widget.
    Every clickqt widget has to inherit from this class.

    :param otype: The type which specifies the clickqt widget type. This type may be different compared to **param**.type when dealing with click.types.CompositeParamType-objects
    :param param: The parameter from which **otype** came from
    :param parent: The parent BaseWidget of **otype**, defaults to None. Needed for :class:`~clickqt.widgets.basewidget.MultiWidget`-widgets
    :param kwargs: Additionally parameters ('widgetsource', 'com', 'label') needed for
                    :class:`~clickqt.widgets.basewidget.MultiWidget`- / :class:`~clickqt.widgets.confirmationwidget.ConfirmationWidget`-widgets
    """

    widget_type: t.ClassVar[t.Type]  #: The Qt-type of this widget.

    def __init__(
        self,
        otype: click.ParamType,
        param: click.Parameter,
        parent: t.Optional["BaseWidget"] = None,
        **kwargs,
    ):  # pylint: disable=too-many-statements
        assert isinstance(otype, click.ParamType)
        assert isinstance(param, click.Parameter)
        if is_unset(param.default):
            # Click >=8.2 uses an UNSET sentinel where clickqt historically expected None.
            param.default = None
        self.is_enabled = True
        self.can_change_enabled = True
        self.type = otype
        self.param = param
        self.parent_widget = parent
        self.click_command: click.Command = kwargs.get("com")
        self.widget_name = param.name
        self.container = QWidget()
        self.layout = (
            QVBoxLayout()
            if parent is None or kwargs.get("vboxlayout")
            else QHBoxLayout()
        )

        self.heading = QWidget()
        self.headinglayout = QHBoxLayout()
        self.heading.setLayout(self.headinglayout)
        self.label = QLabel(text=f"<b>{kwargs.get('label', '')}{self.widget_name}</b>")
        self.label.setTextFormat(Qt.TextFormat.RichText)  # Bold text

        self.widget = self.create_widget()
        self.enabled_button = QToolButton(checkable=True, checked=True)
        self.enabled_button.clicked.connect(
            lambda: self.set_enabled_changeable(enabled=not self.is_enabled)
            if self.can_change_enabled
            else None
        )
        self.set_enabled_changeable(
            enabled=self.is_enabled, changeable=self.can_change_enabled
        )  # update the button

        if self.parent_widget is None:
            self.headinglayout.addWidget(self.enabled_button)
        self.headinglayout.addWidget(self.label)

        self.layout.addWidget(self.heading)
        if (
            isinstance(param, click.Option)
            and param.help
            and (parent is None or kwargs.get("vboxlayout"))
        ):  # Help text
            self.help_label = QLabel(text=param.help)
            self.help_label.setWordWrap(True)  # Multi-line
            self.layout.addWidget(self.help_label)
        self.layout.addWidget(self.widget)
        self.container.setLayout(self.layout)

        self.widget.setObjectName(
            param.name
        )  # Only change the stylesheet of this widget and not of all (child-)widgets

        assert self.widget is not None, "Widget not initialized"
        assert self.param is not None, "Click param object not provided"
        assert self.click_command is not None, "Click command not provided"
        assert self.type is not None, "Type not provided"

        self.focus_out_validator = clickqt.core.FocusOutValidator(self)

        self.widget.installEventFilter(self.focus_out_validator)
        self.widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        def handlewheel(event):
            if self.widget.hasFocus():
                self.widget_type.wheelEvent(self.widget, event)
            else:
                event.ignore()

        def handlefocusin(event):
            self.widget_type.focusInEvent(self.widget, event)
            if self.can_change_enabled:
                self.set_enabled_changeable(enabled=True)

        self.widget.wheelEvent = handlewheel  # Disable scrolling
        if not isinstance(self, (MultiWidget)):
            self.widget.focusInEvent = handlefocusin

    def create_widget(self) -> QWidget:
        """Creates the widget specified in :attr:`~clickqt.widgets.basewidget.BaseWidget.widget_type` and returns it."""

        return self.widget_type()

    @abstractmethod
    def set_value(self, value: t.Any):
        """Sets the value of the Qt-widget.

        :param value: The new value that should be stored in the widget
        :raises click.BadParameter: **value** could not be converted into the corresponding click.ParamType
        """

    def set_enabled_changeable(
        self, enabled: bool | None = None, changeable: bool | None = None
    ):
        """Enable/disable the widget, allow user to enable/disable the widget.
        A disabled widget's values are not used when the command is run or copied to cmdline.

        :param enabled: True if the widget should be enabled, False otherwise
        :param changeable: True if the widget can be enabled/disabled by the user, False otherwise
        """
        btnsizehalf = 5
        self.is_enabled = self.is_enabled if enabled is None else enabled
        self.can_change_enabled = (
            self.can_change_enabled if changeable is None else changeable
        )
        if self.can_change_enabled and self.is_enabled:
            self.enabled_button.setStyleSheet(BLOB_BUTTON_STYLE_ENABLED(btnsizehalf))
            self.enabled_button.setToolTip("Enabled: Option will be used.")
        elif self.can_change_enabled and (not self.is_enabled):
            self.enabled_button.setStyleSheet(BLOB_BUTTON_STYLE_DISABLED(btnsizehalf))
            self.enabled_button.setToolTip("Disabled: Option will be ignored.")
        elif not self.can_change_enabled and self.is_enabled:
            self.enabled_button.setStyleSheet(
                BLOB_BUTTON_STYLE_ENABLED_FORCED(btnsizehalf)
            )
            self.enabled_button.setToolTip("Enabled: This option is required.")
        elif not self.can_change_enabled and not self.is_enabled:
            self.enabled_button.setStyleSheet(
                BLOB_BUTTON_STYLE_DISABLED_FORCED(btnsizehalf)
            )
            self.enabled_button.setToolTip("Disabled: This option cannot be used.")
        self.enabled_button.setFixedSize(btnsizehalf * 2, btnsizehalf * 2)
        # This might be useless, since we cannot disable sub-widgets like tuples
        if enabled and self.parent_widget and not self.parent_widget.is_enabled:
            self.parent_widget.set_enabled_changeable(enabled=True)

    def is_empty(self) -> bool:
        """Checks whether the widget is empty. This can be the case for string-based widgets or the
        multiple choice-widget (:class:`~clickqt.widgets.combobox.CheckableComboBox`).\n
        Subclasses may need to override this method.

        :return: False
        """
        return False

    def get_value(self) -> tuple[t.Any, ClickQtError]:
        """Validates the value of the Qt-widget and returns the result.

        :return: Valid: (widget value or the value of a callback, :class:`~clickqt.core.error.ClickQtError.ErrorType.NO_ERROR`)\n
                 Invalid: (None, :class:`~clickqt.core.error.ClickQtError.ErrorType.CONVERTING_ERROR` or
                 :class:`~clickqt.core.error.ClickQtError.ErrorType.PROCESSING_VALUE_ERROR` or :class:`~clickqt.core.error.ClickQtError.ErrorType.REQUIRED_ERROR`)
        """
        if self.param.required and not self.is_enabled:
            self.handle_valid(False)
            return (
                None,
                ClickQtError(
                    ClickQtError.ErrorType.REQUIRED_ERROR,
                    self.widget_name,
                    self.param.param_type_name,
                ),
            )

        value = None
        raw_value = self.get_widget_value()
        multiple = self.param.multiple
        is_tuple = isinstance(self.type, click.Tuple)
        primitive_nargs = self.param.nargs > 1 and not is_tuple

        # conversion from widget contents to click data type
        def convert(value):
            return self.type.convert(
                value, self.param, click.Context(self.click_command)
            )

        try:
            if multiple or primitive_nargs:
                value = tuple((convert(value) for value in raw_value))
            else:
                value = convert(self.get_widget_value())

        except Exception as e:  # pylint: disable=broad-exception-caught
            self.handle_valid(False)
            return (
                None,
                ClickQtError(
                    ClickQtError.ErrorType.CONVERTING_ERROR, self.widget_name, e
                ),
            )
        return self.handle_callback(value)

    def handle_callback(self, value: t.Any) -> tuple[t.Any, ClickQtError]:
        """Validates **value** in the user-defined callback (if provided) and returns the result.

        :param value: The value that should be validated in the callback

        :return: Valid: (**value** or the value of a callback, :class:`~clickqt.core.error.ClickQtError.ErrorType.NO_ERROR`)\n
                 Invalid: (None, :class:`~clickqt.core.error.ClickQtError.ErrorType.ABORTED_ERROR` or
                 :class:`~clickqt.core.error.ClickQtError.ErrorType.EXIT_ERROR` or :class:`~clickqt.core.error.ClickQtError.ErrorType.PROCESSING_VALUE_ERROR`)
        """

        try:  # Consider callbacks
            ret_val = (
                self.param.process_value(click.Context(self.click_command), value),
                ClickQtError(),
            )
            self.handle_valid(True)
            return ret_val
        except click.exceptions.Abort:
            return (None, ClickQtError(ClickQtError.ErrorType.ABORTED_ERROR))
        except click.exceptions.Exit:
            return (None, ClickQtError(ClickQtError.ErrorType.EXIT_ERROR))
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.handle_valid(False)
            return (
                None,
                ClickQtError(
                    ClickQtError.ErrorType.PROCESSING_VALUE_ERROR, self.widget_name, e
                ),
            )

    @abstractmethod
    def get_widget_value(self) -> t.Any:
        """Returns the value of the Qt-widget without any checks."""

    def get_preferable_opt(self) -> str:
        long_name = max(self.param.opts, key=len, default="")
        return long_name if long_name.startswith("-") else ""

    def get_widget_value_cmdline(self) -> str:
        """Returns the value of the Qt-widget without any checks as a commandline string."""
        is_flag = self.param.to_info_dict().get("is_flag", False)
        is_count = self.param.to_info_dict().get("count", False)
        if is_flag:
            return f"{self.get_preferable_opt()} "
        if is_count:
            count = self.get_widget_value()
            return f"{self.get_preferable_opt()} " * count
        return f"{self.get_preferable_opt()} {shlex.quote(str(self.get_widget_value()))} ".lstrip()

    def handle_valid(self, valid: bool):
        """Changes the border of the widget dependent on **valid**. If **valid** == False, the border will be colored red, otherwise black.

        :param valid: Specifies whether there was no error when validating the widget

        """

        if not valid:
            self.widget.setStyleSheet(
                f"QWidget#{self.widget.objectName()}{{ border: 1px solid red }}"
            )
        else:
            self.widget.setStyleSheet(f"QWidget#{self.widget.objectName()}{{ }}")

    @staticmethod
    def get_param_default(param: click.Parameter, alternative: t.Any = None):
        """Returns the default value of **param**. If there is no default value, **alternative** will be returned."""

        default = param.default
        if callable(default):
            default = default()
        return normalize_default(default, alternative)


class NumericField(BaseWidget):
    """Provides basic functionalities for numeric based widgets

    :param otype: The type which specifies the clickqt widget type. This type may be different compared to **param**.type when dealing with click.types.CompositeParamType-objects
    :param param: The parameter from which **otype** came from
    :param kwargs: Additionally parameters ('parent', 'widgetsource', 'com', 'label') needed for
                    :class:`~clickqt.widgets.basewidget.MultiWidget`- / :class:`~clickqt.widgets.confirmationwidget.ConfirmationWidget`-widgets
    """

    def set_value(self, value: t.Any):
        self.widget.setValue(
            self.type.convert(
                value=str(value),
                param=self.click_command,
                ctx=click.Context(self.click_command),
            )
        )

    def set_minimum(self, minval: t.Union[int, float]):
        """Sets the minimum value."""

        self.widget.setMinimum(minval)

    def set_maximum(self, maxval: t.Union[int, float]):
        """Sets the maximum value."""

        self.widget.setMaximum(maxval)

    def get_widget_value(self) -> t.Union[int, float]:
        return self.widget.value()


class ComboBoxBase(BaseWidget):
    """Provides basic functionalities for click.types.Choice based widgets

    :param otype: The type which specifies the clickqt widget type. This type may be different compared to **param**.type when dealing with click.types.CompositeParamType-objects
    :param param: The parameter from which **otype** came from
    :param kwargs: Additionally parameters ('parent', 'widgetsource', 'com', 'label') needed for
                    :class:`~clickqt.widgets.basewidget.MultiWidget`- / :class:`~clickqt.widgets.confirmationwidget.ConfirmationWidget`-widgets
    """

    def __init__(self, otype: click.ParamType, param: click.Parameter, **kwargs):
        super().__init__(otype, param, **kwargs)

        assert isinstance(
            otype, click.Choice
        ), f"'otype' must be of type '{click.Choice}', but is '{type(otype)}'."

        self.add_items(otype.choices)

    @abstractmethod
    def add_items(self, items: t.Iterable[str]):
        """Adds each of the strings in **items** to the checkable combobox."""


class MultiWidget(BaseWidget):
    """Provides basic functionalities for click.types.CompositeParamType based widgets and multi value widgets.

    :param otype: The type which specifies the clickqt widget type. This type may be different compared to **param**.type when dealing with click.types.CompositeParamType-objects
    :param param: The parameter from which **otype** came from
    :param kwargs: Additionally parameters ('parent', 'widgetsource', 'com', 'label') needed for
                    :class:`~clickqt.widgets.basewidget.MultiWidget`- / :class:`~clickqt.widgets.confirmationwidget.ConfirmationWidget`-widgets
    """

    def __init__(self, otype: click.ParamType, param: click.Parameter, **kwargs):
        super().__init__(otype, param, **kwargs)

        self.children: t.Union[t.Iterable[BaseWidget], t.dict_values[BaseWidget]] = []

    def init(self):
        """Sets the value of the (child-)widgets according to envvar or default values.
        If the envvar values are None, the defaults values will be considered.
        """

        if self.parent_widget is None:
            # Consider envvar
            if (
                envvar_values := self.param.resolve_envvar_value(
                    click.Context(self.click_command)
                )
            ) is not None:
                # self.type.split_envvar_value(envvar_values) does not work because clicks "self.envvar_list_splitter" is not set corrently
                self.set_value(envvar_values.split(os.path.pathsep))
            elif (
                default := BaseWidget.get_param_default(self.param, None)
            ) is not None:  # Consider default value
                self.set_value(default)

    def consider_metavar(self, child: BaseWidget, pos: int):
        if self.param.metavar is None:
            child.layout.removeWidget(child.label)
            child.label.deleteLater()
        else:
            assert isinstance(self.param.metavar, t.Iterable) and pos < len(
                self.param.metavar
            ), f"metavar in option '{self.param.name}' is not correct."

            child.layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            child.widget.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
            )
            label_text = self.param.metavar[pos]
            child.label.setText(label_text + (":" if label_text else ""))

    def set_value(self, value: t.Iterable[t.Any]):
        if value is None:
            self.set_enabled_changeable(enabled=False)
            return

        self.set_enabled_changeable(enabled=len(value) > 0)
        if len(value) != self.param.nargs:
            raise click.BadParameter(
                ngettext(
                    "Takes {nargs} values but 1 was given.",
                    "Takes {nargs} values but {len} were given.",
                    len(value),
                ).format(nargs=self.param.nargs, len=len(value)),
                ctx=click.Context(self.click_command),
                param=self.param,
            )

        for i, c in enumerate(self.children):
            c.set_value(value[i])

    def handle_valid(self, valid: bool):
        for c in self.children:
            c.handle_valid(valid)

    def is_empty(self) -> bool:
        """ "Checks whether the widget is empty. This is the case when there are no children or when at least one (string-based) children is empty.

        :return: True, if this widget has no children or at least one children is empty, False otherwise
        """

        if len(self.children) == 0:
            return True

        return any(c.is_empty() for c in self.children)

    def get_widget_value(self) -> t.Iterable[t.Any]:
        return [c.get_widget_value() for c in self.children]

    def get_widget_value_cmdline(self) -> str:
        optname = self.get_preferable_opt()
        childcmds = [
            c.get_widget_value_cmdline().replace(optname, "").strip()
            for c in self.children
        ]
        cmdstr = " ".join(childcmds)
        return f"{self.get_preferable_opt()} {cmdstr} "
