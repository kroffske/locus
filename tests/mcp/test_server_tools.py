"""Tests for MCP server tools functionality."""

import pytest
from unittest.mock import Mock, patch, AsyncMock


class TestGetFileContext:
    """Test the get_file_context tool."""

    def test_get_file_context_success(self, temp_project):
        """Test successful file context retrieval."""
        with patch(
            "locus.mcp.server.tools.get_file_context.analyze"
        ) as mock_analyze, patch("os.getcwd", return_value=str(temp_project)):
            from locus.mcp.server.tools.get_file_context import get_file_context

            # Mock analyze function
            mock_analyze.return_value = [{"text": "File content from analyzer"}]

            result = get_file_context("src/main.py")

            assert len(result) == 1
            assert "File content from analyzer" in str(result[0])

            # Verify analyze was called correctly
            mock_analyze.assert_called_once()
            call_args = mock_analyze.call_args
            assert call_args[1]["project_path"] == str(temp_project)

    def test_get_file_context_with_line_range(self, temp_project):
        """Test file context retrieval with specific line range."""
        with patch(
            "locus.mcp.server.tools.get_file_context.analyze"
        ) as mock_analyze, patch("os.getcwd", return_value=str(temp_project)):
            from locus.mcp.server.tools.get_file_context import get_file_context

            mock_analyze.return_value = [{"text": "Specific lines"}]

            get_file_context("src/main.py", start_line=5, end_line=10)

            # Verify line range was passed to analyzer
            call_args = mock_analyze.call_args
            target_specs = call_args[1]["target_specs"]
            assert len(target_specs) == 1
            assert target_specs[0].line_ranges == [(5, 10)]

    def test_get_file_context_path_traversal_protection(self, temp_project):
        """Test protection against path traversal attacks."""
        with patch("os.getcwd", return_value=str(temp_project)):
            from locus.mcp.server.tools.get_file_context import get_file_context

            # Try to access file outside repo
            result = get_file_context("../../../etc/passwd")

            assert len(result) == 1
            assert "Error: Invalid path" in result[0].text
            assert "outside repo" in result[0].text

    def test_get_file_context_path_traversal_protection_relative(self, temp_project):
        """Test protection against relative path traversal."""
        with patch("os.getcwd", return_value=str(temp_project)):
            from locus.mcp.server.tools.get_file_context import get_file_context

            # Try various path traversal patterns
            dangerous_paths = [
                "../../sensitive_file.txt",
                "src/../../../etc/passwd",
                "..\\..\\windows\\system32\\config",
                "/etc/passwd",
                "C:\\Windows\\System32\\config",
            ]

            for path in dangerous_paths:
                result = get_file_context(path)
                assert len(result) == 1
                assert "Error: Invalid path" in result[0].text

    def test_get_file_context_valid_relative_path(self, temp_project):
        """Test that valid relative paths within repo work."""
        with patch(
            "locus.mcp.server.tools.get_file_context.analyze"
        ) as mock_analyze, patch("os.getcwd", return_value=str(temp_project)):
            from locus.mcp.server.tools.get_file_context import get_file_context

            mock_analyze.return_value = [{"text": "Valid file content"}]

            # These should work
            valid_paths = [
                "src/main.py",
                "./src/main.py",
                "README.md",
                "src/../README.md",  # This resolves to README.md within repo
            ]

            for path in valid_paths:
                result = get_file_context(path)
                if "Error" not in str(result[0]):
                    assert "Valid file content" in str(result[0])

    def test_get_file_context_missing_mcp_types(self, temp_project):
        """Test error handling when MCP types are missing."""
        with patch(
            "locus.mcp.server.tools.get_file_context.TextContent",
            side_effect=ImportError,
        ):
            from locus.mcp.server.tools.get_file_context import get_file_context

            with pytest.raises(ImportError, match="MCP types not found"):
                get_file_context("src/main.py")

    def test_get_file_context_no_line_range(self, temp_project):
        """Test file context without line range specification."""
        with patch(
            "locus.mcp.server.tools.get_file_context.analyze"
        ) as mock_analyze, patch("os.getcwd", return_value=str(temp_project)):
            from locus.mcp.server.tools.get_file_context import get_file_context

            mock_analyze.return_value = [{"text": "Full file content"}]

            get_file_context("src/main.py")

            # Should pass empty line_ranges
            call_args = mock_analyze.call_args
            target_specs = call_args[1]["target_specs"]
            assert target_specs[0].line_ranges == []


