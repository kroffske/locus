import logging
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)

KNOWN_TEXT_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".html",
    ".css",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".sh",
    ".bat",
    ".gitignore",
    ".dockerignore",
    "dockerfile",
    ".csv",
    ".tsv",
    ".sql",
    ".xml",
    "readme",
}


class FileCache:
    """Caches file contents to avoid repeated disk I/O."""

    def __init__(self):
        self.content_cache: Dict[str, Optional[str]] = {}
        logger.debug("FileCache initialized.")

    def get_content(self, file_path: str) -> Optional[str]:
        """Gets file content from cache or reads from disk.
        Returns None for binary files or on read error.
        """
        if file_path in self.content_cache:
            return self.content_cache[file_path]

        try:
            _, extension = os.path.splitext(file_path)
            if extension.lower() not in KNOWN_TEXT_EXTENSIONS and extension:
                with open(file_path, "rb") as f:
                    if b"\0" in f.read(1024):
                        logger.debug(f"Detected binary file, skipping: {file_path}")
                        self.content_cache[file_path] = None
                        return None

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            self.content_cache[file_path] = content
            return content
        except OSError as e:
            logger.error(f"Error reading file {file_path}: {e}")
            self.content_cache[file_path] = None
            return None

    def clear(self) -> None:
        """Clears the in-memory caches."""
        self.content_cache.clear()
