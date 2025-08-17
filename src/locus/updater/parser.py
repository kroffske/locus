import logging
import re
from typing import List

from .models import UpdateOperation

logger = logging.getLogger(__name__)

# Regex to find code blocks where the first line contains the file path
# Format: ```python
#         # source: path/to/file.py
#         code content
#         ```
CODE_BLOCK_REGEX = re.compile(
    r"```[a-zA-Z]*\n"  # Start of code block with optional language
    r"(.*?)\n"  # The content (non-greedy)
    r"```",  # End of the code block
    re.DOTALL | re.MULTILINE,  # Allow . to match newlines
)


def parse_markdown_to_updates(markdown_content: str) -> List[UpdateOperation]:
    """Parses a Markdown string to find code blocks where the first line
    contains the file path in the format: # source: path/to/file.py
    """
    operations: List[UpdateOperation] = []
    matches = CODE_BLOCK_REGEX.finditer(markdown_content)

    for match in matches:
        content = match.group(1)
        lines = content.split("\n")

        # Check if first line contains the file path
        if not lines:
            continue

        first_line = lines[0].strip().lower()

        # Extract file path from various formats:
        # # source: path/to/file.py
        # # Source: path/to/file.py
        # source: path/to/file.py
        target_path = None
        original_first_line = lines[0].strip()

        if first_line.startswith("# source:") or first_line.startswith("#source:"):
            # Find where "source:" ends in the original line (case-insensitive search)
            idx = original_first_line.lower().index("source:") + 7
            target_path = original_first_line[idx:].strip()
        elif first_line.startswith("source:"):
            target_path = original_first_line[7:].strip()

        if not target_path:
            continue  # Skip blocks without proper source header

        # Remove the source line from content
        new_content = "\n".join(lines[1:])

        # Ensure content ends with a newline for POSIX compliance
        if new_content and not new_content.endswith("\n"):
            new_content += "\n"

        op = UpdateOperation(
            target_path=target_path,
            new_content=new_content,
        )
        operations.append(op)
        logger.debug(f"Parsed update operation for file: {target_path}")

    if not operations:
        logger.warning("No file blocks matching the expected format were found in the input.")

    return operations
