""" Contains the FilePathField class """
from __future__ import annotations

import click
from PySide6.QtWidgets import QLineEdit
from clickqt_utils.extensions import PathWithExtensions

from clickqt.widgets.textfield import PathField


class FilePathField(PathField):
    """Represents a click.types.Path object.

    :param otype: The type which specifies the clickqt widget type.
        This type may be different compared to **param**.type when dealing with click.types.CompositeParamType-objects
    :param param: The parameter from which **otype** came from
    :param kwargs: Additionally parameters ('parent', 'widgetsource', 'com', 'label') needed for
        :class:`~clickqt.widgets.basewidget.MultiWidget`- /
        :class:`~clickqt.widgets.confirmationwidget.ConfirmationWidget`- widgets
    """

    widget_type = QLineEdit  #: The Qt-type of this widget.

    def __init__(self, otype: click.ParamType, param: click.Parameter, **kwargs):
        super().__init__(otype, param, **kwargs)

        assert isinstance(
            otype, click.Path
        ), f"'otype' must be of type '{click.Path}', but is '{type(otype)}'."

        #: File type is
        #   :attr:`~clickqt.widgets.textfield.PathField.FileType.File`
        # and/or
        #   :attr:`~clickqt.widgets.textfield.PathField.FileType.Directory`
        #: depending on **otype**\.file_okay and **otype**\.dir_okay.
        self.file_type: PathField.FileType
        if isinstance(otype, PathWithExtensions):
            # PathWithExtensions always validates file extensions and rejects
            # directories, so the GUI must only expose file selection.
            self.file_type = PathField.FileType.File
        else:
            self.file_type |= (
                PathField.FileType.File if otype.file_okay else self.file_type
            )
            self.file_type |= (
                PathField.FileType.Directory if otype.dir_okay else self.file_type
            )

        assert (
            self.file_type != PathField.FileType.Unknown
        ), f"Neither 'file_okay' nor 'dir_okay' in option '{self.widget_name}' is set"
