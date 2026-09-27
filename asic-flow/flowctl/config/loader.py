"""YAML Configuration loader and path resolver for flowctl."""

import glob
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union
import yaml
from pydantic import ValidationError

from flowctl.config.schema import FlowConfig


class ConfigError(Exception):
    """Raised when configuration loading or validation fails."""
    pass


def load_yaml(path: Union[str, Path]) -> Dict[str, Any]:
    """Load and parse a YAML file."""
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigError(f"Configuration file not found: {config_path}")
    if not config_path.is_file():
        raise ConfigError(f"Config path is not a valid file: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML syntax in '{config_path}':\n{e}") from e

    if data is None:
        raise ConfigError(f"Configuration file '{config_path}' is empty.")
    if not isinstance(data, dict):
        raise ConfigError(
            f"Invalid configuration format in '{config_path}'. Expected a YAML dictionary/mapping at the top level."
        )

    return data


def format_validation_error(err: ValidationError) -> str:
    """Format Pydantic ValidationError into a user-friendly error summary."""
    error_lines = []
    for error in err.errors():
        loc = " -> ".join(str(item) for item in error.get("loc", []))
        msg = error.get("msg", "Invalid value")
        # Strip generic Pydantic prefixes if present
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, "):]
        error_lines.append(f"  • [{loc}]: {msg}")
    return "\n".join(error_lines)


def load_config(path: Union[str, Path]) -> FlowConfig:
    """Load, validate, and return a FlowConfig object from a YAML file."""
    raw_data = load_yaml(path)
    try:
        return FlowConfig(**raw_data)
    except ValidationError as e:
        formatted = format_validation_error(e)
        raise ConfigError(f"Configuration validation failed for '{path}':\n{formatted}") from e


def resolve_sources(patterns: List[str], base_dir: Path) -> Tuple[List[Path], List[str]]:
    """Resolve RTL source patterns/globs relative to base_dir.

    Returns:
        Tuple of (resolved_existing_paths, unresolved_patterns)
    """
    resolved_paths: List[Path] = []
    unresolved: List[str] = []

    for pattern in patterns:
        clean_pat = pattern.strip()
        # Check if it's an absolute path or relative to base_dir
        pat_path = Path(clean_pat)
        if pat_path.is_absolute():
            matches = [Path(p) for p in glob.glob(clean_pat, recursive=True)]
        else:
            search_pattern = str(base_dir / clean_pat)
            matches = [Path(p) for p in glob.glob(search_pattern, recursive=True)]

        if matches:
            resolved_paths.extend(matches)
        else:
            # Check if literal file exists directly
            candidate = (base_dir / clean_pat) if not pat_path.is_absolute() else pat_path
            if candidate.exists():
                resolved_paths.append(candidate)
            else:
                unresolved.append(clean_pat)

    # Deduplicate while preserving order
    unique_paths: List[Path] = []
    for p in resolved_paths:
        if p not in unique_paths:
            unique_paths.append(p)

    return unique_paths, unresolved
