from PySide6.QtWidgets import QGroupBox, QVBoxLayout
from clickqt.widgets.basewidget import BaseWidget
from clickqt.widgets.tuplewidget import TupleWidget
from click import Parameter, Context, ParamType, BadParameter
from typing import Any, List, Callable
from gettext import ngettext


class MultiValueWidget(BaseWidget):
    widget_type = QGroupBox
    
    def __init__(self, otype:ParamType, param:Parameter, widgetsource:Callable[[Any], BaseWidget], parent:BaseWidget=None, *args, **kwargs):
        super().__init__(otype, param, parent, *args, **kwargs)
        self.children:list[BaseWidget] = []
        self.widget.setLayout(QVBoxLayout())

        if param.nargs < 2:
            raise TypeError(f"param.nargs should be >= 2 when creating a MultiValueWIdget but is {param.nargs}.")
        
        # Add param.nargs widgets of type otype
        for i in range(param.nargs):
            nargs = param.nargs
            param.nargs = 1 # Stop recursion
            bw:BaseWidget = widgetsource(otype, param, *args, parent=self, widgetsource=widgetsource, **kwargs)
            param.nargs = nargs # click needs the right value for a correct conversion
            bw.layout.removeWidget(bw.label)
            bw.label.deleteLater()
            self.widget.layout().addWidget(bw.container)
            self.children.append(bw)

        if self.parent_widget is None:
            if (envvar_values := self.param.resolve_envvar_value(Context(self.click_command))) is not None: # Consider envvar
                self.setValue(self.type.split_envvar_value(envvar_values))
            elif (default := BaseWidget.getParamDefault(param, None)) is not None: # Consider default value
                    self.setValue(default)
        
    def setValue(self, value:list[Any]):
        if len(value) != self.param.nargs:
            raise BadParameter(ngettext("Takes {nargs} values but 1 was given.", "Takes {nargs} values but {len} were given.",len(value))
                               .format(nargs=self.param.nargs, len=len(value)),
                               ctx=Context(self.click_command),
                               param=self.param)
        
        for i,c in enumerate(self.children):
            c.setValue(value[i])

    def handleValid(self, valid: bool):
        for c in self.children:
            if not isinstance(c, TupleWidget):
                BaseWidget.handleValid(c, valid)
            else:
                c.handleValid(valid) # Recursive

    def isEmpty(self) -> bool:
        if len(self.children) == 0:
            return True
        
        for c in self.children:
            if c.isEmpty():
                return True
        
        return False
    
    def getWidgetValue(self) -> List[Any]:
        return [c.getWidgetValue() for c in self.children]
    