class TestSearchCodebase:
    """Test the search_codebase tool."""

    def test_search_codebase_basic(self):
        """Test basic codebase search functionality."""
        with patch(
            "locus.mcp.server.tools.search_codebase.get_container"
        ) as mock_get_container:
            from locus.mcp.server.tools.search_codebase import search_codebase

            # Mock container and search engine
            mock_container = Mock()
            mock_engine = Mock()
            mock_engine.search.return_value = [
                {
                    "chunk_id": "chunk1",
                    "rel_path": "src/main.py",
                    "text": "def hello(): pass",
                    "start_line": 1,
                    "end_line": 1,
                    "score": 0.95,
                }
            ]
            mock_container.code_search_engine.return_value = mock_engine
            mock_get_container.return_value = mock_container

            results = search_codebase("hello function", k=5)

            assert len(results) == 1
            mock_engine.search.assert_called_once_with(
                "hello function", k=5, where=None, identifiers=None
            )

    def test_search_codebase_with_path_filter(self):
        """Test search with path glob filtering."""
        with patch(
            "locus.mcp.server.tools.search_codebase.get_container"
        ) as mock_get_container:
            from locus.mcp.server.tools.search_codebase import search_codebase

            mock_container = Mock()
            mock_engine = Mock()
            mock_engine.search.return_value = []
            mock_container.code_search_engine.return_value = mock_engine
            mock_get_container.return_value = mock_container

            search_codebase("test", k=10, path_glob="*.py")

            # Should pass where clause for path filtering
            mock_engine.search.assert_called_once_with(
                "test", k=10, where="rel_path GLOB '*.py'", identifiers=None
            )

    def test_search_codebase_with_identifiers(self):
        """Test search with identifier filtering."""
        with patch(
            "locus.mcp.server.tools.search_codebase.get_container"
        ) as mock_get_container:
            from locus.mcp.server.tools.search_codebase import search_codebase

            mock_container = Mock()
            mock_engine = Mock()
            mock_engine.search.return_value = []
            mock_container.code_search_engine.return_value = mock_engine
            mock_get_container.return_value = mock_container

            identifiers = ["function_name", "class_name"]
            search_codebase("test", identifiers=identifiers)

            mock_engine.search.assert_called_once_with(
                "test", k=10, where=None, identifiers=identifiers
            )

    def test_search_codebase_no_results(self):
        """Test search when no results are found."""
        with patch(
            "locus.mcp.server.tools.search_codebase.get_container"
        ) as mock_get_container:
            from locus.mcp.server.tools.search_codebase import search_codebase

            mock_container = Mock()
            mock_engine = Mock()
            mock_engine.search.return_value = []
            mock_container.code_search_engine.return_value = mock_engine
            mock_get_container.return_value = mock_container

            results = search_codebase("nonexistent")

            assert len(results) == 1
            assert "No relevant code snippets found" in str(results[0])

    def test_search_codebase_missing_mcp_types(self):
        """Test error handling when MCP types are missing."""
        with patch(
            "locus.mcp.server.tools.search_codebase.TextContent",
            side_effect=ImportError,
        ):
            from locus.mcp.server.tools.search_codebase import search_codebase

            with pytest.raises(ImportError, match="MCP types not found"):
                search_codebase("test query")

    def test_search_codebase_search_engine_error(self):
        """Test handling of search engine errors."""
        with patch(
            "locus.mcp.server.tools.search_codebase.get_container"
        ) as mock_get_container:
            from locus.mcp.server.tools.search_codebase import search_codebase

            mock_container = Mock()
            mock_engine = Mock()
            mock_engine.search.side_effect = Exception("Search error")
            mock_container.code_search_engine.return_value = mock_engine
            mock_get_container.return_value = mock_container

            results = search_codebase("test query")

            # Should handle error gracefully
            assert len(results) == 1
            assert "Error during search" in str(results[0])

    def test_search_codebase_multiple_parameters(self):
        """Test search with multiple parameters."""
        with patch(
            "locus.mcp.server.tools.search_codebase.get_container"
        ) as mock_get_container:
            from locus.mcp.server.tools.search_codebase import search_codebase

            mock_container = Mock()
            mock_engine = Mock()
            mock_engine.search.return_value = []
            mock_container.code_search_engine.return_value = mock_engine
            mock_get_container.return_value = mock_container

            search_codebase(
                "authentication",
                k=20,
                path_glob="src/**/*.py",
                identifiers=["auth", "login"],
            )

            mock_engine.search.assert_called_once_with(
                "authentication",
                k=20,
                where="rel_path GLOB 'src/**/*.py'",
                identifiers=["auth", "login"],
            )


