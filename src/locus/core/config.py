"""Configuration management for locus modular export."""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class GroupingRule:
    """Defines how files matching a pattern should be grouped."""

    pattern: str  # Glob pattern like "src/*/features/*"
    group_by: str  # "module", "file", or "directory"
    depth: Optional[int] = None  # How many path levels to include in grouping
    separate: bool = False  # If True, each file gets its own output file


@dataclass
class ModularExportConfig:
    """Configuration for modular file export."""

    enabled: bool = True
    max_lines_per_file: int = 5000
    grouping_rules: List[GroupingRule] = field(default_factory=list)
    default_depth: int = 2


@dataclass
class LocusConfig:
    """Main locus configuration."""

    modular_export: ModularExportConfig = field(default_factory=ModularExportConfig)


DEFAULT_CONFIG = {
    "modular_export": {
        "enabled": True,
        "max_lines_per_file": 5000,
        "grouping_rules": [
            # lib/ and services/ - split by second level (depth 2)
            {
                "pattern": "lib/**",
                "group_by": "directory",
                "depth": 2,
            },
            {
                "pattern": "services/**",
                "group_by": "directory",
                "depth": 2,
            },
            # src/*/features/* - keep existing pattern for compatibility
            {
                "pattern": "src/*/features/*",
                "group_by": "module",
                "depth": 3,
            },
            # Main entry points - separate files
            {
                "pattern": "src/*/run.py",
                "group_by": "file",
                "separate": True,
            },
            {
                "pattern": "src/*/main.py",
                "group_by": "file",
                "separate": True,
            },
        ],
        "default_depth": 1,  # Changed from 2 to 1 for other root folders
    }
}


def load_config(project_path: str) -> LocusConfig:
    """Load locus configuration from .locus/settings.json.

    Args:
        project_path: Root path of the project

    Returns:
        LocusConfig object with loaded or default settings
    """
    config_path = Path(project_path) / ".locus" / "settings.json"

    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            logger.info(f"Loaded configuration from {config_path}")
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(
                f"Error loading config from {config_path}: {e}. Using defaults."
            )
            config_data = DEFAULT_CONFIG
    else:
        logger.debug(f"No config found at {config_path}. Using defaults.")
        config_data = DEFAULT_CONFIG

    return _parse_config(config_data)


def save_default_config(project_path: str) -> Path:
    """Save default configuration to .locus/settings.json.

    Args:
        project_path: Root path of the project

    Returns:
        Path to the saved config file
    """
    config_dir = Path(project_path) / ".locus"
    config_path = config_dir / "settings.json"

    os.makedirs(config_dir, exist_ok=True)

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved default configuration to {config_path}")
    return config_path


def _parse_config(config_data: Dict[str, Any]) -> LocusConfig:
    """Parse configuration dictionary into LocusConfig object.

    Args:
        config_data: Raw configuration dictionary

    Returns:
        Parsed LocusConfig object
    """
    modular_export_data = config_data.get("modular_export", {})

    rules = []
    for rule_data in modular_export_data.get("grouping_rules", []):
        rules.append(
            GroupingRule(
                pattern=rule_data["pattern"],
                group_by=rule_data["group_by"],
                depth=rule_data.get("depth"),
                separate=rule_data.get("separate", False),
            )
        )

    modular_export = ModularExportConfig(
        enabled=modular_export_data.get("enabled", True),
        max_lines_per_file=modular_export_data.get("max_lines_per_file", 5000),
        grouping_rules=rules,
        default_depth=modular_export_data.get("default_depth", 2),
    )

    return LocusConfig(modular_export=modular_export)
