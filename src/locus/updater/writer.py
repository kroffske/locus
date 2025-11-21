import logging
import os
import shutil
from typing import List

from ..formatting.colors import (
    confirm,
    print_error,
    print_file_status,
    print_header,
    print_info,
    print_success,
    print_warning,
)
from .models import UpdateOperation

logger = logging.getLogger(__name__)


def _create_backup(target_path: str):
    """Creates a .bak backup of a file."""
    if not os.path.exists(target_path):
        return
    backup_path = f"{target_path}.bak"
    try:
        shutil.copy2(target_path, backup_path)
        logger.info(f"Created backup: {backup_path}")
    except OSError as e:
        logger.error(f"Failed to create backup for {target_path}: {e}")


def apply_updates(operations: List[UpdateOperation], backup: bool, dry_run: bool):
    """Applies a list of update operations to the filesystem with safety checks."""
    if not operations:
        return

    print_header("Proposed File Changes")
    for op in operations:
        op.is_new_file = not os.path.exists(op.target_path)
        status = "CREATE" if op.is_new_file else "UPDATE"
        print_file_status(status, op.target_path)

    if dry_run:
        print_warning("\nDRY RUN - No files will be changed")
        return

    try:
        if not confirm("\nDo you want to apply these changes?"):
            print_warning("Update cancelled.")
            return
    except (EOFError, KeyboardInterrupt):
        print_error("\nUpdate cancelled by user.")
        return

    print_info("\nApplying changes...")
    for op in operations:
        try:
            # Ensure target directory exists
            target_dir = os.path.dirname(op.target_path)
            if target_dir:
                os.makedirs(target_dir, exist_ok=True)

            # Create backup if requested
            if backup:
                _create_backup(op.target_path)

            # Write the new content
            with open(op.target_path, "w", encoding="utf-8") as f:
                f.write(op.new_content)

            status = "CREATED" if op.is_new_file else "UPDATED"
            print_file_status(status, op.target_path)
        except OSError as e:
            logger.error(f"Failed to write to {op.target_path}: {e}")

    print_success("\nUpdate process complete!")
