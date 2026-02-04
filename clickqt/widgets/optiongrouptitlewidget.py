from __future__ import annotations
import typing as t
from qt_collapsible_section import Section
import click
from clickqt.widgets.basewidget import BaseWidget


class OptionGroupTitleWidget(BaseWidget):
    widget_type = Section

    def __init__(
        self,
        otype: click.ParamType,
        param: click.Parameter,
        parent: t.Optional["BaseWidget"] = None,
        **kwargs,
    ):
        self.child_basewidgets: list[BaseWidget] = []
        super().__init__(otype, param, **kwargs)
        self.widget_name = param._GroupTitleFakeOption__group.__dict__["_name"]
        self.widget.setTitle(self.widget_name)
        self.widget.setToolTip(self.param.help)
        self.enabled_button.clicked.connect(
            lambda: self.set_enabled_changeable(enabled=self.enabled_button.isChecked())
            if self.can_change_enabled
            else None
        )
        self.label.setText(f"<b>{self.widget_name}</b>")
        self.layout.removeWidget(self.heading)

    def get_widget_value(self) -> t.Any:
        return ""

    def set_value(self, value: t.Any):
        pass

    def get_widget_value_cmdline(self) -> str:
        return ""
