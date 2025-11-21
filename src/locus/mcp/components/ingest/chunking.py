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
    content: str, strategy: str = "lines", line_window: int = 150, overlap: int = 25
) -> List[Chunk]:
    """Chunks file content using the specified strategy."""
    if strategy == "lines":
        return _chunk_lines(content, line_window, overlap)
    elif strategy == "semantic":
        return _chunk_semantic(content)
    else:
        raise ValueError(f"Unknown chunking strategy: {strategy}")


def _chunk_lines(content: str, line_window: int, overlap: int) -> List[Chunk]:
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


def _chunk_semantic(content: str) -> List[Chunk]:
    """Placeholder for semantic chunking (e.g., via langchain or sentence boundaries)."""
    # TODO: Implement semantic chunking, potentially with optional dep
    try:
        # Example: simple split by double newlines as placeholder
        paragraphs = content.split("\n\n")
        chunks = []
        line = 1
        for para in paragraphs:
            if not para.strip():
                continue
            end_line = line + para.count("\n")
            chunk_id = str(uuid.uuid4())
            chunks.append(
                Chunk(
                    id=chunk_id,
                    text=para,
                    start=line,
                    end=end_line,
                )
            )
            line = end_line + 1
        return chunks
    except Exception:
        raise ValueError(
            "Semantic chunking requires additional dependencies or configuration."
        )
