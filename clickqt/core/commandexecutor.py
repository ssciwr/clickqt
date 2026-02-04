from __future__ import annotations

import sys
import typing as t
import traceback
import click
from PySide6.QtCore import Signal, QObject, Slot, QThread


class CommandExecutor(QObject):
    """Worker which executes the received tasks/callbacks"""

    finished: Signal = Signal()
    # Internal Qt-signal emitted when :func:`~clickqt.core.commandexecutor.CommandExecutor.run`-Slot has finished

    @Slot(list, click.Context)
    def run(
        self, tasks: t.Iterable[t.Callable], ctx: click.Context
    ):  # pragma: no cover; Tested in test_execution.py
        """Pushes the current context on the click internal stack and executes the received tasks.
        When the execution is done, the finished signal will be emitted

        :param tasks: The callbacks to execute
        :param ctx: The current context which should be pushed on the click internal stack
        """

        # Push context of selected command, needed for @click.pass_context and @click.pass_obj
        click.globals.push_context(ctx)

        for task in tasks:
            if QThread.currentThread().isInterruptionRequested():
                break
            try:
                task()
            except SystemExit as e:
                print(f"SystemExit-Exception, return code: {e.code}", file=sys.stderr)
            except Exception:  # pylint: disable=broad-exception-caught
                traceback.print_exc(file=sys.stderr)

        self.finished.emit()
