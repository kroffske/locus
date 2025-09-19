import logging
import os
from pathlib import Path
from typing import Set, Tuple

logger = logging.getLogger(__name__)

# Default templates for config files
DEFAULT_LOCUSALLOW = """# File patterns to include in analysis
# One pattern per line, supports glob patterns
# Lines starting with # are comments

**/*.py
**/*.js
**/*.ts
**/*.jsx
**/*.tsx
**/*.java
**/*.c
**/*.cpp
**/*.h
**/*.hpp
**/*.cs
**/*.go
**/*.rs
**/*.rb
**/*.php
**/*.swift
**/*.kt
**/*.scala
**/*.r
**/*.m
**/*.mm
**/*.sh
**/*.bash
**/*.zsh
**/*.fish
**/*.ps1
**/*.bat
**/*.cmd
**/*.yml
**/*.yaml
**/*.json
**/*.xml
**/*.toml
**/*.ini
**/*.cfg
**/*.conf
**/*.config
**/*.md
**/*.rst
**/*.txt
**/README*
**/LICENSE*
**/Dockerfile
**/docker-compose.yml
**/Makefile
**/.env.example
"""

DEFAULT_LOCUSIGNORE = """# File patterns to exclude from analysis
# One pattern per line, supports glob patterns
# Lines starting with # are comments

# Version control
**/.git/**
**/.hg/**
**/.svn/**
**/.bzr/**

# Python
**/__pycache__/**
**/*.pyc
**/*.pyo
**/*.pyd
**/.Python
**/*.egg-info/**
**/dist/**
**/build/**
**/.pytest_cache/**
**/.mypy_cache/**
**/.ruff_cache/**
**/.coverage
**/*.coverage
**/.hypothesis/**

# Virtual environments
**/.venv/**
**/venv/**
**/.env/**
**/env/**
**/ENV/**

# Node
**/node_modules/**
**/npm-debug.log
**/yarn-error.log
**/yarn-debug.log
**/.npm/**
**/.yarn/**

# IDE
**/.idea/**
**/.vscode/**
**/*.swp
**/*.swo
**/*~
**/.DS_Store
**/Thumbs.db

# Build outputs
**/out/**
**/output/**
**/outputs/**
**/target/**
**/bin/**
**/obj/**

# Logs
**/logs/**
**/*.log

# Temporary files
**/tmp/**
**/temp/**
**/.tmp/**
**/.temp/**

# Config files to exclude
.locus/**
.locusignore
.locusallow
"""


def create_default_config_if_needed(project_path: str) -> None:
    """Creates default .locus directory and config files if they don't exist."""
    project_root = Path(project_path)
    locus_dir = project_root / ".locus"
    locus_allow = locus_dir / "allow"
    locus_ignore = locus_dir / "ignore"

    # Check if any config files exist (new or legacy)
    legacy_allow = project_root / ".locusallow"
    legacy_ignore = project_root / ".locusignore"

    # Only create if no config exists at all
    if not any([locus_allow.exists(), locus_ignore.exists(), legacy_allow.exists(), legacy_ignore.exists()]):
        try:
            # Create .locus directory
            locus_dir.mkdir(exist_ok=True)

            # Create config files
            locus_allow.write_text(DEFAULT_LOCUSALLOW, encoding="utf-8")
            locus_ignore.write_text(DEFAULT_LOCUSIGNORE, encoding="utf-8")

            logger.info(f"Created .locus directory with default config files at {locus_dir}")
        except OSError as e:
            logger.warning(f"Could not create .locus config directory: {e}")

    # Migrate legacy files if they exist and new directory doesn't
    elif not locus_dir.exists() and (legacy_allow.exists() or legacy_ignore.exists()):
        try:
            locus_dir.mkdir(exist_ok=True)

            if legacy_allow.exists():
                content = legacy_allow.read_text(encoding="utf-8")
                locus_allow.write_text(content, encoding="utf-8")
                legacy_allow.unlink()  # Remove old file
                logger.info(f"Migrated .locusallow to {locus_allow}")

            if legacy_ignore.exists():
                content = legacy_ignore.read_text(encoding="utf-8")
                locus_ignore.write_text(content, encoding="utf-8")
                legacy_ignore.unlink()  # Remove old file
                logger.info(f"Migrated .locusignore to {locus_ignore}")

        except OSError as e:
            logger.warning(f"Could not migrate legacy config files: {e}")


def load_project_config(project_path: str) -> Tuple[Set[str], Set[str]]:
    """Loads ignore and allow patterns from config files.

    Priority order:
    1. .locus/allow and .locus/ignore (new directory structure)
    2. .locusallow / .locusignore (legacy root files for backwards compatibility)

    If no config exists, creates default .locus directory and files.
    """
    # Try to create default config files if needed
    create_default_config_if_needed(project_path)

    project_root = Path(project_path)

    # Check for new directory structure first
    locus_dir = project_root / ".locus"
    new_ignore = locus_dir / "ignore"
    new_allow = locus_dir / "allow"

    # Check for legacy root files
    legacy_ignore = project_root / ".locusignore"
    legacy_allow = project_root / ".locusallow"

    # Use new structure if available, otherwise fall back to legacy
    ignore_file = str(new_ignore) if new_ignore.exists() else str(legacy_ignore)
    allow_file = str(new_allow) if new_allow.exists() else str(legacy_allow)

    ignore_patterns = _read_pattern_file(ignore_file)
    allow_patterns = _read_pattern_file(allow_file)

    logger.debug(f"Loaded {len(ignore_patterns)} ignore patterns.")
    logger.debug(f"Loaded {len(allow_patterns)} allow patterns.")

    return ignore_patterns, allow_patterns


def _read_pattern_file(filepath: str) -> Set[str]:
    """Reads a pattern file, ignoring comments and empty lines."""
    patterns: Set[str] = set()
    if not os.path.isfile(filepath):
        return patterns

    try:
        with open(filepath, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.add(line)
    except OSError as e:
        logger.error(f"Could not read pattern file {filepath}: {e}")

    return patterns