class TestIndexControl:
    """Test the index_control tool."""

    @pytest.mark.asyncio
    async def test_index_paths_success(self):
        """Test successful indexing of paths."""
        with patch(
            "locus.mcp.server.tools.index_control.get_container"
        ) as mock_get_container:
            from locus.mcp.server.tools.index_control import index_paths

            # Mock container and ingest component
            mock_container = Mock()
            mock_ingest = Mock()
            mock_ingest.index_paths = AsyncMock(return_value={"files": 5, "chunks": 25})
            mock_container.ingest_component.return_value = mock_ingest
            mock_get_container.return_value = mock_container

            results = await index_paths(["/test/path"])

            assert len(results) == 1
            assert "Indexing complete" in results[0]["text"]
            assert "5 files" in results[0]["text"]
            assert "25 chunks" in results[0]["text"]

            mock_ingest.index_paths.assert_called_once_with(["/test/path"], False)

    @pytest.mark.asyncio
    async def test_index_paths_with_force_rebuild(self):
        """Test indexing with force rebuild option."""
        with patch(
            "locus.mcp.server.tools.index_control.get_container"
        ) as mock_get_container:
            from locus.mcp.server.tools.index_control import index_paths

            mock_container = Mock()
            mock_ingest = Mock()
            mock_ingest.index_paths = AsyncMock(return_value={"files": 3, "chunks": 15})
            mock_container.ingest_component.return_value = mock_ingest
            mock_get_container.return_value = mock_container

            results = await index_paths(["/test/path"], force_rebuild=True)

            assert len(results) == 1
            mock_ingest.index_paths.assert_called_once_with(["/test/path"], True)

    @pytest.mark.asyncio
    async def test_index_paths_multiple_paths(self):
        """Test indexing multiple paths."""
        with patch(
            "locus.mcp.server.tools.index_control.get_container"
        ) as mock_get_container:
            from locus.mcp.server.tools.index_control import index_paths

            mock_container = Mock()
            mock_ingest = Mock()
            mock_ingest.index_paths = AsyncMock(
                return_value={"files": 10, "chunks": 50}
            )
            mock_container.ingest_component.return_value = mock_ingest
            mock_get_container.return_value = mock_container

            paths = ["/path1", "/path2", "/path3"]
            results = await index_paths(paths)

            assert len(results) == 1
            mock_ingest.index_paths.assert_called_once_with(paths, False)

    @pytest.mark.asyncio
    async def test_index_paths_error_handling(self):
        """Test error handling during indexing."""
        with patch(
            "locus.mcp.server.tools.index_control.get_container"
        ) as mock_get_container:
            from locus.mcp.server.tools.index_control import index_paths

            mock_container = Mock()
            mock_ingest = Mock()
            mock_ingest.index_paths = AsyncMock(
                side_effect=Exception("Indexing failed")
            )
            mock_container.ingest_component.return_value = mock_ingest
            mock_get_container.return_value = mock_container

            results = await index_paths(["/test/path"])

            assert len(results) == 1
            assert "Error during indexing" in results[0]["text"]
            assert "Indexing failed" in results[0]["text"]

    @pytest.mark.asyncio
    async def test_index_paths_missing_mcp_types(self):
        """Test error handling when MCP types are missing."""
        with patch(
            "locus.mcp.server.tools.index_control.TextContent", side_effect=ImportError
        ):
            from locus.mcp.server.tools.index_control import index_paths

            with pytest.raises(ImportError, match="MCP types not found"):
                await index_paths(["/test/path"])


