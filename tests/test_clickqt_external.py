"""
Tests the external use of clickqt.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
import click
import clickqt.__main__ as clickqt_main
from clickqt.__main__ import (
    _iter_entry_points,
    clickqtfy,
    get_command_from_entrypoint,
    get_command_from_path,
    get_gui_specs_from_entrypoint,
    get_gui_specs_from_path,
)


def test_clickqt_external():
    """
    Try some good/bad imports and check if they are recognized as commands/garbage.
    """
    # test with endpoint
    with pytest.raises(ImportError):
        get_command_from_entrypoint("example")
    with pytest.raises(TypeError):
        get_command_from_entrypoint("example_gui")
    assert isinstance(get_command_from_entrypoint("example_cli"), click.Command)

    # test with file
    with pytest.raises(ImportError):
        get_command_from_path("example/example/afwizard.py", "ma")
    with pytest.raises(FileNotFoundError):
        get_command_from_path("example/example/--_--_-_.py", "main")
    with pytest.raises(TypeError):
        get_command_from_path(
            "example/example/afwizard.py", "validate_spatial_reference"
        )
    assert isinstance(
        get_command_from_path("example/example/afwizard.py", "main"), click.Command
    )


def test_clickqt_external_gui_specs():
    # test with gui endpoint
    with pytest.raises(ImportError):
        get_gui_specs_from_entrypoint("main")
    with pytest.raises(TypeError):
        get_gui_specs_from_entrypoint("example_cli")
    assert isinstance(get_gui_specs_from_entrypoint("example_gui"), dict)

    # test with file
    with pytest.raises(ImportError):
        get_gui_specs_from_path("example/example/afwizard.py", "example_cli")
    with pytest.raises(TypeError):
        get_gui_specs_from_path(
            "example/example/afwizard.py", "validate_spatial_reference"
        )
    with pytest.raises(FileNotFoundError):
        get_gui_specs_from_path("example/example/-.py", "gui")
    assert isinstance(
        get_gui_specs_from_path("example/example/__main__.py", "gui"), dict
    )


def test_iter_entry_points_supports_fallback_iterable_api(monkeypatch):
    entrypoints = [
        SimpleNamespace(name="ep1", value="pkg:one"),
        SimpleNamespace(name="ep2", value="pkg:two"),
    ]
    monkeypatch.setattr(clickqt_main.metadata, "entry_points", lambda: entrypoints)

    assert list(_iter_entry_points()) == entrypoints


def test_iter_entry_points_supports_groups_api(monkeypatch):
    class EntryPointsWithGroups:
        groups = ("console_scripts", "gui_scripts")

        def __init__(self):
            self.select_calls = []

        def select(self, *, group):
            self.select_calls.append(group)
            return [SimpleNamespace(name=f"{group}_ep", value=f"{group}:main")]

    entrypoints = EntryPointsWithGroups()
    monkeypatch.setattr(clickqt_main.metadata, "entry_points", lambda: entrypoints)

    resolved = list(_iter_entry_points())

    assert [ep.name for ep in resolved] == ["console_scripts_ep", "gui_scripts_ep"]
    assert entrypoints.select_calls == ["console_scripts", "gui_scripts"]


class DummyControl:
    def __init__(self):
        self.is_ep = None
        self.ep_or_path = None
        self.call_count = 0

    def set_is_ep(self, is_ep):
        self.is_ep = is_ep

    def set_ep_or_path(self, ep_or_path):
        self.ep_or_path = ep_or_path

    def __call__(self):
        self.call_count += 1
        return "ran"


def test_clickqtfy_uses_path_resolvers_for_file_inputs(monkeypatch, tmp_path):
    path = tmp_path / "cli.py"
    path.write_text("x = 1\n", encoding="utf-8")
    cmd = click.Command("cmd")
    custom_mapping = {"custom": "mapping"}
    control = DummyControl()
    captured = {}

    def fake_qtgui_from_click(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return control

    monkeypatch.setattr(clickqt_main, "qtgui_from_click", fake_qtgui_from_click)
    monkeypatch.setattr(
        clickqt_main,
        "get_command_from_path",
        lambda ep, fn: cmd if (ep, fn) == (str(path), "main") else None,
    )
    monkeypatch.setattr(
        clickqt_main,
        "get_gui_specs_from_path",
        lambda ep, gui: custom_mapping if (ep, gui) == (str(path), "gui") else None,
    )
    monkeypatch.setattr(
        clickqt_main,
        "get_command_from_entrypoint",
        lambda *_: (_ for _ in ()).throw(
            AssertionError("entrypoint resolver should not be used")
        ),
    )
    monkeypatch.setattr(
        clickqt_main,
        "get_gui_specs_from_entrypoint",
        lambda *_: (_ for _ in ()).throw(
            AssertionError("entrypoint gui resolver should not be used")
        ),
    )

    result = clickqtfy.callback(str(path), "main", "gui")

    assert result == "ran"
    assert control.call_count == 1
    assert control.is_ep is False
    assert control.ep_or_path == str(path)
    assert captured["command"] is cmd
    assert captured["kwargs"] == {
        "custom_mapping": custom_mapping,
        "application_name": f"{path} - main",
    }


def test_clickqtfy_uses_entrypoint_resolvers_for_installed_entrypoints(monkeypatch):
    cmd = click.Command("cmd")
    custom_mapping = {"custom": "mapping"}
    control = DummyControl()
    captured = {}

    def fake_qtgui_from_click(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return control

    monkeypatch.setattr(clickqt_main, "qtgui_from_click", fake_qtgui_from_click)
    monkeypatch.setattr(
        clickqt_main,
        "get_command_from_entrypoint",
        lambda ep: cmd if ep == "cli-ep" else None,
    )
    monkeypatch.setattr(
        clickqt_main,
        "get_gui_specs_from_entrypoint",
        lambda ep: custom_mapping if ep == "gui-ep" else None,
    )
    monkeypatch.setattr(
        clickqt_main,
        "get_command_from_path",
        lambda *_: (_ for _ in ()).throw(
            AssertionError("path resolver should not be used")
        ),
    )
    monkeypatch.setattr(
        clickqt_main,
        "get_gui_specs_from_path",
        lambda *_: (_ for _ in ()).throw(
            AssertionError("path gui resolver should not be used")
        ),
    )

    result = clickqtfy.callback("cli-ep", None, "gui-ep")

    assert result == "ran"
    assert control.call_count == 1
    assert control.is_ep is True
    assert control.ep_or_path == "cli-ep"
    assert captured["command"] is cmd
    assert captured["kwargs"] == {
        "custom_mapping": custom_mapping,
        "application_name": "cli-ep",
    }


def test_clickqtfy_without_custom_gui_uses_default_mapping(monkeypatch):
    cmd = click.Command("cmd")
    control = DummyControl()
    captured = {}

    def fake_qtgui_from_click(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return control

    monkeypatch.setattr(clickqt_main, "qtgui_from_click", fake_qtgui_from_click)
    monkeypatch.setattr(clickqt_main, "get_command_from_entrypoint", lambda _: cmd)

    result = clickqtfy.callback("cli-ep", None, None)

    assert result == "ran"
    assert control.call_count == 1
    assert control.is_ep is True
    assert control.ep_or_path == "cli-ep"
    assert captured["command"] is cmd
    assert captured["kwargs"] == {"application_name": "cli-ep"}


def test_get_command_from_entrypoint_raises_for_missing_exact_match(monkeypatch):
    monkeypatch.setattr(clickqt_main, "get_entrypoints_from_name", lambda _: [])

    with pytest.raises(ImportError, match="No entry point named 'missing' found."):
        get_command_from_entrypoint("missing")


def test_get_gui_specs_from_entrypoint_raises_for_missing_exact_match(monkeypatch):
    monkeypatch.setattr(clickqt_main, "get_entrypoints_from_name", lambda _: [])

    with pytest.raises(ImportError, match="No entry point named 'missing' found."):
        get_gui_specs_from_entrypoint("missing")
