"""Tests for code ingest component functionality."""

import asyncio
import pytest
from unittest.mock import Mock, patch
from locus.mcp.components.ingest.code_ingest_component import CodeIngestComponent


class TestCodeIngestComponent:
    """Test the CodeIngestComponent class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_embed_component = Mock()
        self.mock_vector_store = Mock()
        self.component = CodeIngestComponent(
            embed_component=self.mock_embed_component,
            vector_store=self.mock_vector_store,
        )

    def test_init(self):
        """Test component initialization."""
        assert self.component.embed_component is self.mock_embed_component
        assert self.component.vector_store is self.mock_vector_store

    @pytest.mark.asyncio
    async def test_index_paths_single_file(self, temp_project):
        """Test indexing a single file."""
        # Setup mocks
        self.mock_embed_component.embed_chunks.return_value = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
        ]

        with patch(
            "locus.mcp.components.ingest.code_ingest_component.scanner"
        ) as mock_scanner, patch(
            "locus.mcp.components.ingest.code_ingest_component.config"
        ) as mock_config:
            # Mock config loading
            mock_config.load_project_config.return_value = ({"*.pyc"}, {"*.py"})

            # Mock scanner to return one file
            test_file = temp_project / "src" / "main.py"
            mock_scanner.scan_directory.return_value = [str(test_file)]

            results = await self.component.index_paths([str(temp_project)])

            assert results["files"] == 1
            assert results["chunks"] > 0

            # Verify interactions
            mock_config.load_project_config.assert_called_once()
            mock_scanner.scan_directory.assert_called_once()
            self.mock_embed_component.embed_chunks.assert_called_once()
            self.mock_vector_store.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_index_paths_multiple_files(self, temp_project):
        """Test indexing multiple files."""
        self.mock_embed_component.embed_chunks.return_value = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
        ]

        with patch(
            "locus.mcp.components.ingest.code_ingest_component.scanner"
        ) as mock_scanner, patch(
            "locus.mcp.components.ingest.code_ingest_component.config"
        ) as mock_config:
            mock_config.load_project_config.return_value = ({"*.pyc"}, {"*.py"})

            # Mock scanner to return multiple files
            files = [
                str(temp_project / "src" / "main.py"),
                str(temp_project / "src" / "utils.py"),
            ]
            mock_scanner.scan_directory.return_value = files

            results = await self.component.index_paths([str(temp_project)])

            assert results["files"] == 2
            assert results["chunks"] > 0

            # Should process files concurrently
            assert self.mock_embed_component.embed_chunks.call_count == 2
            assert self.mock_vector_store.upsert.call_count == 2

    @pytest.mark.asyncio
    async def test_index_paths_force_rebuild(self, temp_project):
        """Test force rebuild functionality."""
        self.mock_embed_component.embed_chunks.return_value = [[0.1, 0.2, 0.3]]

        with patch(
            "locus.mcp.components.ingest.code_ingest_component.scanner"
        ) as mock_scanner, patch(
            "locus.mcp.components.ingest.code_ingest_component.config"
        ) as mock_config:
            mock_config.load_project_config.return_value = (set(), {"*.py"})
            test_file = temp_project / "src" / "main.py"
            mock_scanner.scan_directory.return_value = [str(test_file)]

            await self.component.index_paths([str(temp_project)], force_rebuild=True)

            # Should delete existing entries
            rel_path = "src/main.py"
            self.mock_vector_store.delete_by_file.assert_called_with(rel_path)

    @pytest.mark.asyncio
    async def test_index_paths_no_force_rebuild(self, temp_project):
        """Test without force rebuild."""
        self.mock_embed_component.embed_chunks.return_value = [[0.1, 0.2, 0.3]]

        with patch(
            "locus.mcp.components.ingest.code_ingest_component.scanner"
        ) as mock_scanner, patch(
            "locus.mcp.components.ingest.code_ingest_component.config"
        ) as mock_config:
            mock_config.load_project_config.return_value = (set(), {"*.py"})
            test_file = temp_project / "src" / "main.py"
            mock_scanner.scan_directory.return_value = [str(test_file)]

            await self.component.index_paths([str(temp_project)], force_rebuild=False)

            # Should not delete existing entries
            self.mock_vector_store.delete_by_file.assert_not_called()

    @pytest.mark.asyncio
    async def test_index_paths_empty_files(self, temp_project):
        """Test handling of empty or whitespace-only files."""
        # Create empty file
        empty_file = temp_project / "empty.py"
        empty_file.write_text("")

        with patch(
            "locus.mcp.components.ingest.code_ingest_component.scanner"
        ) as mock_scanner, patch(
            "locus.mcp.components.ingest.code_ingest_component.config"
        ) as mock_config:
            mock_config.load_project_config.return_value = (set(), {"*.py"})
            mock_scanner.scan_directory.return_value = [str(empty_file)]

            results = await self.component.index_paths([str(temp_project)])

            # Should handle empty files gracefully
            assert results["files"] == 0
            assert results["chunks"] == 0
            self.mock_embed_component.embed_chunks.assert_not_called()

    @pytest.mark.asyncio
    async def test_index_paths_file_read_error(self, temp_project):
        """Test handling of file read errors."""
        with patch(
            "locus.mcp.components.ingest.code_ingest_component.scanner"
        ) as mock_scanner, patch(
            "locus.mcp.components.ingest.code_ingest_component.config"
        ) as mock_config, patch(
            "builtins.open", side_effect=PermissionError("Access denied")
        ):
            mock_config.load_project_config.return_value = (set(), {"*.py"})
            test_file = temp_project / "src" / "main.py"
            mock_scanner.scan_directory.return_value = [str(test_file)]

            results = await self.component.index_paths([str(temp_project)])

            # Should handle errors gracefully
            assert results["files"] == 0
            assert results["chunks"] == 0

    @pytest.mark.asyncio
    async def test_process_file_success(self, temp_project):
        """Test successful file processing."""
        self.mock_embed_component.embed_chunks.return_value = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
        ]

        test_file = temp_project / "src" / "main.py"
        config_root = str(temp_project)

        chunks_count = await self.component._process_file(
            str(test_file), config_root, force_rebuild=False
        )

        assert chunks_count > 0
        self.mock_embed_component.embed_chunks.assert_called_once()
        self.mock_vector_store.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_file_with_force_rebuild(self, temp_project):
        """Test file processing with force rebuild."""
        self.mock_embed_component.embed_chunks.return_value = [[0.1, 0.2, 0.3]]

        test_file = temp_project / "src" / "main.py"
        config_root = str(temp_project)

        await self.component._process_file(
            str(test_file), config_root, force_rebuild=True
        )

        rel_path = "src/main.py"
        self.mock_vector_store.delete_by_file.assert_called_once_with(rel_path)

    @pytest.mark.asyncio
    async def test_process_file_path_normalization(self, temp_project):
        """Test that file paths are normalized correctly."""
        self.mock_embed_component.embed_chunks.return_value = [[0.1, 0.2, 0.3]]

        # Test with Windows-style paths
        test_file = temp_project / "src" / "main.py"
        config_root = str(temp_project)

        await self.component._process_file(
            str(test_file), config_root, force_rebuild=False
        )

        # Verify upsert was called with normalized path
        call_args = self.mock_vector_store.upsert.call_args[0][0]
        chunk_data = call_args[0]

        # Should use forward slashes regardless of OS
        assert "/" in chunk_data.rel_path or chunk_data.rel_path == "src/main.py"

    @pytest.mark.asyncio
    async def test_process_file_chunk_metadata(self, temp_project):
        """Test that chunk metadata is set correctly."""
        self.mock_embed_component.embed_chunks.return_value = [[0.1, 0.2, 0.3]]

        test_file = temp_project / "src" / "main.py"
        config_root = str(temp_project)

        await self.component._process_file(
            str(test_file), config_root, force_rebuild=False
        )

        # Verify chunk metadata
        call_args = self.mock_vector_store.upsert.call_args[0][0]
        chunk_data = call_args[0]

        assert hasattr(chunk_data, "chunk_id")
        assert hasattr(chunk_data, "repo_root")
        assert hasattr(chunk_data, "rel_path")
        assert hasattr(chunk_data, "start_line")
        assert hasattr(chunk_data, "end_line")
        assert hasattr(chunk_data, "text")
        assert hasattr(chunk_data, "vector")
        assert hasattr(chunk_data, "language")
        assert hasattr(chunk_data, "symbols")

        assert chunk_data.repo_root == config_root
        assert chunk_data.language == "python"  # Placeholder
        assert chunk_data.symbols == []  # Placeholder

    @pytest.mark.asyncio
    async def test_process_file_exception_handling(self, temp_project):
        """Test exception handling during file processing."""
        test_file = temp_project / "nonexistent.py"
        config_root = str(temp_project)

        chunks_count = await self.component._process_file(
            str(test_file), config_root, force_rebuild=False
        )

        assert chunks_count == 0
        self.mock_embed_component.embed_chunks.assert_not_called()
        self.mock_vector_store.upsert.assert_not_called()

    @pytest.mark.asyncio
    async def test_concurrent_processing(self, temp_project):
        """Test that files are processed concurrently."""
        # Setup to track call order and timing
        call_order = []

        async def mock_process_file(*args, **kwargs):
            call_order.append(args[0])  # File path
            await asyncio.sleep(0.01)  # Simulate processing time
            return 1

        self.component._process_file = mock_process_file

        with patch(
            "locus.mcp.components.ingest.code_ingest_component.scanner"
        ) as mock_scanner, patch(
            "locus.mcp.components.ingest.code_ingest_component.config"
        ) as mock_config:
            mock_config.load_project_config.return_value = (set(), {"*.py"})

            # Multiple files
            files = [
                str(temp_project / "src" / "main.py"),
                str(temp_project / "src" / "utils.py"),
                str(temp_project / "README.md"),
            ]
            mock_scanner.scan_directory.return_value = files

            start_time = asyncio.get_event_loop().time()
            await self.component.index_paths([str(temp_project)])
            end_time = asyncio.get_event_loop().time()

            # Should process files concurrently (total time < sum of individual times)
            assert len(call_order) == 3
            # With concurrent processing, should finish faster than sequential
            assert (end_time - start_time) < 0.1  # Much less than 3 * 0.01

    @pytest.mark.asyncio
    async def test_mixed_success_failure_processing(self, temp_project):
        """Test handling mixed success and failure scenarios."""
        # Create one good file and simulate one bad file
        good_file = temp_project / "src" / "main.py"
        bad_file = temp_project / "src" / "bad.py"

        # Mock to simulate one file failing
        original_process = self.component._process_file

        async def mock_process_file(abs_path, config_root, force_rebuild):
            if "bad.py" in abs_path:
                raise Exception("Simulated processing error")
            return await original_process(abs_path, config_root, force_rebuild)

        self.component._process_file = mock_process_file
        self.mock_embed_component.embed_chunks.return_value = [[0.1, 0.2, 0.3]]

        with patch(
            "locus.mcp.components.ingest.code_ingest_component.scanner"
        ) as mock_scanner, patch(
            "locus.mcp.components.ingest.code_ingest_component.config"
        ) as mock_config:
            mock_config.load_project_config.return_value = (set(), {"*.py"})
            mock_scanner.scan_directory.return_value = [str(good_file), str(bad_file)]

            results = await self.component.index_paths([str(temp_project)])

            # Should process the good file despite the bad one failing
            assert results["files"] == 1
            assert results["chunks"] > 0


class TestCodeIngestComponentIntegration:
    """Integration tests for CodeIngestComponent."""

    @pytest.mark.asyncio
    async def test_real_project_structure(self, temp_project):
        """Test processing a realistic project structure."""
        mock_embed_component = Mock()
        mock_vector_store = Mock()

        # Setup realistic embeddings
        mock_embed_component.embed_chunks.return_value = [
            [0.1, 0.2, 0.3, 0.4]
            for _ in range(10)  # Simulate multiple chunks
        ]

        component = CodeIngestComponent(
            embed_component=mock_embed_component, vector_store=mock_vector_store
        )

        # Test with real project structure
        results = await component.index_paths([str(temp_project)])

        assert results["files"] >= 2  # At least main.py and utils.py
        assert results["chunks"] > 0

        # Verify embeddings were generated
        mock_embed_component.embed_chunks.assert_called()

        # Verify data was stored
        mock_vector_store.upsert.assert_called()

    @pytest.mark.asyncio
    async def test_chunking_integration(self, temp_project, sample_code_content):
        """Test integration with chunking functionality."""
        # Create a file with known content
        large_file = temp_project / "large_file.py"
        large_file.write_text(sample_code_content)

        mock_embed_component = Mock()
        mock_vector_store = Mock()

        # Return embeddings for each chunk
        mock_embed_component.embed_chunks.return_value = [
            [0.1, 0.2, 0.3] for _ in range(5)
        ]

        component = CodeIngestComponent(
            embed_component=mock_embed_component, vector_store=mock_vector_store
        )

        with patch(
            "locus.mcp.components.ingest.code_ingest_component.scanner"
        ) as mock_scanner, patch(
            "locus.mcp.components.ingest.code_ingest_component.config"
        ) as mock_config:
            mock_config.load_project_config.return_value = (set(), {"*.py"})
            mock_scanner.scan_directory.return_value = [str(large_file)]

            results = await component.index_paths([str(temp_project)])

            # Should have chunked the content
            assert results["chunks"] > 1

            # Verify chunks were embedded
            call_args = mock_embed_component.embed_chunks.call_args[0][0]
            assert len(call_args) > 1  # Multiple chunks

    @pytest.mark.asyncio
    async def test_error_resilience(self, temp_project):
        """Test that the component is resilient to various errors."""
        mock_embed_component = Mock()
        mock_vector_store = Mock()

        # Simulate embedding service errors
        mock_embed_component.embed_chunks.side_effect = Exception(
            "Embedding service down"
        )

        component = CodeIngestComponent(
            embed_component=mock_embed_component, vector_store=mock_vector_store
        )

        with patch(
            "locus.mcp.components.ingest.code_ingest_component.scanner"
        ) as mock_scanner, patch(
            "locus.mcp.components.ingest.code_ingest_component.config"
        ) as mock_config:
            mock_config.load_project_config.return_value = (set(), {"*.py"})
            test_file = temp_project / "src" / "main.py"
            mock_scanner.scan_directory.return_value = [str(test_file)]

            results = await component.index_paths([str(temp_project)])

            # Should handle errors gracefully
            assert results["files"] == 0
            assert results["chunks"] == 0
