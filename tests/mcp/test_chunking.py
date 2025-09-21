"""Tests for chunking functionality."""
import pytest
from locus.mcp.components.ingest.chunking import chunk_file, _chunk_lines, _chunk_semantic, Chunk


class TestChunk:
    """Test the Chunk dataclass."""

    def test_chunk_creation(self):
        """Test creating a chunk with all fields."""
        chunk = Chunk(
            id="test-id",
            text="sample text",
            start=1,
            end=5,
            symbols=["func1", "class1"]
        )
        assert chunk.id == "test-id"
        assert chunk.text == "sample text"
        assert chunk.start == 1
        assert chunk.end == 5
        assert chunk.symbols == ["func1", "class1"]

    def test_chunk_optional_symbols(self):
        """Test creating a chunk without symbols."""
        chunk = Chunk(
            id="test-id",
            text="sample text",
            start=1,
            end=5
        )
        assert chunk.symbols is None


class TestChunkFile:
    """Test the main chunk_file function."""

    def test_lines_strategy(self, sample_code_content):
        """Test chunking with lines strategy."""
        chunks = chunk_file(sample_code_content, strategy="lines", line_window=10, overlap=2)

        assert len(chunks) > 0
        assert all(isinstance(chunk, Chunk) for chunk in chunks)
        assert all(chunk.id for chunk in chunks)  # All have IDs
        assert all(chunk.text.strip() for chunk in chunks)  # All have content

    def test_semantic_strategy(self, sample_code_content):
        """Test chunking with semantic strategy."""
        chunks = chunk_file(sample_code_content, strategy="semantic")

        assert len(chunks) > 0
        assert all(isinstance(chunk, Chunk) for chunk in chunks)
        assert all(chunk.id for chunk in chunks)

    def test_invalid_strategy(self, sample_code_content):
        """Test that invalid strategy raises ValueError."""
        with pytest.raises(ValueError, match="Unknown chunking strategy"):
            chunk_file(sample_code_content, strategy="invalid_strategy")

    def test_default_strategy(self, sample_code_content):
        """Test that default strategy is lines."""
        chunks_default = chunk_file(sample_code_content)
        chunks_lines = chunk_file(sample_code_content, strategy="lines")

        assert len(chunks_default) == len(chunks_lines)


class TestChunkLines:
    """Test the line-based chunking strategy."""

    def test_simple_chunking(self):
        """Test basic line chunking functionality."""
        content = "line1\nline2\nline3\nline4\nline5"
        chunks = _chunk_lines(content, line_window=3, overlap=1)

        assert len(chunks) == 3

        # First chunk: lines 1-3
        assert chunks[0].start == 1
        assert chunks[0].end == 3
        assert "line1" in chunks[0].text
        assert "line3" in chunks[0].text

        # Second chunk: lines 3-5 (overlap of 1)
        assert chunks[1].start == 3
        assert chunks[1].end == 5
        assert "line3" in chunks[1].text
        assert "line5" in chunks[1].text

        # Third chunk: line 5 only (last partial chunk)
        assert chunks[2].start == 5
        assert chunks[2].end == 5
        assert chunks[2].text == "line5"

    def test_no_overlap(self):
        """Test chunking without overlap."""
        content = "line1\nline2\nline3\nline4"
        chunks = _chunk_lines(content, line_window=2, overlap=0)

        assert len(chunks) == 2
        assert chunks[0].start == 1
        assert chunks[0].end == 2
        assert chunks[1].start == 3
        assert chunks[1].end == 4

    def test_large_window(self):
        """Test chunking where window is larger than content."""
        content = "line1\nline2\nline3"
        chunks = _chunk_lines(content, line_window=10, overlap=0)

        assert len(chunks) == 1
        assert chunks[0].start == 1
        assert chunks[0].end == 3
        assert chunks[0].text == content

    def test_empty_content(self):
        """Test chunking empty content."""
        chunks = _chunk_lines("", line_window=5, overlap=1)
        assert len(chunks) == 0

    def test_whitespace_only_content(self):
        """Test chunking content with only whitespace."""
        content = "\n\n\n   \n\n"
        chunks = _chunk_lines(content, line_window=3, overlap=1)
        assert len(chunks) == 0

    def test_single_line(self):
        """Test chunking single line content."""
        content = "single line"
        chunks = _chunk_lines(content, line_window=5, overlap=1)

        assert len(chunks) == 1
        assert chunks[0].text == content
        assert chunks[0].start == 1
        assert chunks[0].end == 1

    def test_chunk_ids_unique(self):
        """Test that chunk IDs are unique."""
        content = "line1\nline2\nline3\nline4\nline5\nline6"
        chunks = _chunk_lines(content, line_window=2, overlap=0)

        ids = [chunk.id for chunk in chunks]
        assert len(ids) == len(set(ids))  # All IDs unique

    def test_realistic_code_chunking(self, sample_code_content):
        """Test chunking realistic code content."""
        chunks = _chunk_lines(sample_code_content, line_window=15, overlap=3)

        assert len(chunks) > 0
        # Check that overlapping content appears in adjacent chunks
        if len(chunks) > 1:
            # Should have some overlap between chunks
            first_lines = chunks[0].text.splitlines()
            second_lines = chunks[1].text.splitlines()

            # Find overlap
            overlap_found = False
            for line in first_lines[-5:]:  # Check last 5 lines of first chunk
                if line in second_lines[:5]:  # Against first 5 lines of second chunk
                    overlap_found = True
                    break
            assert overlap_found or chunks[0].end == chunks[1].start - 1


