from __future__ import annotations

import typing as t

import click
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from clickqt.core.control import Control


def qtgui_from_click(cmd: click.Command, application_name: t.Optional[str] = None, window_icon: t.Optional[str] = None):
    """This function is used to generate the GUI for a given command. It takes a click command as its argument and returns a Control object
    that contains the GUI, execution logic, and the generated widgets used for the parameters of the command.

    :param cmd: The click.Command-object to create a GUI from
    :param application_name: Name of the application, defaults to None (= 'python')
    :param window_icon: Path to an icon, changes the icon of the application, defaults to None (= no icon)
                  
    :return: The control-object that contains the GUI
    """
    if QApplication.instance() is None:
        # Testing: The testing suite creates a QApplication instance
        app = QApplication([])
        app.setWindowIcon(QIcon(window_icon))
        app.setApplicationName(application_name)

    return Control(cmd)
