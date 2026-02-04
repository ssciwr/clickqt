# pylint: disable=cyclic-import
from __future__ import annotations

import inspect
from collections import defaultdict
import typing as t

import click

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThread


def raise_(ex: Exception):
    raise ex


def wait_process_Events(ms: int, x_times: int = 3):
    for _ in range(x_times):
        QApplication.processEvents()
        QThread.msleep(ms)


# Credits to https://stackoverflow.com/questions/15788725/how-to-determine-the-closest-common-ancestor-class
def clcoancl(*cls_list):
    mros = [list(inspect.getmro(cls)) for cls in cls_list]
    track = defaultdict(int)
    while mros:
        for mro in mros:
            cur = mro.pop(0)
            track[cur] += 1
            if track[cur] == len(cls_list):
                return cur
            if len(mro) == 0:
                mros.remove(mro)
    return None  # or raise, if that's more appropriate


class ClickAttrs:
    @staticmethod
    def unprocessed(**attrs_dict) -> dict:
        return {"type": click.types.UNPROCESSED, **attrs_dict}

    @staticmethod
    def messagebox(prompt: str, **attrs_dict) -> dict:
        return {
            "type": click.types.BOOL,
            "is_flag": True,
            "prompt": prompt,
            **attrs_dict,
        }

    @staticmethod
    def intfield(**attrs_dict) -> dict:
        return {"type": click.types.INT, **attrs_dict}

    @staticmethod
    def passwordfield(**attrs_dict) -> dict:
        return {"type": click.types.STRING, "hide_input": True, **attrs_dict}

    @staticmethod
    def realfield(**attrs_dict) -> dict:
        return {"type": click.types.FLOAT, **attrs_dict}

    @staticmethod
    def intrange(
        minval: "int|None" = None,
        maxval: "int|None" = None,
        min_open: bool = False,
        max_open: bool = False,
        clamp: bool = False,
        **attrs_dict,
    ) -> dict:
        return {
            "type": click.IntRange(
                min=minval,
                max=maxval,
                min_open=min_open,
                max_open=max_open,
                clamp=clamp,
            ),
            **attrs_dict,
        }

    @staticmethod
    def floatrange(
        minval: "float|None" = None,
        maxval: "float|None" = None,
        min_open: bool = False,
        max_open: bool = False,
        clamp: bool = False,
        **attrs_dict,
    ) -> dict:
        return {
            "type": click.FloatRange(
                min=minval,
                max=maxval,
                min_open=min_open,
                max_open=max_open,
                clamp=clamp,
            ),
            **attrs_dict,
        }

    @staticmethod
    def confirmation_widget(**attrs_dict) -> dict:
        return {"confirmation_prompt": True, **attrs_dict}

    @staticmethod
    def checkbox(**attrs_dict) -> dict:
        return {"type": click.types.BOOL, **attrs_dict}

    @staticmethod
    def combobox(
        choices: t.Sequence[str], case_sensitive: bool = True, **attrs_dict
    ) -> dict:
        return {
            "type": click.types.Choice(choices=choices, case_sensitive=case_sensitive),
            **attrs_dict,
        }

    @staticmethod
    def checkable_combobox(
        choices: t.Sequence[str], case_sensitive: bool = True, **attrs_dict
    ) -> dict:
        return {
            "type": click.types.Choice(choices=choices, case_sensitive=case_sensitive),
            "multiple": True,
            **attrs_dict,
        }

    @staticmethod
    def filefield(type_dict: dict = None, **attrs_dict) -> dict:
        type_dict = {} if type_dict is None else type_dict
        return {"type": click.types.File(**type_dict), **attrs_dict}

    @staticmethod
    def filepathfield(type_dict: dict = None, **attrs_dict) -> dict:
        type_dict = {} if type_dict is None else type_dict
        return {"type": click.types.Path(**type_dict), **attrs_dict}

    @staticmethod
    def datetime(formats: t.Optional[t.Sequence[str]] = None, **attrs_dict) -> dict:
        return {"type": click.types.DateTime(formats), **attrs_dict}

    @staticmethod
    def tuple_widget(
        types: t.Sequence[t.Union[t.Type[t.Any], click.ParamType]], **attrs_dict
    ) -> dict:
        return {"type": click.types.Tuple(types), **attrs_dict}

    @staticmethod
    def multi_value_widget(nargs: int, **attrs_dict) -> dict:
        assert nargs > 1
        assert attrs_dict.get("type") is None or not isinstance(
            attrs_dict["type"], tuple
        )
        return {"nargs": nargs, **attrs_dict}

    @staticmethod
    def nvalue_widget(**attrs_dict) -> dict:
        assert attrs_dict.get("type") is None or attrs_dict.get("type") is not bool
        return {"multiple": True, **attrs_dict}

    @staticmethod
    def uuid(**attrs_dict) -> dict:
        return {"type": click.types.UUID, **attrs_dict}

    @staticmethod
    def textfield(**attrs_dict) -> dict:
        return {"type": click.types.STRING, **attrs_dict}

    @staticmethod
    def countwidget(**attrs_dict) -> dict:
        return {"count": True, **attrs_dict}
