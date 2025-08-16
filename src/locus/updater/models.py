from dataclasses import dataclass


@dataclass
class UpdateOperation:
    """A simple data structure to hold a pending file change."""

    target_path: str
    new_content: str
    is_new_file: bool = False