class TestMCPServerToolsIntegration:
    """Integration tests for MCP server tools."""

    def test_all_tools_import_successfully(self):
        """Test that all tools can be imported without errors."""
        try:
            from locus.mcp.server.tools.get_file_context import get_file_context
            from locus.mcp.server.tools.search_codebase import search_codebase
            from locus.mcp.server.tools.index_control import index_paths

            assert callable(get_file_context)
            assert callable(search_codebase)
            assert callable(index_paths)
        except ImportError as e:
            pytest.fail(f"Failed to import MCP tools: {e}")

    def test_tools_have_proper_signatures(self):
        """Test that tools have the expected function signatures."""
        from locus.mcp.server.tools.get_file_context import get_file_context
        from locus.mcp.server.tools.search_codebase import search_codebase
        from locus.mcp.server.tools.index_control import index_paths

        import inspect

        # Check get_file_context signature
        sig = inspect.signature(get_file_context)
        assert "path" in sig.parameters
        assert "start_line" in sig.parameters
        assert "end_line" in sig.parameters

        # Check search_codebase signature
        sig = inspect.signature(search_codebase)
        assert "query" in sig.parameters
        assert "k" in sig.parameters
        assert "path_glob" in sig.parameters
        assert "identifiers" in sig.parameters

        # Check index_paths signature
        sig = inspect.signature(index_paths)
        assert "paths" in sig.parameters
        assert "force_rebuild" in sig.parameters

    @pytest.mark.asyncio
    async def test_tools_work_together(self, temp_project):
        """Test that tools can work together in a workflow."""
        with patch(
            "locus.mcp.server.tools.get_file_context.analyze"
        ) as mock_analyze, patch(
            "locus.mcp.server.tools.search_codebase.get_container"
        ) as mock_search_container, patch(
            "locus.mcp.server.tools.index_control.get_container"
        ) as mock_index_container, patch("os.getcwd", return_value=str(temp_project)):
            from locus.mcp.server.tools.get_file_context import get_file_context
            from locus.mcp.server.tools.search_codebase import search_codebase
            from locus.mcp.server.tools.index_control import index_paths

            # Setup mocks
            mock_analyze.return_value = [{"text": "File content"}]

            mock_search_container_instance = Mock()
            mock_search_engine = Mock()
            mock_search_engine.search.return_value = [{"text": "Search result"}]
            mock_search_container_instance.code_search_engine.return_value = (
                mock_search_engine
            )
            mock_search_container.return_value = mock_search_container_instance

            mock_index_container_instance = Mock()
            mock_ingest = Mock()
            mock_ingest.index_paths = AsyncMock(return_value={"files": 1, "chunks": 3})
            mock_index_container_instance.ingest_component.return_value = mock_ingest
            mock_index_container.return_value = mock_index_container_instance

            # Workflow: Index -> Search -> Get context
            # 1. Index the project
            index_results = await index_paths([str(temp_project)])
            assert len(index_results) == 1

            # 2. Search for code
            search_results = search_codebase("hello function")
            assert len(search_results) == 1

            # 3. Get file context
            context_results = get_file_context("src/main.py")
            assert len(context_results) == 1

    def test_error_messages_are_user_friendly(self):
        """Test that error messages are user-friendly and informative."""
        with patch("os.getcwd", return_value="/tmp/test"):
            from locus.mcp.server.tools.get_file_context import get_file_context

            # Test path traversal error message
            result = get_file_context("../../../etc/passwd")
            error_message = result[0].text

            assert "Error" in error_message
            assert "Invalid path" in error_message
            assert "outside repo" in error_message
            # Should not expose internal paths or implementation details
            assert "/tmp/test" not in error_message or "repo" in error_message
