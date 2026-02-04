from __future__ import annotations

import typing as t

import click
from PySide6.QtWidgets import QGroupBox, QHBoxLayout

from clickqt.widgets.basewidget import BaseWidget, MultiWidget


class TupleWidget(MultiWidget):
    """Represents a click.types.Tuple-object.
    The child widgets are set according to :func:`~clickqt.widgets.basewidget.MultiWidget.init`.

    :param otype: The type which specifies the clickqt widget type. This type may be different compared to **param**.type when dealing with click.types.CompositeParamType-objects
    :param param: The parameter from which **otype** came from
    :param widgetsource: A reference to :func:`~clickqt.core.gui.GUI.create_widget`
    :param parent: The parent BaseWidget of **otype**, defaults to None. Needed for :class:`~clickqt.widgets.basewidget.MultiWidget`-widgets
    :param kwargs: Additionally parameters ('com', 'label') needed for
                    :class:`~clickqt.widgets.basewidget.MultiWidget`- / :class:`~clickqt.widgets.confirmationwidget.ConfirmationWidget`-widgets
    """

    widget_type = QGroupBox  #: The Qt-type of this widget.

    def __init__(
        self,
        otype: click.ParamType,
        param: click.Parameter,
        widgetsource: t.Callable[[t.Any], BaseWidget],
        parent: t.Optional[BaseWidget] = None,
        **kwargs,
    ):
        super().__init__(otype, param, parent=parent, **kwargs)

        assert isinstance(
            otype, click.Tuple
        ), f"'otype' must be of type '{click.Tuple}', but is '{type(otype)}'."
        assert otype.is_composite, "otype.is_composite should be True"

        self.widget.setLayout(QHBoxLayout())

        for i, child_type in enumerate(
            otype.types if hasattr(otype, "types") else otype
        ):
            nargs = self.param.nargs
            self.param.nargs = 1
            bw: BaseWidget = widgetsource(
                child_type, self.param, widgetsource=widgetsource, parent=self, **kwargs
            )
            self.param.nargs = nargs

            self.consider_metavar(bw, i)
            self.widget.layout().addWidget(bw.container)
            self.children.append(bw)

        self.init()
