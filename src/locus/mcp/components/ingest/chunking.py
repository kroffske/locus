from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import List


@dataclass
class Chunk:
    """Represents a chunk of code with metadata."""

    id: str
    text: str
    start: int
    end: int
    symbols: List[str] | None = None


def chunk_file(
    content: str, line_window: int = 150, overlap: int = 25
) -> List[Chunk]:
    """Chunks file content using a simple line-window strategy."""
    chunks = []
    lines = content.splitlines()
    num_lines = len(lines)
    step = line_window - overlap

    for start_line in range(0, num_lines, step):
        end_line = min(start_line + line_window, num_lines)
        chunk_text = "\n".join(lines[start_line:end_line])

        if not chunk_text.strip():
            continue

        chunk_id = str(uuid.uuid4())
        chunks.append(
            Chunk(
                id=chunk_id,
                text=chunk_text,
                start=start_line + 1,
                end=end_line,
            )
        )
    return chunks
