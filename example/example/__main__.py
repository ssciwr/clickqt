import os
import sys

if "QT_QPA_PLATFORM" not in os.environ:
    executable_name = os.path.basename(sys.argv[0]).lower()
    if "gui" not in executable_name:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"

import click
import clickqt

from example.apps.full_showcase import rnaseq_pipeline_configurator
from example.apps.hello_world import lab_greeter
from example.apps.realistic_app import pcr_plate_planner


@click.group(
    help=(
        "Biology-themed ClickQt examples. "
        "Launch one of the lab-ready commands below."
    )
)
def bio_suite():
    """Launcher for all biology example apps."""


bio_suite.add_command(lab_greeter)
bio_suite.add_command(pcr_plate_planner)
bio_suite.add_command(rnaseq_pipeline_configurator)


def suite_gui():
    gui()


# Backward-compatible aliases for existing docs and installs.
example_cli = bio_suite
utilgroup = bio_suite
gui = clickqt.qtgui_from_click(
    bio_suite,
    custom_mapping={},
    application_name="ClickQt Biology Example Suite",
    invocation_command="example_cli",
)
example_gui = gui


if __name__ == "__main__":
    bio_suite()
