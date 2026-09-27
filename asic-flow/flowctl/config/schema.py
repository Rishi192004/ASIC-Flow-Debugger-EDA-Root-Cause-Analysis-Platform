"""Flow YAML schema definitions using Pydantic.

Defines schemas for project configuration, RTL sources, stages, and tool adapters.
"""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class SupportedAdapter(str, Enum):
    """Supported tool adapters."""
    VERIBLE = "verible"
    VERILATOR = "verilator"
    YOSYS = "yosys"
    REPORT = "report"
    CUSTOM = "custom"


class RTLConfig(BaseModel):
    """Configuration for RTL sources and top module."""
    sources: List[str] = Field(
        ...,
        min_length=1,
        description="List of RTL source files or glob patterns (e.g. ['examples/rtl/*.sv'])"
    )
    top: str = Field(
        ...,
        min_length=1,
        description="Top-level module name for synthesis and simulation"
    )
    include_dirs: List[str] = Field(
        default_factory=list,
        description="Optional list of include directories"
    )

    @field_validator("sources")
    @classmethod
    def validate_sources_non_empty(cls, v: List[str]) -> List[str]:
        if not v or any(not s.strip() for s in v):
            raise ValueError("RTL sources list must contain at least one non-empty path pattern.")
        return [s.strip() for s in v]

    @field_validator("top")
    @classmethod
    def validate_top_identifier(cls, v: str) -> str:
        val = v.strip()
        if not val:
            raise ValueError("Top-level module name cannot be empty.")
        return val


class ToolConfig(BaseModel):
    """Configuration for a stage tool adapter."""
    adapter: str = Field(
        ...,
        description="Name of the tool adapter (e.g. verible, verilator, yosys, report, custom)"
    )
    testbench: Optional[str] = Field(
        None,
        description="Path to testbench file for simulation stages"
    )
    target: Optional[str] = Field(
        None,
        description="Target synthesis technology or platform (e.g. generic, sky130, ice40)"
    )
    flags: List[str] = Field(
        default_factory=list,
        description="Additional CLI flags to pass to the tool"
    )
    extra_args: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional tool-specific configuration parameters"
    )
    output_dir: Optional[str] = Field(
        None,
        description="Optional custom stage output directory"
    )

    @field_validator("adapter")
    @classmethod
    def validate_adapter_name(cls, v: str) -> str:
        name = v.strip().lower()
        valid_adapters = [a.value for a in SupportedAdapter]
        if name not in valid_adapters:
            raise ValueError(
                f"Unknown tool adapter '{v}'. Supported adapters are: {', '.join(valid_adapters)}"
            )
        return name


class FlowConfig(BaseModel):
    """Root configuration schema for an ASIC flow pipeline."""
    project: str = Field(
        ...,
        min_length=1,
        description="Project name identifier"
    )
    rtl: RTLConfig = Field(
        ...,
        description="RTL source and top-level module configuration"
    )
    stages: List[str] = Field(
        ...,
        min_length=1,
        description="Ordered list of flow stages to execute"
    )
    tools: Dict[str, ToolConfig] = Field(
        default_factory=dict,
        description="Tool adapter configuration mapping for each stage"
    )

    @field_validator("project")
    @classmethod
    def validate_project_name(cls, v: str) -> str:
        val = v.strip()
        if not val:
            raise ValueError("Project name cannot be empty.")
        return val

    @field_validator("stages")
    @classmethod
    def validate_stages(cls, v: List[str]) -> List[str]:
        cleaned = [s.strip() for s in v if s.strip()]
        if not cleaned:
            raise ValueError("Flow must specify at least one stage in 'stages'.")
        return cleaned

    @model_validator(mode="after")
    def validate_stages_and_tools(self) -> "FlowConfig":
        """Ensure all specified stages have a corresponding tool configuration."""
        missing_tools = []
        for stage in self.stages:
            if stage not in self.tools:
                # Built-in fallback for 'report' stage if omitted
                if stage == "report":
                    self.tools["report"] = ToolConfig(adapter="report")
                else:
                    missing_tools.append(stage)

        if missing_tools:
            available = list(self.tools.keys())
            raise ValueError(
                f"Missing tool configuration for stage(s): {', '.join(missing_tools)}. "
                f"Configured tools: {', '.join(available) if available else 'None'}. "
                f"Please add a tool mapping under 'tools.<stage_name>'."
            )

        return self
