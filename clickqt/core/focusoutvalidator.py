from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QObject, QEvent
from clickqt.core.error import ClickQtError
from clickqt.widgets.base_widget import BaseWidget
from clickqt.widgets.nvaluewidget import NValueWidget
from click import Context
from typing import Tuple, Any
import sys

class FocusOutValidator(QWidget):
    """
        Validates a widget value when the widget goes out of focus
    """

    def __init__(self, widget: BaseWidget):
        super().__init__()
        
        self.widget = widget

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.FocusOut:
            value, err = self.validate()
            #if value is not None and err.type == ClickQtError.ErrorType.NO_ERROR:
                #TODO: Check if value has correct type
                #self.widget.setValue(value)
            #    pass
            #else:
            #    print(err.message(), file=sys.stderr)

        return QWidget.eventFilter(self, watched, event)
    
    def validate(self) -> Tuple[Any, ClickQtError]:
        """
            Validates the value of the widget, which went out of focus
        """
        if (self.widget.parent_widget is not None and not isinstance(self.widget.parent_widget, NValueWidget)):
            return self.widget.parent_widget.getValue()
        elif self.widget.parent_widget is None:
            return self.widget.getValue()

        # self.widget.parent_widget == NValueWidget -> We have a child here

        try: # Try to convert the provided value into the corresponding click object type
            ret_val = self.widget.click_object.type.convert(value=self.widget.getWidgetValue(), param=None, ctx=Context(self.widget.click_command))
            # Don't consider callbacks because we have only one child here
            self.widget.handleValid(True)
            return (ret_val, ClickQtError())
        except Exception as e:
            self.widget.handleValid(False)
            return (None, ClickQtError(ClickQtError.ErrorType.CONVERTION_ERROR, self.widget.widget_name, e))

       
    