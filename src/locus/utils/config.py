import logging
import os
from pathlib import Path
from typing import Set, Tuple

logger = logging.getLogger(__name__)

# Default templates for config files
DEFAULT_LOTUSALLOW = """# File patterns to include in analysis
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

DEFAULT_LOTUSIGNORE = """# File patterns to exclude from analysis
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
.lotusignore
.lotusallow
.claudeignore
.claudeallow
"""


def create_default_config_if_needed(project_path: str) -> None:
    """Creates default .lotusallow and .lotusignore files if they don't exist."""
    lotus_allow = Path(project_path) / ".lotusallow"
    lotus_ignore = Path(project_path) / ".lotusignore"
    
    if not lotus_allow.exists() and not (Path(project_path) / ".claudeallow").exists():
        try:
            lotus_allow.write_text(DEFAULT_LOTUSALLOW, encoding="utf-8")
            logger.info(f"Created default .lotusallow file at {lotus_allow}")
        except OSError as e:
            logger.warning(f"Could not create .lotusallow file: {e}")
    
    if not lotus_ignore.exists() and not (Path(project_path) / ".claudeignore").exists():
        try:
            lotus_ignore.write_text(DEFAULT_LOTUSIGNORE, encoding="utf-8")
            logger.info(f"Created default .lotusignore file at {lotus_ignore}")
        except OSError as e:
            logger.warning(f"Could not create .lotusignore file: {e}")


def load_project_config(project_path: str) -> Tuple[Set[str], Set[str]]:
    """Loads ignore and allow patterns from config files.
    
    Priority order:
    1. .lotusallow / .lotusignore (new names)
    2. .claudeallow / .claudeignore (legacy names for compatibility)
    
    If neither exists, creates default .lotus* files.
    """
    # Try to create default config files if needed
    create_default_config_if_needed(project_path)
    
    # Check for new names first, then fall back to legacy names
    lotus_ignore = os.path.join(project_path, ".lotusignore")
    lotus_allow = os.path.join(project_path, ".lotusallow")
    claude_ignore = os.path.join(project_path, ".claudeignore")
    claude_allow = os.path.join(project_path, ".claudeallow")
    
    # Use lotus files if they exist, otherwise fall back to claude files
    ignore_file = lotus_ignore if os.path.exists(lotus_ignore) else claude_ignore
    allow_file = lotus_allow if os.path.exists(lotus_allow) else claude_allow

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