class TestChunkSemantic:
    """Test the semantic chunking strategy."""

    def test_semantic_chunking_basic(self):
        """Test basic semantic chunking functionality."""
        content = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        chunks = _chunk_semantic(content)

        assert len(chunks) >= 1
        assert all(isinstance(chunk, Chunk) for chunk in chunks)

    def test_semantic_chunking_no_double_newlines(self):
        """Test semantic chunking with content that has no double newlines."""
        content = "Line 1\nLine 2\nLine 3"
        chunks = _chunk_semantic(content)

        # Should still create one chunk
        assert len(chunks) == 1
        assert chunks[0].text == content

    def test_semantic_chunking_empty_paragraphs(self):
        """Test semantic chunking with empty paragraphs."""
        content = "Para 1\n\n\n\nPara 2\n\n"
        chunks = _chunk_semantic(content)

        # Should skip empty paragraphs
        assert len(chunks) == 2
        assert "Para 1" in chunks[0].text
        assert "Para 2" in chunks[1].text

    def test_semantic_line_numbers(self):
        """Test that semantic chunking calculates line numbers correctly."""
        content = "Line 1\nLine 2\n\nParagraph 2\nLine 4\nLine 5\n\nParagraph 3"
        chunks = _chunk_semantic(content)

        assert len(chunks) == 3
        assert chunks[0].start == 1
        assert chunks[1].start > chunks[0].end
        assert chunks[2].start > chunks[1].end

    def test_semantic_chunk_ids_unique(self):
        """Test that semantic chunk IDs are unique."""
        content = "Para 1\n\nPara 2\n\nPara 3\n\nPara 4"
        chunks = _chunk_semantic(content)

        ids = [chunk.id for chunk in chunks]
        assert len(ids) == len(set(ids))

    def test_semantic_empty_content(self):
        """Test semantic chunking with empty content."""
        chunks = _chunk_semantic("")
        assert len(chunks) == 0

    def test_semantic_whitespace_only(self):
        """Test semantic chunking with only whitespace."""
        content = "\n\n   \n\n  \n\n"
        chunks = _chunk_semantic(content)
        assert len(chunks) == 0


class TestChunkFileIntegration:
    """Integration tests for chunk_file with different strategies."""

    def test_both_strategies_produce_chunks(self, sample_code_content):
        """Test that both strategies produce valid chunks."""
        lines_chunks = chunk_file(sample_code_content, strategy="lines")
        semantic_chunks = chunk_file(sample_code_content, strategy="semantic")

        assert len(lines_chunks) > 0
        assert len(semantic_chunks) > 0

        # Both should have valid chunks
        for chunk in lines_chunks + semantic_chunks:
            assert chunk.id
            assert chunk.text.strip()
            assert chunk.start > 0
            assert chunk.end >= chunk.start

    def test_strategies_may_differ(self, sample_code_content):
        """Test that different strategies may produce different results."""
        lines_chunks = chunk_file(sample_code_content, strategy="lines", line_window=10)
        semantic_chunks = chunk_file(sample_code_content, strategy="semantic")

        # Results may differ in number or content
        # This is expected as strategies work differently
        assert isinstance(lines_chunks, list)
        assert isinstance(semantic_chunks, list)

    def test_parameter_forwarding(self, sample_code_content):
        """Test that parameters are correctly forwarded to strategy functions."""
        # Test with small window to force multiple chunks
        chunks_small = chunk_file(
            sample_code_content,
            strategy="lines",
            line_window=5,
            overlap=1
        )

        # Test with large window
        chunks_large = chunk_file(
            sample_code_content,
            strategy="lines",
            line_window=100,
            overlap=1
        )

        # Small window should create more chunks
        assert len(chunks_small) >= len(chunks_large)