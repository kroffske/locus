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
.locusignore
.locusallow
.claudeignore
.claudeallow
"""


def create_default_config_if_needed(project_path: str) -> None:
    """Creates default .locusallow and .locusignore files if they don't exist."""
    locus_allow = Path(project_path) / ".locusallow"
    locus_ignore = Path(project_path) / ".locusignore"
    
    if not locus_allow.exists() and not (Path(project_path) / ".claudeallow").exists():
        try:
            locus_allow.write_text(DEFAULT_LOCUSALLOW, encoding="utf-8")
            logger.info(f"Created default .locusallow file at {locus_allow}")
        except OSError as e:
            logger.warning(f"Could not create .locusallow file: {e}")
    
    if not locus_ignore.exists() and not (Path(project_path) / ".claudeignore").exists():
        try:
            locus_ignore.write_text(DEFAULT_LOCUSIGNORE, encoding="utf-8")
            logger.info(f"Created default .locusignore file at {locus_ignore}")
        except OSError as e:
            logger.warning(f"Could not create .locusignore file: {e}")


def load_project_config(project_path: str) -> Tuple[Set[str], Set[str]]:
    """Loads ignore and allow patterns from config files.
    
    Priority order:
    1. .locusallow / .locusignore (new names)
    2. .claudeallow / .claudeignore (legacy names for compatibility)
    
    If neither exists, creates default .locus* files.
    """
    # Try to create default config files if needed
    create_default_config_if_needed(project_path)
    
    # Check for new names first, then fall back to legacy names
    locus_ignore = os.path.join(project_path, ".locusignore")
    locus_allow = os.path.join(project_path, ".locusallow")
    claude_ignore = os.path.join(project_path, ".claudeignore")
    claude_allow = os.path.join(project_path, ".claudeallow")
    
    # Use locus files if they exist, otherwise fall back to claude files
    ignore_file = locus_ignore if os.path.exists(locus_ignore) else claude_ignore
    allow_file = locus_allow if os.path.exists(locus_allow) else claude_allow

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
