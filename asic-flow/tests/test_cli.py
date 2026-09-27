"""Unit tests for flowctl CLI commands."""

from pathlib import Path
from click.testing import CliRunner
from flowctl.cli import cli


def test_cli_help():
    """Test CLI base help."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "flowctl" in result.output
    assert "validate" in result.output
    assert "run" in result.output


def test_cli_validate_success():
    """Test validating existing configs/flow.yaml."""
    runner = CliRunner()
    config_path = Path("configs/flow.yaml")
    result = runner.invoke(cli, ["validate", "--config", str(config_path)])
    assert result.exit_code == 0
    assert "syntax and schema are valid" in result.output
    assert "my_design" in result.output
    assert "alu_top" in result.output


def test_cli_validate_failure(tmp_path: Path):
    """Test validating an invalid configuration file."""
    bad_cfg = tmp_path / "bad.yaml"
    bad_cfg.write_text("invalid_key: true", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["validate", "--config", str(bad_cfg)])
    assert result.exit_code == 1
    assert "Configuration Validation Failed" in result.output


def test_cli_run_dry_run():
    """Test running flowctl in dry-run mode."""
    runner = CliRunner()
    config_path = Path("configs/flow.yaml")
    result = runner.invoke(cli, ["run", "--config", str(config_path)])
    assert result.exit_code == 0
    assert "Execution Plan (Dry Run)" in result.output
    assert "my_design" in result.output
    assert "alu_top" in result.output
    assert "lint" in result.output
    assert "sim" in result.output
    assert "synth" in result.output
    assert "verible" in result.output
    assert "verilator" in result.output
    assert "yosys" in result.output
    assert "Dry run plan successfully generated" in result.output
