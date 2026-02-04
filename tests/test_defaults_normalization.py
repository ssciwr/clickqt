from __future__ import annotations

import click

from clickqt.core.defaults import (
    has_explicit_default,
    has_truthy_default,
    is_unset,
    normalize_default,
)
from clickqt.widgets.basewidget import BaseWidget


def test_normalize_default_maps_unset_to_fallback():
    assert is_unset(click.core.UNSET)
    assert normalize_default(click.core.UNSET, "fallback") == "fallback"


def test_get_param_default_maps_unset_to_alternative():
    param = click.Option(["--value"])
    assert BaseWidget.get_param_default(param, "x") == "x"


def test_has_explicit_default_matches_click_semantics():
    assert not has_explicit_default(click.Option(["--unset"]))
    assert not has_explicit_default(click.Option(["--none"], default=None))
    assert has_explicit_default(click.Option(["--set"], default=0))


def test_has_truthy_default_matches_click_semantics():
    assert not has_truthy_default(click.Option(["--unset"]))
    assert not has_truthy_default(click.Option(["--none"], default=None))
    assert not has_truthy_default(click.Option(["--zero"], default=0))
    assert has_truthy_default(click.Option(["--one"], default=1))
