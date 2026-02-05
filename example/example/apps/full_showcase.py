import re

import click
import clickqt
from click_option_group import optgroup


def validate_contrasts(ctx, param, value):
    for case, control in value:
        if case == control:
            raise click.BadParameter("Case and control names must be different.")
    return value


def validate_project_tag(ctx, param, value):
    if not re.fullmatch(r"[a-z0-9_]+", value):
        raise click.BadParameter(
            "Use lowercase letters, numbers, and underscores for project tags."
        )
    return value


@click.command(
    help=(
        "Configure an RNA-seq pipeline with practical defaults for QC, "
        "normalization, and output delivery."
    )
)
@optgroup.group("Input data")
@optgroup.option(
    "--reads-r1",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="Primary FASTQ file (read 1).",
)
@optgroup.option(
    "--reads-r2",
    type=click.Path(exists=True, dir_okay=False),
    help="Secondary FASTQ file (read 2) for paired-end runs.",
)
@optgroup.option(
    "--sample-metadata",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="Sample metadata sheet linking sample IDs to conditions.",
)
@optgroup.option(
    "--feature-annotation",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="Gene annotation file used for quantification.",
)
@optgroup.group("Pipeline design")
@optgroup.option(
    "--library-layout",
    type=click.Choice(["single-end", "paired-end"]),
    default="paired-end",
    show_default=True,
    help="Sequencing library structure.",
)
@optgroup.option(
    "--normalization",
    type=click.Choice(["tpm", "cpm", "deseq2"]),
    default="tpm",
    show_default=True,
    help="Normalization strategy for expression tables.",
)
@optgroup.option(
    "--contrast",
    type=(str, str),
    multiple=True,
    callback=validate_contrasts,
    help="Case/control condition pair. Repeat for multiple contrasts.",
)
@optgroup.option(
    "--expected-library-size",
    type=(int, int),
    default=(20_000_000, 60_000_000),
    show_default=True,
    help="Expected read depth window per sample.",
)
@optgroup.option(
    "--project-tag",
    type=str,
    default="pilot_batch_1",
    callback=validate_project_tag,
    confirmation_prompt=True,
    show_default=True,
    help="Lowercase label for naming run outputs.",
)
@optgroup.group("QC thresholds")
@optgroup.option(
    "--min-read-length",
    type=click.IntRange(35, 250),
    default=75,
    show_default=True,
    help="Discard reads shorter than this threshold.",
)
@optgroup.option(
    "--max-n-content",
    type=click.FloatRange(0.0, 0.25),
    default=0.05,
    show_default=True,
    help="Maximum ambiguous-base fraction allowed per read.",
)
@optgroup.option(
    "--min-mapping-rate",
    type=click.FloatRange(0.5, 1.0),
    default=0.80,
    show_default=True,
    help="Warn if mapping rate falls below this value.",
)
@click.option(
    "--trim-adapters/--no-trim-adapters",
    default=True,
    help="Enable adapter trimming.",
)
@click.option(
    "--deduplicate/--no-deduplicate",
    default=False,
    help="Remove duplicate alignments after mapping.",
)
@click.option(
    "--publish-report/--no-publish-report",
    default=True,
    help="Publish the HTML QC report after completion.",
)
@click.option(
    "--notify-channel",
    type=click.Choice(["email", "slack", "none"]),
    multiple=True,
    help="Notification channels for run completion.",
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False),
    default="rnaseq_results",
    show_default=True,
    help="Directory used to store pipeline outputs.",
)
@click.option(
    "--dry-run/--no-dry-run",
    default=False,
    help="Validate config only, without running the pipeline.",
)
def rnaseq_pipeline_configurator(
    reads_r1,
    reads_r2,
    sample_metadata,
    feature_annotation,
    library_layout,
    normalization,
    contrast,
    expected_library_size,
    project_tag,
    min_read_length,
    max_n_content,
    min_mapping_rate,
    trim_adapters,
    deduplicate,
    publish_report,
    notify_channel,
    output_dir,
    dry_run,
):
    if library_layout == "paired-end" and not reads_r2:
        raise click.BadParameter(
            "Paired-end layout requires --reads-r2.",
            param_hint="--reads-r2",
        )

    contrast_pairs = contrast if contrast else (("treated", "control"),)
    contrast_text = ", ".join(
        f"{case} vs {control}" for case, control in contrast_pairs
    )

    low_reads, high_reads = expected_library_size
    notifications = ", ".join(notify_channel) if notify_channel else "none"

    click.echo("=== RNA-seq Pipeline Configurator ===")
    click.echo(f"Project tag: {project_tag}")
    click.echo(f"Input R1: {reads_r1}")
    click.echo(f"Input R2: {reads_r2 or 'not used'}")
    click.echo(f"Sample metadata: {sample_metadata}")
    click.echo(f"Feature annotation: {feature_annotation}")
    click.echo(f"Library layout: {library_layout}")
    click.echo(f"Normalization mode: {normalization}")
    click.echo(f"Contrasts: {contrast_text}")
    click.echo(f"Expected library size: {low_reads:,} to {high_reads:,} reads/sample")
    click.echo(
        f"QC thresholds: min_read_length={min_read_length}, max_n={max_n_content:.2f}"
    )
    click.echo(f"Minimum mapping rate: {min_mapping_rate:.2f}")
    click.echo(f"Trim adapters: {'yes' if trim_adapters else 'no'}")
    click.echo(f"Deduplicate: {'yes' if deduplicate else 'no'}")
    click.echo(f"Publish report: {'yes' if publish_report else 'no'}")
    click.echo(f"Notify via: {notifications}")
    click.echo(f"Output directory: {output_dir}")
    click.echo(f"Dry run: {'enabled' if dry_run else 'disabled'}")
    click.echo("Configuration is complete and ready for execution.")


def rnaseq_gui():
    clickqt.qtgui_from_click(
        rnaseq_pipeline_configurator,
        application_name="ClickQt RNA-seq Pipeline Configurator",
    )()


if __name__ == "__main__":
    rnaseq_pipeline_configurator()
