#!/usr/bin/env python3
"""Command line interface for flowctl ASIC Flow Automation."""

import sys
from pathlib import Path
import click
from rich.console import Console
from rich.panel import Panel

from flowctl.config.loader import ConfigError, load_config, resolve_sources
from flowctl.engine.dag import ExecutionPlan


console = Console(safe_box=True)


@click.group()
@click.version_option(version="0.1.0", prog_name="flowctl")
def cli():
    """flowctl - ASIC Flow Automation and Verification CLI tool."""
    pass


@cli.command(name="validate")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=False, dir_okay=False, path_type=Path),
    default=Path("configs/flow.yaml"),
    show_default=True,
    help="Path to YAML flow configuration file.",
)
def validate_command(config: Path):
    """Validate a flow configuration file against the schema."""
    config_path = config.resolve()
    console.print(f"[bold cyan]Validating configuration:[/bold cyan] [yellow]{config_path}[/yellow]")

    try:
        flow_cfg = load_config(config_path)
    except ConfigError as err:
        console.print(f"\n[bold red][ERROR] Configuration Validation Failed[/bold red]")
        console.print(Panel(str(err), border_style="red", title="[bold red]Error Details[/bold red]"))
        sys.exit(1)
    except Exception as ex:
        console.print(f"\n[bold red][ERROR] Unexpected Error:[/bold red] {ex}")
        sys.exit(1)

    # Validate RTL sources presence
    base_dir = config_path.parent.parent if config_path.parent.name == "configs" else config_path.parent
    resolved, unresolved = resolve_sources(flow_cfg.rtl.sources, base_dir)

    console.print(f"\n[bold green][OK] Configuration syntax and schema are valid![/bold green]")
    console.print(f"  * [bold]Project:[/bold] {flow_cfg.project}")
    console.print(f"  * [bold]Top Module:[/bold] {flow_cfg.rtl.top}")
    console.print(f"  * [bold]Stages ({len(flow_cfg.stages)}):[/bold] {' -> '.join(flow_cfg.stages)}")
    console.print(f"  * [bold]Resolved Sources:[/bold] {len(resolved)} file(s) found")

    if unresolved:
        console.print(f"\n[bold yellow][WARN] Source File Warning:[/bold yellow]")
        for pat in unresolved:
            console.print(f"  * Pattern/File not found: [yellow]{pat}[/yellow]")
    else:
        console.print(f"  * [bold green]All source patterns matched existing files.[/bold green]")

    console.print()


@cli.command(name="run")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=False, dir_okay=False, path_type=Path),
    default=Path("configs/flow.yaml"),
    show_default=True,
    help="Path to YAML flow configuration file.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=True,
    help="Print the resolved stage execution plan without running stages (default).",
)
def run_command(config: Path, dry_run: bool):
    """Parse configuration and execute ASIC pipeline stages (dry-run by default)."""
    config_path = config.resolve()

    try:
        flow_cfg = load_config(config_path)
    except ConfigError as err:
        console.print(f"\n[bold red][ERROR] Flow Failed to Initialize[/bold red]")
        console.print(Panel(str(err), border_style="red", title="[bold red]Config Error[/bold red]"))
        sys.exit(1)
    except Exception as ex:
        console.print(f"\n[bold red][ERROR] Unexpected Error:[/bold red] {ex}")
        sys.exit(1)

    plan = ExecutionPlan.from_config(flow_cfg, config_path)
    plan.display(console)


def main():
    """Main CLI entry point."""
    cli()


if __name__ == "__main__":
    main()
