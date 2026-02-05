import click
import clickqt


@click.command(
    help=(
        "Start a small lab intake session and confirm the workstation is ready "
        "for incoming samples."
    )
)
@click.option(
    "--researcher",
    type=str,
    default="Dr. Rivera",
    show_default=True,
    help="Name shown on the intake dashboard.",
)
@click.option(
    "--organism",
    type=click.Choice(["human", "mouse", "yeast"]),
    default="human",
    show_default=True,
    help="Primary organism for this intake session.",
)
@click.option(
    "--replicate-count",
    type=click.IntRange(1, 12),
    default=3,
    show_default=True,
    help="Planned biological replicate count for the next run.",
)
@click.option(
    "--notify/--no-notify",
    default=True,
    help="Enable lab dashboard notifications for this run.",
)
def lab_greeter(researcher, organism, replicate_count, notify):
    status = "notifications enabled" if notify else "notifications muted"
    click.echo("=== ClickQt Bio Lab Greeter ===")
    click.echo(f"Researcher: {researcher}")
    click.echo(f"Organism queue: {organism}")
    click.echo(
        f"{researcher} is ready for sample intake with "
        f"{replicate_count} replicates ({status})."
    )


def hello_gui():
    clickqt.qtgui_from_click(
        lab_greeter,
        application_name="ClickQt Bio Lab Greeter",
    )()


if __name__ == "__main__":
    lab_greeter()
