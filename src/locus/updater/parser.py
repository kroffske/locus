import logging
import re
from typing import List

from .models import UpdateOperation

logger = logging.getLogger(__name__)

# Regex to find file blocks, e.g., ### File: `path/to/file.py`
FILE_BLOCK_REGEX = re.compile(
    r"###\s+File:\s+`([^`]+)`\s*\n"  # Header line with filename
    r"```[a-zA-Z]*\n"  # Start of the code block
    r"(.*?)\n"  # The content (non-greedy)
    r"```",  # End of the code block
    re.DOTALL,  # Allow . to match newlines
)


def parse_markdown_to_updates(markdown_content: str) -> List[UpdateOperation]:
    """Parses a Markdown string to find specially formatted code blocks and
    creates a list of UpdateOperation objects.
    """
    operations: List[UpdateOperation] = []
    matches = FILE_BLOCK_REGEX.finditer(markdown_content)

    for match in matches:
        target_path = match.group(1).strip()
        new_content = match.group(2)

        # Clean the content by removing a potential source header line
        lines = new_content.split("\n")
        if lines and lines[0].strip().startswith("# source:"):
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
