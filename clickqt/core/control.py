from __future__ import annotations

import typing as t
import sys
from functools import reduce
import re
import inspect
import click

try:
    from click.shell_completion import split_arg_string
except ImportError:  # pragma: no cover - compatibility with older click
    from click.parser import split_arg_string
from click_option_group._core import _GroupTitleFakeOption, GroupedOption
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QVBoxLayout,
    QTabWidget,
    QScrollArea,
    QApplication,
    QSizePolicy,
    QLabel,
    QLayout,
)
from PySide6.QtCore import QThread, QObject, Signal, Slot, Qt
from PySide6.QtGui import QPalette, QClipboard

from clickqt.core.gui import GUI
from clickqt.core.commandexecutor import CommandExecutor
from clickqt.core.defaults import has_explicit_default, has_truthy_default
from clickqt.core.error import ClickQtError
from clickqt.widgets.basewidget import BaseWidget
from clickqt.widgets.messagebox import MessageBox
from clickqt.widgets.filefield import FileField


class Control(QObject):  # pylint: disable=too-many-public-methods
    """Regulates the creation of the GUI with their widgets according to clicks parameter types and causes the execution/abortion of a selected command.

    :param cmd: The callback function from which a GUI should be created
    """

    #: Internal Qt-signal, which will be emitted when the :func:`~clickqt.core.control.Control.start_execution`-Slot was triggered and executed successfully.
    requestExecution: Signal = Signal(list, click.Context)  # Generics do not work here

    def __init__(
        self,
        cmd: click.Command,
        custom_mapping: dict = None,
        is_ep: bool = True,
        ep_or_path: str = " ",
    ):
        """Initializing the GUI object and the registries together with the differentiation of a group command and a simple command."""

        super().__init__()

        self.gui = GUI()
        self.cmd = cmd

        self.is_ep = is_ep
        self.ep_or_path = ep_or_path

        self.custom_mapping = custom_mapping
        if self.custom_mapping is not None and len(self.custom_mapping) >= 1:
            self.gui.update_typedict(self.custom_mapping)

        # Create a worker in another thread when the user clicks the run button
        # Don't destroy a thread when no command is running and the user closes the application
        # Otherwise "QThread: Destroyed while thread is still running" would be appear
        self.worker_thread: QThread = None
        self.worker: CommandExecutor = None

        # Connect GUI buttons with slots
        self.gui.run_button.clicked.connect(self.start_execution)
        self.gui.stop_button.clicked.connect(self.stop_execution)
        self.gui.copy_button.clicked.connect(self.construct_command_string)
        self.gui.import_button.clicked.connect(self.import_cmdline)

        # Groups-Command-name concatinated with ":" to command-option-names to BaseWidget
        self.widget_registry: dict[str, dict[str, BaseWidget]] = {}
        self.command_registry: dict[str, dict[str, tuple[int, t.Callable]]] = {}

        # Add all widgets
        self.parse(self.gui.widgets_container, cmd, cmd.name)

        self.gui.construct()

    def __call__(self):
        """Shows the GUI according to :func:`~clickqt.core.gui.GUI.__call__` of :class:`~clickqt.core.gui.GUI`."""

        self.gui()

    def set_ep_or_path(self, ep_or_path):
        self.ep_or_path = ep_or_path

    def set_is_ep(self, is_ep):
        self.is_ep = is_ep

    def set_custom_mapping(self, custom_mapping):
        self.custom_mapping = custom_mapping

    def parameter_to_widget(
        self,
        command: click.Command,
        groups_command_name: str,
        param: click.Parameter,
    ) -> QWidget:
        """Creates a clickqt widget according to :func:`~clickqt.core.gui.GUI.create_widget` and returns the container of the widget (label-element + Qt-widget).

        :param command: The click command of the provided **param**
        :param groups_command_name: The hierarchy of the **command** as string whereby the names of the components are
                                    concatenated according to :func:`~clickqt.core.control.Control.concat`
        :param param: The click parameter whose type a clickqt widget should be created from

        :return: The container of the created widget (label-element + Qt-widget)
        """

        assert param.name, "No parameter name specified"
        assert self.widget_registry[groups_command_name].get(param.name) is None

        widget = self.gui.create_widget(
            param.type,
            param,
            widgetsource=self.gui.create_widget,
            com=command,
        )

        self.widget_registry[groups_command_name][param.name] = widget
        self.command_registry[groups_command_name][param.name] = (
            param.nargs,
            type(param.type).__name__,
        )

        return widget.container

    def concat(self, a: str, b: str) -> str:
        """Concatenates the strings a and b with ':' and returns the result."""

        return a + ":" + b

    def parse(
        self,
        tab_widget: QWidget,
        cmd: click.Command,
        group_name: str,
        group_names_concatenated: str = "",
    ):
        if isinstance(cmd, click.Group):
            child_tabs: QWidget = None
            concat_group_names = (
                self.concat(group_names_concatenated, group_name)
                if group_names_concatenated
                else group_name
            )
            if len(cmd.params) > 0:
                child_tabs = QWidget()
                child_tabs.setLayout(QVBoxLayout())
                group_params = self.parse_cmd(cmd, concat_group_names)
                group_params.widget().layout().setContentsMargins(0, 0, 0, 0)
                group_params.setSizePolicy(
                    QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
                )  # Group params don't have to be resizable
                child_tabs.layout().addWidget(group_params)
                child_tabs.layout().addWidget(
                    self.parse_cmd_group(cmd, concat_group_names)
                )
            else:
                child_tabs = self.parse_cmd_group(cmd, concat_group_names)

            child_tabs.setAutoFillBackground(True)
            child_tabs.setBackgroundRole(
                QPalette.ColorRole.Window
            )  # Remove white spacing between widgets

            if tab_widget == self.gui.widgets_container:
                self.gui.widgets_container = child_tabs
            else:
                tab_widget.addTab(child_tabs, group_name)
        elif tab_widget == self.gui.widgets_container:
            self.gui.widgets_container = self.parse_cmd(cmd, cmd.name)
        else:
            tab_widget.addTab(
                self.parse_cmd(
                    cmd,
                    self.concat(group_names_concatenated, cmd.name)
                    if group_names_concatenated
                    else cmd.name,
                ),
                group_name,
            )

    def parse_cmd_group(
        self, cmdgroup: click.Group, group_names_concatenated: str
    ) -> QTabWidget:
        """Creates for every group in **cmdgroup** a QTabWidget instance and adds every command in **cmdgroup** as a tab to it.
        The creation of the content of every tab is realized by calling :func:`~clickqt.core.control.Control.parse_cmd`.
        To realize command hierachies, this method is called recursively.

        :param cmdgroup: The group from which a QTabWidget with content should be created
        :param group_names_concatenated: The hierarchy of **cmdgroup** as string whereby the names of the components are
                                         concatenated according to :func:`~clickqt.core.control.Control.concat`

        :returns: A Qt-GUI representation in a QTabWidget of **cmdgroup**
        """

        group_tab_widget = QTabWidget()
        for group_name, group_cmd in cmdgroup.commands.items():
            self.parse(
                group_tab_widget, group_cmd, group_name, group_names_concatenated
            )

        return group_tab_widget

    # pylint: disable-next=too-many-locals,too-many-statements
    def parse_cmd(
        self,
        cmd: click.Command,
        groups_command_name: str,
    ) -> QScrollArea:
        """Creates for every click parameter in **cmd** a clickqt widget and returns them stored in a QScrollArea.
        The widgets are divided into a "Required arguments", "Optional arguments" and "Option Group" part.

        :param cmd: The command from which a QTabWidget with content should be created
        :param groups_command_name: The hierarchy of **cmd** as string whereby the names of the components are
                                    concatenated according to :func:`~clickqt.core.control.Control.concat`

        :returns: The created clickqt widgets stored in a QScrollArea
        """
        cmdbox = QWidget()
        cmdbox.setLayout(QVBoxLayout())
        cmdbox.layout().setAlignment(Qt.AlignmentFlag.AlignTop)

        def mkbox(label: str):
            box = QWidget()
            box.setLayout(QVBoxLayout())
            box_label = QLabel(text=f"<b>'{label}'</b>")
            box_label.setTextFormat(Qt.TextFormat.RichText)  # Bold text
            box.layout().addWidget(box_label)
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            box.layout().addWidget(line)
            box.layout().setAlignment(Qt.AlignmentFlag.AlignTop)
            return box

        required_box = mkbox("Required Parameters")
        optional_box = mkbox("Optional Parameters")

        INITIAL_CHILD_WIDGETS = len(required_box.children())  # layout, label, line

        assert (
            self.widget_registry.get(groups_command_name) is None
        ), f"Not a unique group_command_name_concat ({groups_command_name})"

        self.widget_registry[groups_command_name] = {}
        self.command_registry[groups_command_name] = {}

        # parameter name to flag values
        feature_switches: dict[str, QLayout] = {}
        current_option_group: str = ""
        option_group_layouts: dict[str, QVBoxLayout] = {}

        for param in cmd.params:
            is_flag = hasattr(param, "is_flag") and param.is_flag
            has_flag_value = hasattr(param, "flag_value")
            flag_value = param.flag_value if has_flag_value else None
            widget_required = param.required or isinstance(param, click.Argument)
            is_option_group = isinstance(param, _GroupTitleFakeOption)
            is_grouped_option = isinstance(param, GroupedOption)
            target_layout = (required_box if widget_required else optional_box).layout()
            created_widget = None

            if not isinstance(param, click.core.Parameter):
                continue
            if is_flag and has_flag_value and isinstance(flag_value, str):
                # param is a flag using a feature switch
                if feature_switches.get(param.name) is None:
                    feature_switches[param.name] = []
                feature_switches[param.name].append(param)
            else:
                # most other params
                created_widget = self.parameter_to_widget(
                    cmd,
                    groups_command_name,
                    param,
                )
                if is_option_group:
                    # the "heading" of the option group, creates a new section
                    current_option_group = param.name
                    option_group_layouts[current_option_group] = QVBoxLayout()
                else:
                    if is_grouped_option:
                        # a member of an option group
                        assert (
                            current_option_group is not None
                        ), "Option groups are out of order!"
                        target_layout = option_group_layouts.get(current_option_group)
                    self.widget_registry[groups_command_name][
                        param.name
                    ].set_enabled_changeable(
                        enabled=widget_required
                        or (
                            has_truthy_default(param)
                            if is_flag
                            else (widget_required or has_explicit_default(param))
                        ),
                        changeable=not widget_required,
                    )
            if created_widget is not None:
                assert target_layout is not None, "No target layout for widget"
                target_layout.addWidget(created_widget)

        for keys, values in option_group_layouts.items():
            self.widget_registry[groups_command_name][keys].widget.setContentLayout(
                values
            )

        # Create for every feature switch a ComboBox
        for param_name, switch_names in feature_switches.items():
            choice = click.Option(
                [f"--{param_name}"],
                type=click.Choice([x.flag_value for x in switch_names]),
                required=reduce(lambda x, y: x | y.required, switch_names, False),
            )
            default = next(
                (x.flag_value for x in switch_names if has_truthy_default(x)),
                switch_names[0].flag_value,
            )  # First param with default==True is the default
            (required_box if choice.required else optional_box).layout().addWidget(
                self.parameter_to_widget(
                    cmd,
                    groups_command_name,
                    choice,
                )
            )
            self.widget_registry[groups_command_name][param_name].set_value(default)
        helptext = cmd.help
        cmdbox.layout().addWidget(
            QLabel(text=helptext.strip() if helptext else "<No docstring provided>")
        )
        for box in required_box, optional_box:
            if len(box.children()) > INITIAL_CHILD_WIDGETS:
                cmdbox.layout().addWidget(box)

        cmd_tab_widget = QScrollArea()
        cmd_tab_widget.setFrameShape(QFrame.Shape.NoFrame)  # Remove black border
        cmd_tab_widget.setBackgroundRole(QPalette.ColorRole.Window)
        cmd_tab_widget.setWidgetResizable(True)  # Widgets should use the whole area
        cmd_tab_widget.setWidget(cmdbox)

        return cmd_tab_widget

    def check_error(self, err: ClickQtError) -> bool:
        """Checks whether **err** contains an error and prints on error case the message of it to sys.stderr.

        :return: True, if **err** contains an error, False otherwise"""

        if err.type != ClickQtError.ErrorType.NO_ERROR:
            if message := err.message():  # Don't print on context exit
                print(message, file=sys.stderr)
            return True

        return False

    def current_command_hierarchy(
        self, tab_widget: QWidget, cmd: click.Command
    ) -> list[click.Command]:
        """Returns the hierarchy of the command of the selected tab as list whereby the order of the list is from root command
        to the selected command.

        :param tab_widget: The currend widget of the root-QTabWidget
        :param cmd: The click command provided to :func:`~clickqt.core.control.Control`

        :return: The hierarchy of the command of the selected tab as ordered list (root command to selected command)
        """

        if isinstance(cmd, click.Group):
            if len(cmd.params) > 0:  # Group has params
                tab_widget = tab_widget.findChild(QTabWidget)

            assert isinstance(tab_widget, QTabWidget)

            command = cmd.get_command(
                ctx=None, cmd_name=tab_widget.tabText(tab_widget.currentIndex())
            )

            return [cmd] + self.current_command_hierarchy(
                tab_widget.currentWidget(), command
            )

        return [cmd]

    def select_current_command_hierarchy(
        self, commands: list[str]
    ) -> tuple[list[str], QWidget]:
        """Set up the tab widgets such that the command gets selected, up to `commands`."""
        widget = self.gui.widgets_container
        fulfilled_cmds = []
        for command in commands:
            if not isinstance(widget, QTabWidget):
                return fulfilled_cmds, widget
            subcommands = [widget.tabText(i) for i in range(widget.count())]
            if command not in subcommands:
                return fulfilled_cmds, widget
            tabidx = subcommands.index(command)
            fulfilled_cmds.append(command)
            widget.setCurrentIndex(tabidx)
            widget = widget.currentWidget()
        return fulfilled_cmds, widget

    def clean_command_string(self, word, text):
        """Returns a string without any special characters using regex."""
        text = re.sub(rf"\b{re.escape(word)}\b", "", text)
        text = re.sub(r"[^a-zA-Z0-9 .-]", " ", text)
        return text

    def command_to_string(self, hierarchy_selected_command_name: str):
        """Returns the current command name."""
        hierarchy_selected_command_name = self.clean_command_string(
            self.cmd.name, hierarchy_selected_command_name
        )
        return self.ep_or_path + " " + hierarchy_selected_command_name

    def hierarchy_to_str(self, command_hierarchy: list[str]) -> str:
        assert isinstance(command_hierarchy, list)
        return ":".join(command_hierarchy)

    def command_to_cli_string(self, command_hierarchy: list[str]):
        """Returns the click command line string corresponding to the current UI setup."""
        param_strings = ""
        hierarchy_str = self.hierarchy_to_str(command_hierarchy)
        widgets = list(self.widget_registry[hierarchy_str].values())
        for widget in filter(lambda widget: widget.is_enabled, widgets):
            param_strings += widget.get_widget_value_cmdline()
        msgpieces = []
        if self.is_ep:
            command_hierarchy = command_hierarchy[1:]
        if not self.is_ep:
            if (
                isinstance(self.cmd, click.Group)
                and command_hierarchy[0] == self.cmd.name
            ):
                command_hierarchy = command_hierarchy[1:]
            msgpieces.append("python")
        msgpieces.append(self.ep_or_path)
        msgpieces.extend(command_hierarchy)
        msgpieces.append(param_strings)
        msg = " ".join(msgpieces).strip()
        return msg

    @Slot()
    def stop_execution(self):
        """Qt-Slot, which stops the execution of the command(-hierarchy) which is currently running."""

        print("Execution stopped!", file=sys.stderr)
        self.worker_thread.terminate()
        self.execution_finished()

    @Slot()
    def execution_finished(self):
        """Qt-Slot, which deletes the internal worker-object and resets the buttons of the GUI.
        This slot is automatically executed when the execution of a command has finished.
        """

        self.worker_thread.deleteLater()
        self.worker.deleteLater()

        self.worker_thread = None
        self.worker = None

        self.gui.run_button.setEnabled(True)
        self.gui.stop_button.setEnabled(False)

    @Slot()
    def start_execution(self):
        """Qt-Slot, which validates the selected command hierarchy and causes (on success) their execution in another thread by
        emitting the :func:`~clickqt.core.control.Control.requestExecution`-Signal. Widgets that will show a dialog will be validated at last.
        This slot is automatically executed when the user clicks on the 'Run'-button.
        """

        self.gui.terminal_output.clear()

        hierarchy_selected_command = self.current_command_hierarchy(
            self.gui.widgets_container, self.cmd
        )

        def run_command(
            command: click.Command, hierarchy: list[str]
        ) -> t.Optional[t.Callable]:
            kwargs: dict[str, t.Any] = {}
            has_error = False
            dialog_widgets: list[BaseWidget] = []  # widgets that will show a dialog
            hierarchy_str = self.hierarchy_to_str(hierarchy)

            if (
                self.widget_registry.get(hierarchy_str) is not None
            ):  # Groups with no options are not in the dict
                # Check the values of all non dialog widgets for errors
                for option_name, widget in self.widget_registry[hierarchy_str].items():
                    if not widget.is_enabled:
                        kwargs[option_name] = widget.get_param_default(
                            widget.param, () if widget.param.multiple else None
                        )
                        continue
                    if isinstance(widget, MessageBox):
                        dialog_widgets.append(
                            widget
                        )  # MessageBox widgets should be shown at last
                    elif (
                        isinstance(widget, FileField)
                        and "r" in widget.type.mode
                        and widget.get_widget_value() == "-"
                    ):
                        dialog_widgets.insert(
                            0, widget
                        )  # FileField widgets with input dialog should be shown at last, but before MessageBox widgets
                    else:
                        widget_value, err = widget.get_value()
                        has_error |= self.check_error(err)

                        if widget.param.expose_value:
                            kwargs[option_name] = widget_value

                if has_error:
                    return None

                # Now check the values of all dialog widgets for errors
                for widget in dialog_widgets:
                    widget_value, err = widget.get_value()
                    if isinstance(widget, FileField):
                        assert callable(widget_value)
                        widget_value, err = widget_value()

                    if self.check_error(err):
                        return None

                    if widget.param.expose_value:
                        kwargs[widget.param.name] = widget_value

            if len(callback_args := inspect.getfullargspec(command.callback).args) > 0:
                args: list[t.Any] = []
                for ca in callback_args:  # Bring the args in the correct order
                    args.append(
                        kwargs.pop(ca, None)
                    )  # Remove explicitly mentioned args from kwargs
                print(
                    f"For command details, please call '{self.command_to_string(hierarchy_str)} --help'"
                )
                print(self.command_to_cli_string(hierarchy))
                return lambda: command.callback(*args, **kwargs)
            return lambda: command.callback(  # pylint: disable=unnecessary-lambda
                **kwargs
            )

        callables: list[t.Callable] = []
        for i, command in enumerate(hierarchy_selected_command, 1):
            hierarchy = [g.name for g in hierarchy_selected_command[:i]]
            if (c := run_command(command, hierarchy)) is not None:
                callables.append(c)

        if len(callables) == len(hierarchy_selected_command):
            self.gui.run_button.setEnabled(False)
            self.gui.stop_button.setEnabled(True)

            self.worker_thread = QThread()
            self.worker_thread.start()
            self.worker = CommandExecutor()
            self.worker.moveToThread(self.worker_thread)
            self.worker.finished.connect(self.worker_thread.quit)
            self.worker.finished.connect(self.execution_finished)
            self.requestExecution.connect(self.worker.run)

            self.requestExecution.emit(
                callables, click.Context(hierarchy_selected_command[-1])
            )

    def get_hierarchy(self):
        return [
            g.name
            for g in self.current_command_hierarchy(
                self.gui.widgets_container, self.cmd
            )
        ]

    def construct_command_string(self):
        """
        Build a shell-executable command from the current state of the GUI and put it into the clipboard.
        """
        self.gui.terminal_output.clear()
        message = self.command_to_cli_string(self.get_hierarchy())
        clip_board = QApplication.clipboard()
        clip_board.setText(message, QClipboard.Clipboard)
        click.echo(f"Copied to clipboard: '{message}'")

    def get_clipboard(self) -> str:
        """Obtain the clipboard as a string."""
        return QApplication.clipboard().text()

    def import_cmdline(self) -> None:
        """Set the values of the widgets according to the text in the clipboard."""
        self.gui.terminal_output.clear()
        cmdstr = self.get_clipboard()
        click.echo(f"Importing '{cmdstr}' ...")
        splitstrs = split_arg_string(cmdstr)
        click.echo(f"Read as: '{splitstrs}' ...")
        error = ClickQtError()

        # sanity checks
        if self.is_ep:
            if len(splitstrs) == 0 or splitstrs[0] != self.ep_or_path:
                error = ClickQtError(
                    ClickQtError.ErrorType.PROCESSING_VALUE_ERROR,
                    "Cannot import due to missing or wrong entry point name",
                )
        elif len(splitstrs) <= 3:
            error = ClickQtError(
                ClickQtError.ErrorType.PROCESSING_VALUE_ERROR,
                "Cannot import due to missing or wrong file/function combination",
            )
        if self.check_error(error):
            return
        if self.is_ep:
            splitstrs.pop(0)
        else:
            splitstrs = splitstrs[2:]
        click.echo(f"Arguments w/ command: {splitstrs}")
        hierarchystrs, _ = self.select_current_command_hierarchy(splitstrs)
        click.echo(f"Set tabs to: '{hierarchystrs}' from '{splitstrs}'")
        for hierarchystr in hierarchystrs:
            splitstrs.remove(hierarchystr)
        click.echo(f"Arguments w/o command: {splitstrs}")
        commandstr = self.hierarchy_to_str(hierarchystrs)

        cmd: click.Group = self.cmd
        for cmdname in hierarchystrs:
            cmd = cmd.commands[cmdname]
        ctx = click.Context(cmd)
        cmd.parse_args(ctx, splitstrs[:])
        if commandstr:
            relevant_widgets = self.widget_registry[self.cmd.name + ":" + commandstr]
        else:
            relevant_widgets = self.widget_registry[self.cmd.name]

        for paramname, paramvalue in ctx.params.items():
            widget = relevant_widgets[paramname]
            widget.set_value(paramvalue)
