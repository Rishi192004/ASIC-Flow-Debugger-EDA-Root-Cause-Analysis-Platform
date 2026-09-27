"""Unit tests for flowctl configuration schema and loader."""

import pytest
import yaml
from pathlib import Path
from pydantic import ValidationError

from flowctl.config.loader import ConfigError, load_config, resolve_sources
from flowctl.config.schema import FlowConfig, RTLConfig, ToolConfig


def test_valid_schema_model():
    """Test instantiating FlowConfig directly with valid data."""
    config_data = {
        "project": "alu_core",
        "rtl": {
            "sources": ["examples/rtl/*.sv"],
            "top": "alu_top",
        },
        "stages": ["lint", "sim", "synth"],
        "tools": {
            "lint": {"adapter": "verible"},
            "sim": {"adapter": "verilator", "testbench": "tb/tb_alu.sv"},
            "synth": {"adapter": "yosys", "target": "generic"},
        },
    }
    cfg = FlowConfig(**config_data)
    assert cfg.project == "alu_core"
    assert cfg.rtl.top == "alu_top"
    assert len(cfg.stages) == 3
    assert cfg.tools["lint"].adapter == "verible"
    assert cfg.tools["sim"].testbench == "tb/tb_alu.sv"
    assert cfg.tools["synth"].target == "generic"


def test_load_valid_yaml_file(tmp_path: Path):
    """Test loading a valid YAML configuration file."""
    yaml_content = """
project: test_proj
rtl:
  sources:
    - rtl/a.v
    - rtl/b.v
  top: a_top
stages:
  - lint
  - synth
tools:
  lint:
    adapter: verible
  synth:
    adapter: yosys
"""
    cfg_file = tmp_path / "flow.yaml"
    cfg_file.write_text(yaml_content, encoding="utf-8")

    cfg = load_config(cfg_file)
    assert cfg.project == "test_proj"
    assert cfg.rtl.sources == ["rtl/a.v", "rtl/b.v"]
    assert cfg.rtl.top == "a_top"
    assert cfg.stages == ["lint", "synth"]


def test_missing_project_field(tmp_path: Path):
    """Test error when 'project' field is missing."""
    yaml_content = """
rtl:
  sources: [rtl/top.v]
  top: top
stages: [lint]
tools:
  lint: {adapter: verible}
"""
    cfg_file = tmp_path / "missing_proj.yaml"
    cfg_file.write_text(yaml_content, encoding="utf-8")

    with pytest.raises(ConfigError) as exc_info:
        load_config(cfg_file)
    assert "project" in str(exc_info.value)


def test_missing_rtl_sources(tmp_path: Path):
    """Test error when 'rtl.sources' is missing or empty."""
    yaml_content = """
project: test_proj
rtl:
  top: top
stages: [lint]
tools:
  lint: {adapter: verible}
"""
    cfg_file = tmp_path / "missing_sources.yaml"
    cfg_file.write_text(yaml_content, encoding="utf-8")

    with pytest.raises(ConfigError) as exc_info:
        load_config(cfg_file)
    assert "sources" in str(exc_info.value)


def test_empty_rtl_sources(tmp_path: Path):
    """Test error when 'rtl.sources' is an empty list."""
    yaml_content = """
project: test_proj
rtl:
  sources: []
  top: top
stages: [lint]
tools:
  lint: {adapter: verible}
"""
    cfg_file = tmp_path / "empty_sources.yaml"
    cfg_file.write_text(yaml_content, encoding="utf-8")

    with pytest.raises(ConfigError) as exc_info:
        load_config(cfg_file)
    assert "sources" in str(exc_info.value)


def test_missing_rtl_top(tmp_path: Path):
    """Test error when 'rtl.top' module is missing."""
    yaml_content = """
project: test_proj
rtl:
  sources: [rtl/top.v]
stages: [lint]
tools:
  lint: {adapter: verible}
"""
    cfg_file = tmp_path / "missing_top.yaml"
    cfg_file.write_text(yaml_content, encoding="utf-8")

    with pytest.raises(ConfigError) as exc_info:
        load_config(cfg_file)
    assert "top" in str(exc_info.value)


def test_bad_tool_adapter_name(tmp_path: Path):
    """Test validation error on unsupported tool adapter."""
    yaml_content = """
project: test_proj
rtl:
  sources: [rtl/top.v]
  top: top
stages: [synth]
tools:
  synth:
    adapter: non_existent_tool_xyz
"""
    cfg_file = tmp_path / "bad_tool.yaml"
    cfg_file.write_text(yaml_content, encoding="utf-8")

    with pytest.raises(ConfigError) as exc_info:
        load_config(cfg_file)
    err_str = str(exc_info.value)
    assert "Unknown tool adapter 'non_existent_tool_xyz'" in err_str
    assert "Supported adapters are" in err_str


def test_stage_missing_tool_config(tmp_path: Path):
    """Test error when a configured stage does not have tool settings."""
    yaml_content = """
project: test_proj
rtl:
  sources: [rtl/top.v]
  top: top
stages:
  - lint
  - synth
tools:
  lint:
    adapter: verible
"""
    cfg_file = tmp_path / "missing_stage_tool.yaml"
    cfg_file.write_text(yaml_content, encoding="utf-8")

    with pytest.raises(ConfigError) as exc_info:
        load_config(cfg_file)
    assert "Missing tool configuration for stage(s): synth" in str(exc_info.value)


def test_invalid_yaml_syntax(tmp_path: Path):
    """Test error on broken YAML syntax."""
    bad_yaml = """
project: broken
rtl: [unclosed list
stages: lint
"""
    cfg_file = tmp_path / "syntax_error.yaml"
    cfg_file.write_text(bad_yaml, encoding="utf-8")

    with pytest.raises(ConfigError) as exc_info:
        load_config(cfg_file)
    assert "Invalid YAML syntax" in str(exc_info.value)


def test_nonexistent_config_file():
    """Test error when config file does not exist."""
    with pytest.raises(ConfigError) as exc_info:
        load_config("does_not_exist_file.yaml")
    assert "Configuration file not found" in str(exc_info.value)


def test_resolve_sources(tmp_path: Path):
    """Test glob expansion and source file resolution."""
    rtl_dir = tmp_path / "rtl"
    rtl_dir.mkdir()
    f1 = rtl_dir / "mod1.sv"
    f2 = rtl_dir / "mod2.sv"
    f1.write_text("module mod1; endmodule", encoding="utf-8")
    f2.write_text("module mod2; endmodule", encoding="utf-8")

    resolved, unresolved = resolve_sources(["rtl/*.sv", "rtl/missing.v"], tmp_path)
    assert len(resolved) == 2
    assert f1 in resolved
    assert f2 in resolved
    assert "rtl/missing.v" in unresolved
