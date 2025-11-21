"""MCP-specific test fixtures and configuration."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import asyncio


@pytest.fixture
def temp_project(tmp_path: Path):
    """Create a temporary project structure for MCP testing."""
    project_root = tmp_path / "test_mcp_project"
    project_root.mkdir()

    # Create .locus config
    locus_dir = project_root / ".locus"
    locus_dir.mkdir()
    (locus_dir / "allow").write_text("*.py\n*.md\n*.txt\n")
    (locus_dir / "ignore").write_text("__pycache__/\n*.pyc\n.git/\n")

    # Create test source files
    src_dir = project_root / "src"
    src_dir.mkdir()

    (src_dir / "main.py").write_text("""
def hello_world():
    \"\"\"Simple hello world function.\"\"\"
    return "Hello, World!"

class Calculator:
    def add(self, a, b):
        return a + b

    def multiply(self, a, b):
        return a * b
""")

    (src_dir / "utils.py").write_text("""
import os
from typing import List

def read_file(path: str) -> str:
    \"\"\"Read file contents.\"\"\"
    with open(path, 'r') as f:
        return f.read()

def process_items(items: List[str]) -> List[str]:
    \"\"\"Process a list of items.\"\"\"
    return [item.strip().upper() for item in items]
""")

    (project_root / "README.md").write_text("""
# Test Project

This is a test project for MCP functionality.

## Features
- Simple functions
- Classes with methods
- File operations
""")

    return project_root


@pytest.fixture
def mock_sentence_transformers():
    """Mock SentenceTransformers to avoid requiring actual model."""
    with patch("sentence_transformers.SentenceTransformer") as mock_model:
        mock_instance = MagicMock()
        mock_instance.encode.return_value = [[0.1, 0.2, 0.3] for _ in range(10)]
        mock_model.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_lancedb():
    """Mock LanceDB to avoid requiring actual database."""
    with patch("lancedb.connect") as mock_connect:
        mock_db = MagicMock()
        mock_table = MagicMock()
        mock_table.search.return_value.limit.return_value.where.return_value.to_list.return_value = []
        mock_table.add.return_value = None
        mock_table.delete.return_value = None
        mock_db.create_table.return_value = mock_table
        mock_db.open_table.return_value = mock_table
        mock_connect.return_value = mock_db
        yield mock_db


@pytest.fixture
def mock_fastmcp():
    """Mock FastMCP to avoid requiring actual MCP server."""
    with patch("fastmcp.FastMCP") as mock_mcp:
        mock_instance = MagicMock()
        mock_instance.tool.return_value = lambda func: func  # Decorator passthrough
        mock_instance.run_stdio.return_value = None
        mock_mcp.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_code_content():
    """Sample code content for testing chunking."""
    return """
def function_one():
    '''First function with some logic.'''
    x = 1
    y = 2
    return x + y

def function_two():
    '''Second function with more logic.'''
    data = [1, 2, 3, 4, 5]
    total = sum(data)
    return total

class MyClass:
    '''A sample class for testing.'''

    def __init__(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def set_value(self, new_value):
        self.value = new_value

def long_function():
    '''A longer function that spans many lines.'''
    result = []
    for i in range(100):
        if i % 2 == 0:
            result.append(i * 2)
        else:
            result.append(i * 3)

    # More processing
    processed = []
    for item in result:
        if item > 50:
            processed.append(item)

    return processed
"""


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_db_path(tmp_path):
    """Temporary path for test database."""
    return str(tmp_path / "test_db")


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    settings = {
        "embedding": {
            "provider": "huggingface",
            "model_name": "test-model",
            "trust_remote_code": True,
            "batch_size": 32,
        },
        "vector_store": {"provider": "lancedb", "db_path": "/tmp/test_db"},
        "index": {"chunking_strategy": "lines", "max_lines": 150, "overlap": 25},
    }
    return settings
