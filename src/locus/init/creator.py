"""Core file creation logic for project initialization.

Handles template file creation with conflict detection and user interaction.
Separates I/O boundary operations from pure logic functions.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Set

from .templates import get_default_templates, get_template_content

logger = logging.getLogger(__name__)


class InitError(Exception):
    """Raised when initialization encounters an error."""


class FileConflictError(InitError):
    """Raised when template files already exist and user chooses not to continue."""


def check_existing_files(target_dir: Path, template_files: Dict[str, str]) -> Set[str]:
    """Check which template files already exist in the target directory.

    Args:
        target_dir: Directory to check for existing files
        template_files: Dict mapping filename to template name

    Returns:
        Set of filenames that already exist
    """
    existing = set()
    for filename in template_files.keys():
        file_path = target_dir / filename
        if file_path.exists():
            existing.add(filename)
    return existing


def prompt_user_for_overwrite(existing_files: Set[str]) -> bool:
    """Prompt user whether to continue when files exist.

    Args:
        existing_files: Set of existing filenames

    Returns:
        True if user wants to continue, False otherwise
    """
    if not existing_files:
        return True

    file_list = ", ".join(sorted(existing_files))
    logger.warning(f"The following template files already exist: {file_list}")

    try:
        response = input("Continue and overwrite existing files? (y/N): ").strip().lower()
        return response in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


def prompt_user_for_each_file(existing_files: Set[str]) -> Set[str]:
    """Prompt user for each existing file individually.

    Args:
        existing_files: Set of existing filenames

    Returns:
        Set of filenames user wants to overwrite
    """
    files_to_overwrite = set()

    for filename in sorted(existing_files):
        try:
            response = input(f"Overwrite existing {filename}? (y/N): ").strip().lower()
            if response in ("y", "yes"):
                files_to_overwrite.add(filename)
        except (EOFError, KeyboardInterrupt):
            logger.info("Initialization cancelled by user.")
            break

    return files_to_overwrite


def create_template_files(
    target_dir: Path,
    template_files: Dict[str, str],
    substitutions: Dict[str, str] = None,
    files_to_create: Set[str] = None,
) -> List[str]:
    """Create template files in the target directory.

    Args:
        target_dir: Directory where files should be created
        template_files: Dict mapping filename to template name
        substitutions: Optional substitutions for template content
        files_to_create: Optional set of specific files to create (defaults to all)

    Returns:
        List of successfully created filenames

    Raises:
        InitError: If file creation fails
    """
    if files_to_create is None:
        files_to_create = set(template_files.keys())

    created_files = []
    substitutions = substitutions or {}

    for filename in files_to_create:
        if filename not in template_files:
            logger.warning(f"Skipping unknown template file: {filename}")
            continue

        template_name = template_files[filename]
        file_path = target_dir / filename

        try:
            content = get_template_content(template_name, substitutions)

            # Ensure parent directory exists
            os.makedirs(target_dir, exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            created_files.append(filename)
            logger.info(f"Created {filename}")

        except (OSError, ValueError) as e:
            raise InitError(f"Failed to create {filename}: {e}") from e

    return created_files


def init_project(
    target_dir: Path = None,
    force: bool = False,
    interactive: bool = True,
    project_name: str = None,
) -> List[str]:
    """Initialize a project with template files.

    Args:
        target_dir: Directory to initialize (defaults to current directory)
        force: If True, overwrite existing files without prompting
        interactive: If True, prompt for individual file overwrites when conflicts exist
        project_name: Name to use in templates (defaults to directory name)

    Returns:
        List of successfully created filenames

    Raises:
        InitError: If initialization fails
        FileConflictError: If files exist and user chooses not to continue
    """
    if target_dir is None:
        target_dir = Path.cwd()

    target_dir = Path(target_dir).resolve()

    if not target_dir.exists():
        raise InitError(f"Target directory does not exist: {target_dir}")

    if not target_dir.is_dir():
        raise InitError(f"Target path is not a directory: {target_dir}")

    # Determine project name
    if project_name is None:
        project_name = target_dir.name

    # Get template definitions
    template_files = get_default_templates()
    substitutions = {"project_name": project_name}

    # Check for existing files
    existing_files = check_existing_files(target_dir, template_files)

    # Determine which files to create
    files_to_create = set(template_files.keys())

    if existing_files and not force:
        if interactive:
            # Interactive mode: prompt for each file
            files_to_overwrite = prompt_user_for_each_file(existing_files)
            files_to_create = (files_to_create - existing_files) | files_to_overwrite
        else:
            # Non-interactive mode: ask once for all files
            if not prompt_user_for_overwrite(existing_files):
                raise FileConflictError("User chose not to overwrite existing files")

    # Create the files
    try:
        created_files = create_template_files(target_dir, template_files, substitutions, files_to_create)
        logger.info(f"Successfully initialized project in {target_dir}")
        logger.info(f"Created {len(created_files)} template files")
        return created_files

    except Exception as e:
        if isinstance(e, (InitError, FileConflictError)):
            raise
        raise InitError(f"Unexpected error during initialization: {e}") from e
