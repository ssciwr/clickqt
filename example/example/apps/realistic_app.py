import math

import click
import clickqt


def validate_cycle_for_primer(ctx, param, value):
    primer_set = ctx.params.get("primer_set")
    if primer_set == "16s_v4" and value > 35:
        raise click.BadParameter("16s_v4 amplicons usually require 35 cycles or fewer.")
    if primer_set == "its2" and value < 25:
        raise click.BadParameter("ITS2 amplicons usually need at least 25 cycles.")
    return value


def count_samples(sample_sheet):
    with open(sample_sheet, encoding="utf-8") as handle:
        rows = [line.strip() for line in handle if line.strip()]

    if not rows:
        raise click.ClickException(
            "Sample sheet is empty; add at least one sample row."
        )

    header = rows[0].lower()
    if "sample" in header or "id" in header:
        return max(len(rows) - 1, 0)
    return len(rows)


@click.command(
    help=(
        "Plan a PCR plate from a sample sheet, primer chemistry, and control "
        "targets used in routine assay setup."
    )
)
@click.option(
    "--sample-sheet",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="CSV/TSV file with one sample per row.",
)
@click.option(
    "--primer-set",
    type=click.Choice(["16s_v4", "its2", "custom"]),
    required=True,
    help="Amplicon primer panel used for this plate.",
)
@click.option(
    "--cycle-count",
    type=click.IntRange(15, 45),
    default=30,
    show_default=True,
    callback=validate_cycle_for_primer,
    help="PCR cycle count used for amplification.",
)
@click.option(
    "--anneal-c",
    type=click.FloatRange(45.0, 72.0, clamp=True),
    default=60.0,
    show_default=True,
    help="Annealing temperature in degrees Celsius.",
)
@click.option(
    "--control-gene",
    type=click.Choice(["GAPDH", "ACTB", "RPLP0"]),
    multiple=True,
    help="Optional control genes to include on plate.",
)
@click.option(
    "--plate-shape",
    type=(int, int),
    default=(8, 12),
    show_default=True,
    help="Plate dimensions as rows and columns.",
)
def pcr_plate_planner(
    sample_sheet, primer_set, cycle_count, anneal_c, control_gene, plate_shape
):
    sample_count = count_samples(sample_sheet)
    if sample_count == 0:
        raise click.ClickException("No sample rows detected in sample sheet.")

    control_targets = control_gene if control_gene else ("none",)
    rows, cols = plate_shape
    total_wells = rows * cols
    assay_count = sample_count + len(control_gene)
    plates_needed = max(1, math.ceil(assay_count / total_wells))
    unused_wells = plates_needed * total_wells - assay_count

    click.echo("=== PCR Plate Planner ===")
    click.echo(f"Sample sheet: {sample_sheet}")
    click.echo(f"Primer set: {primer_set}")
    click.echo(f"Cycle count: {cycle_count}")
    click.echo(f"Annealing temperature (C): {anneal_c:.1f}")
    click.echo(f"Control genes: {', '.join(control_targets)}")
    click.echo(f"Sample rows detected: {sample_count}")
    click.echo(f"Assays planned: {assay_count}")
    click.echo(f"Plate format: {rows}x{cols} ({total_wells} wells)")
    click.echo(f"Estimated plates needed: {plates_needed}")
    click.echo(f"Unused wells after layout: {unused_wells}")


def pcr_gui():
    clickqt.qtgui_from_click(
        pcr_plate_planner,
        application_name="ClickQt PCR Plate Planner",
        invocation_command="example_bio_pcr_cli",
    )()


if __name__ == "__main__":
    pcr_plate_planner()
