from __future__ import annotations

import typing as t

import click
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from clickqt.core.control import Control
from clickqt.core.gui import CustomBindingType


def qtgui_from_click(
    cmd: click.Command,
    custom_mapping: t.Optional[dict[click.ParamType, CustomBindingType]] = None,
    application_name: t.Optional[str] = None,
    window_icon: t.Optional[str] = None,
    invocation_command: t.Optional[str] = None,
):
    """This function is used to generate the GUI for a given command. It takes a click command as its argument and returns a Control object
    that contains the GUI, execution logic, and the generated widgets used for the parameters of the command.

    :param cmd: The click.Command-object to create a GUI from
    :param custom_mapping: The dictionary containing the customized mapping from a user-defined click type to an intended Qt Widget.
    :param application_name: Name of the application, defaults to None (= 'python')
    :param window_icon: Path to an icon, changes the icon of the application, defaults to None (= no icon)
    :param invocation_command: Command prefix used for generated/imported command lines, defaults to None (= inferred)

    :return: The control-object that contains the GUI
    """
    if QApplication.instance() is None:
        # Testing: The testing suite creates a QApplication instance
        app = QApplication([])
        app.setWindowIcon(QIcon(window_icon))
        app.setApplicationName(application_name)
        app.setStyleSheet(
            """QToolTip {
                background-color: #182035;
                color: white;
                border: white solid 1px
                }"""
        )

    return Control(cmd, custom_mapping, invocation_command=invocation_command)
