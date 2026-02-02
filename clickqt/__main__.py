"""
Contains the entry point for clickqt, called clickqtfy, allowing external use.
"""
from __future__ import annotations

import sys
from importlib import util, metadata

import click
from clickqt.core.control import Control
from clickqt.core.core import qtgui_from_click


@click.command("clickqtfy")
@click.argument("entrypoint")
@click.argument("funcname", default=None, required=False)
@click.option(
    "--custom-gui",
    type=str,
    required=False,
    help="Use this to insert your own GUI entry point,"
    "either as a standalone entry point or as a variable to a Control() object.",
)
def clickqtfy(entrypoint, funcname, custom_gui):
    """
    Generate a GUI for an entry point or a file + click.command combinaiton.

    ENTRYPOINT: Name of an installed entry point or a file path.\n
    FUNCNAME: Name of the click.command inside the file at ENTRYPOINT.\n
    If FUNCNAME is provided, ENTRYPOINT is interpreted as a file. Otherwise, as an entry point.
    """
    appname = entrypoint + (f" - {funcname}" if funcname else "")
    gui_specs = None
    command = None
    control = None
    if custom_gui:
        if funcname:
            gui_specs = get_gui_specs_from_path(entrypoint, custom_gui)
        else:
            gui_specs = get_gui_specs_from_entrypoint(custom_gui)

    if funcname:
        click.types.File().convert(entrypoint, None, None)  # check if its real file
        command = get_command_from_path(entrypoint, funcname)
    else:
        command = get_command_from_entrypoint(entrypoint)

    if gui_specs:
        control = qtgui_from_click(
            command, custom_mapping=gui_specs, application_name=appname
        )
    else:
        control = qtgui_from_click(command, application_name=appname)
    control.set_is_ep(funcname is None)
    control.set_ep_or_path(entrypoint)
    return control()


def get_command_from_entrypoint(epname: str) -> click.Command:
    """
    Returns the click.Command specified by `epname`.
    If `epname` is not a click.Command, raises `ImportError`.
    """
    eps = get_entrypoints_from_name(epname)
    if len(eps) == 0:
        raise ImportError(f"No entry point named '{epname}' found.")
    if len(eps) > 1 or (len(eps) == 1 and eps[0].name != epname):
        concateps = "\n".join([ep.name for ep in eps])
        raise ImportError(
            f"No entry point named '{epname}' found. Similar ones:\n{concateps}"
        )
    return validate_entrypoint(eps[0].load())


def get_entrypoints_from_name(epname: str) -> list[metadata.EntryPoint]:
    """
    Returns the entrypoints that include `epname` in their name.
    """
    eps = metadata.entry_points()
    return list(eps.select(name=epname))
    # TODO This is also had some logic to determine and recommend "similar"
    #      commands, but it broke and I had to quick-fix it. Could be readded.


def get_gui_specs_from_entrypoint(epname: str):
    """
    Returns the click.Command specified by `epname`.
    If `epname` is not a click.Command, raises `ImportError`.
    """
    eps = get_entrypoints_from_name(epname)
    if len(eps) == 0:
        raise ImportError(f"No entry point named '{epname}' found.")
    if len(eps) > 1 or (len(eps) == 1 and eps[0].name != epname):
        concateps = "\n".join([ep.name for ep in eps])
        raise ImportError(
            f"No entry point named '{epname}' found. Similar ones:\n{concateps}"
        )
    return validate_gui_ep(eps[0].load())


def get_command_from_path(eppath: str, epname: str) -> click.Command:
    """
    Returns the entrypoint given by the file path and the function name,
    or raises `ImportError` if the endpoint is not a `click.Command`.
    """
    modulename = "clickqtfy.imported_module"
    spec = util.spec_from_file_location(modulename, eppath)
    module = util.module_from_spec(spec)
    sys.modules[modulename] = module
    spec.loader.exec_module(module)
    entrypoint = getattr(module, epname, None)
    if entrypoint is None:
        raise ImportError(
            f"Module '{spec.origin}' does not contain the entry point '{epname}'."
        )
    return validate_entrypoint(entrypoint)


def get_gui_specs_from_path(eppath: str, epname: str):
    """
    Returns the entpoint pointing to a Control() object, or raises `ImportError` if it doesn't.
    """
    modulename = "clickqtfy.imported_module"
    spec = util.spec_from_file_location(modulename, eppath)
    module = util.module_from_spec(spec)
    sys.modules[modulename] = module
    spec.loader.exec_module(module)
    entrypoint = getattr(module, epname, None)
    if entrypoint is None:
        raise ImportError(
            f"Module '{spec.origin}' does not contain the entry point '{epname}'."
        )
    return validate_gui_ep(entrypoint)


def validate_entrypoint(entrypoint):
    """
    Raise a `TypeError` if a provided function is not a `click.Command`.
    """
    if not isinstance(entrypoint, click.Command):
        raise TypeError(f"Entry point '{entrypoint}' is not a 'click.Command'.")
    return entrypoint


def validate_gui_ep(entrypoint):
    if not isinstance(entrypoint, Control):
        raise TypeError(f"Entry point '{entrypoint}' is not a Control")
    return entrypoint.custom_mapping
