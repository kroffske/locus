"""Tests for updater functionality."""

from locus.updater.parser import _sanitize_markdown_backticks, parse_markdown_to_updates


class TestSanitizeMarkdownBackticks:
    """Test cases for the _sanitize_markdown_backticks function."""

    def test_consecutive_backticks(self):
        """Test handling of consecutive backticks (6+ in a row)."""
        # Case 1: Two adjacent code blocks
        input_md = """```python
# source: file1.py
content1
``````python
# source: file2.py
content2
```"""

        result = _sanitize_markdown_backticks(input_md)

        # Should have whitespace between the blocks
        assert "```\n\n```python" in result
        # Should still be parseable
        assert result.count("```") == 4

    def test_unmatched_closing_backticks(self):
        """Test handling of unmatched closing backticks."""
        # Case 1: Extra closing backtick
        input_md = """```python
# source: file1.py
content1
```
```
Some text here
```python
# source: file2.py
content2
```"""

        result = _sanitize_markdown_backticks(input_md)

        # Should remove the extra closing backtick
        lines = result.split("\n")
        closing_count = sum(1 for line in lines if line.strip() == "```")
        opening_count = sum(
            1
            for line in lines
            if line.strip().startswith("```") and line.strip() != "```"
        )

        assert closing_count == opening_count

    def test_multiple_consecutive_backticks(self):
        """Test handling of multiple consecutive backtick sequences."""
        input_md = """```python
# source: file1.py
content1
``````javascript
# source: file2.py
content2
``````bash
# source: file3.py
content3
```"""

        result = _sanitize_markdown_backticks(input_md)

        # Should have proper spacing between all blocks
        assert result.count("```\n\n```") == 2

    def test_normal_markdown_unchanged(self):
        """Test that normal markdown is not affected."""
        input_md = """```python
# source: file1.py
def hello():
    print("world")
```

Some text here

```javascript
# source: file2.js
console.log("hello");
```"""

        result = _sanitize_markdown_backticks(input_md)

        # Should be largely unchanged (maybe some whitespace normalization)
        assert "# source: file1.py" in result
        assert "# source: file2.js" in result
        assert "def hello():" in result

    def test_empty_content(self):
        """Test handling of empty content."""
        result = _sanitize_markdown_backticks("")
        assert result == ""

    def test_no_code_blocks(self):
        """Test content with no code blocks."""
        input_md = "This is just regular markdown text with no code blocks."
        result = _sanitize_markdown_backticks(input_md)
        assert result == input_md


class TestParseMarkdownToUpdates:
    """Test cases for parse_markdown_to_updates function."""

    def test_parse_single_file_block(self):
        """Test parsing a single file block."""
        markdown = """```python
# source: test.py
def hello():
    print("world")
```"""

        operations = parse_markdown_to_updates(markdown)

        assert len(operations) == 1
        assert operations[0].target_path == "test.py"
        assert "def hello():" in operations[0].new_content
        assert operations[0].new_content.endswith("\n")

    def test_parse_multiple_file_blocks(self):
        """Test parsing multiple file blocks."""
        markdown = """```python
# source: file1.py
content1
```

Some text

```javascript
# source: file2.js
content2
```"""

        operations = parse_markdown_to_updates(markdown)

        assert len(operations) == 2
        assert operations[0].target_path == "file1.py"
        assert operations[1].target_path == "file2.js"

    def test_parse_with_consecutive_backticks(self):
        """Test parsing markdown with consecutive backticks edge case."""
        markdown = """```python
# source: file1.py
content1
``````python
# source: file2.py
content2
```"""

        operations = parse_markdown_to_updates(markdown)

        # Should successfully parse both files despite the consecutive backticks
        assert len(operations) == 2
        assert operations[0].target_path == "file1.py"
        assert operations[1].target_path == "file2.py"

    def test_parse_with_unmatched_closing_backticks(self):
        """Test parsing markdown with unmatched closing backticks."""
        markdown = """```python
# source: file1.py
content1
```
```
```python
# source: file2.py
content2
```"""

        operations = parse_markdown_to_updates(markdown)

        # Should successfully parse both files despite unmatched backticks
        assert len(operations) == 2
        assert operations[0].target_path == "file1.py"
        assert operations[1].target_path == "file2.py"

    def test_parse_different_source_formats(self):
        """Test parsing different source header formats."""
        markdown = """```python
# source: file1.py
content1
```

```python
#source: file2.py
content2
```

```python
Source: file3.py
content3
```

```python
source: file4.py
content4
```"""

        operations = parse_markdown_to_updates(markdown)

        assert len(operations) == 4
        paths = [op.target_path for op in operations]
        assert "file1.py" in paths
        assert "file2.py" in paths
        assert "file3.py" in paths
        assert "file4.py" in paths

    def test_parse_no_source_headers(self):
        """Test parsing blocks without source headers."""
        markdown = """```python
def hello():
    print("world")
```

```javascript
console.log("hello");
```"""

        operations = parse_markdown_to_updates(markdown)

        # Should not parse any blocks without source headers
        assert len(operations) == 0

    def test_parse_empty_content(self):
        """Test parsing empty content."""
        operations = parse_markdown_to_updates("")
        assert len(operations) == 0

    def test_parse_posix_compliance(self):
        """Test that content ends with newline for POSIX compliance."""
        markdown = """```python
# source: test.py
print("hello")```"""

        operations = parse_markdown_to_updates(markdown)

        assert len(operations) == 1
        assert operations[0].new_content.endswith("\n")
