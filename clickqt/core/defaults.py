from __future__ import annotations

import typing as t

import click

_UNSET = getattr(click.core, "UNSET", object())


def is_unset(value: t.Any) -> bool:
    """Return True if *value* is Click's internal UNSET sentinel."""

    return value is _UNSET


def normalize_default(value: t.Any, fallback: t.Any = None) -> t.Any:
    """Map Click's "no default" markers to a concrete fallback value."""

    return fallback if value is None or is_unset(value) else value


def has_explicit_default(param: click.Parameter) -> bool:
    """
    Return True if a parameter has an explicit default value configured.

    Click uses an internal sentinel for "no default". We treat this the same as
    None for clickqt's UI initialization logic.
    """

    return not is_unset(param.default) and param.default is not None


def has_truthy_default(param: click.Parameter) -> bool:
    """
    Return True when a parameter has an explicit default that evaluates to True.
    """

    return has_explicit_default(param) and bool(param.default)
