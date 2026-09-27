#!/usr/bin/env python3
"""Command line interface for asic-flow tooling."""
import click

@click.group()
def cli():
    """flowctl - ASIC Flow Automation CLI"""
    pass

@cli.command()
@click.option("--config", "-c", default="configs/flow.yaml", help="Path to flow configuration file")
def run(config):
    """Run the ASIC flow pipeline."""
    click.echo(f"Executing ASIC flow from {config}...")

def main():
    cli()

if __name__ == "__main__":
    main()
