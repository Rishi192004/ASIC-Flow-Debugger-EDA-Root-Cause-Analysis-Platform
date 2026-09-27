"""Flow orchestration plan and stage resolver."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from flowctl.config.loader import resolve_sources
from flowctl.config.schema import FlowConfig, ToolConfig


@dataclass
class StagePlan:
    """Resolved execution plan for a single stage in the flow."""
    order: int
    name: str
    adapter: str
    top_module: str
    resolved_sources: List[Path] = field(default_factory=list)
    unresolved_sources: List[str] = field(default_factory=list)
    testbench: Optional[str] = None
    target: Optional[str] = None
    flags: List[str] = field(default_factory=list)
    extra_args: Dict[str, Any] = field(default_factory=dict)
    output_dir: Optional[str] = None

    @property
    def input_summary(self) -> str:
        """Provide a readable summary of inputs for the stage."""
        inputs = []
        if self.resolved_sources:
            inputs.append(f"{len(self.resolved_sources)} RTL source(s)")
        if self.testbench:
            inputs.append(f"TB: {self.testbench}")
        if self.unresolved_sources:
            inputs.append(f"(! missing: {', '.join(self.unresolved_sources)})")
        return ", ".join(inputs) if inputs else "N/A"


@dataclass
class ExecutionPlan:
    """Complete resolved execution plan for a flow pipeline."""
    project: str
    top_module: str
    config_path: Path
    base_dir: Path
    stages: List[StagePlan] = field(default_factory=list)
    resolved_sources: List[Path] = field(default_factory=list)
    unresolved_sources: List[str] = field(default_factory=list)

    @classmethod
    def from_config(cls, config: FlowConfig, config_path: Path) -> "ExecutionPlan":
        """Resolve and build an ExecutionPlan from a FlowConfig and its location."""
        base_dir = config_path.parent.resolve() if config_path else Path.cwd()
        # If the config file is in configs/ directory, project root is its parent if sources are relative to root
        project_root = base_dir.parent if base_dir.name == "configs" else base_dir

        # Try resolving relative to project_root first, then base_dir
        resolved, unresolved = resolve_sources(config.rtl.sources, project_root)
        if unresolved and project_root != base_dir:
            resolved2, unresolved2 = resolve_sources(config.rtl.sources, base_dir)
            if len(resolved2) > len(resolved):
                resolved, unresolved = resolved2, unresolved2

        stage_plans: List[StagePlan] = []
        for idx, stage_name in enumerate(config.stages, start=1):
            tool_cfg: ToolConfig = config.tools.get(stage_name, ToolConfig(adapter="custom"))
            
            # Resolve testbench if present
            tb_path = tool_cfg.testbench
            
            stage_plan = StagePlan(
                order=idx,
                name=stage_name,
                adapter=tool_cfg.adapter,
                top_module=config.rtl.top,
                resolved_sources=resolved,
                unresolved_sources=unresolved,
                testbench=tb_path,
                target=tool_cfg.target,
                flags=tool_cfg.flags,
                extra_args=tool_cfg.extra_args,
                output_dir=tool_cfg.output_dir or f"build/{config.project}/{stage_name}",
            )
            stage_plans.append(stage_plan)

        return cls(
            project=config.project,
            top_module=config.rtl.top,
            config_path=config_path,
            base_dir=project_root,
            stages=stage_plans,
            resolved_sources=resolved,
            unresolved_sources=unresolved,
        )

    def display(self, console: Optional[Console] = None) -> None:
        """Print rich, formatted execution plan."""
        if console is None:
            console = Console()

        title = f"[bold cyan]Execution Plan (Dry Run)[/bold cyan] | Project: [bold green]{self.project}[/bold green] (Top: [bold yellow]{self.top_module}[/bold yellow])"
        
        table = Table(show_header=True, header_style="bold magenta", border_style="dim", box=None)
        table.add_column("#", style="dim", width=4, justify="right")
        table.add_column("Stage", style="bold", min_width=12)
        table.add_column("Tool / Adapter", style="cyan", min_width=15)
        table.add_column("Target / Options", style="green", min_width=18)
        table.add_column("Inputs & Sources", min_width=30)
        table.add_column("Output Dir", style="dim", min_width=25)

        for s in self.stages:
            target_opts = []
            if s.target:
                target_opts.append(f"target: {s.target}")
            if s.flags:
                target_opts.append(f"flags: {' '.join(s.flags)}")
            target_str = ", ".join(target_opts) if target_opts else "-"

            table.add_row(
                str(s.order),
                s.name,
                s.adapter,
                target_str,
                s.input_summary,
                s.output_dir or "-",
            )

        console.print()
        console.print(Panel(table, title=title, subtitle=f"[dim]Config: {self.config_path}[/dim]"))

        if self.resolved_sources:
            console.print(f"\n[bold]Resolved RTL Files ({len(self.resolved_sources)}):[/bold]")
            for src in self.resolved_sources:
                try:
                    rel = src.relative_to(Path.cwd())
                    console.print(f"  * {rel}")
                except ValueError:
                    console.print(f"  * {src}")

        if self.unresolved_sources:
            console.print(f"\n[bold yellow][WARN] Unresolved Pattern(s) / Missing Files:[/bold yellow]")
            for unres in self.unresolved_sources:
                console.print(f"  * [yellow]{unres}[/yellow]")

        console.print("\n[bold green][OK][/bold green] [dim]Dry run plan successfully generated. No actions were executed.[/dim]\n")
