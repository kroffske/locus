"""Integration tests for the complete MCP system."""
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from locus.mcp.di.container import get_container


class TestMCPFullWorkflow:
    """Test complete MCP workflow from indexing to search."""

    @pytest.mark.asyncio
    async def test_complete_indexing_and_search_workflow(self, temp_project, mock_sentence_transformers, mock_lancedb):
        """Test the complete workflow: index files -> search -> retrieve context."""
        with patch('locus.mcp.components.embedding.embedding_component.SentenceTransformer', return_value=mock_sentence_transformers), \
             patch('lancedb.connect', return_value=mock_lancedb), \
             patch('lancedb.pydantic.LanceModel'), \
             patch('lancedb.pydantic.Vector'):

            # Setup embeddings mock to return consistent vectors
            mock_sentence_transformers.encode.return_value.tolist.return_value = [
                [0.1, 0.2, 0.3, 0.4],  # For first chunk
                [0.5, 0.6, 0.7, 0.8],  # For second chunk
            ]

            # Setup vector store mock
            mock_table = MagicMock()
            mock_lancedb.create_table.return_value = mock_table
            mock_lancedb.open_table.return_value = mock_table

            # Mock search results
            mock_search_result = MagicMock()
            mock_search_result.limit.return_value.to_list.return_value = [
                {
                    'chunk_id': 'test-chunk-1',
                    'rel_path': 'src/main.py',
                    'text': 'def hello_world():\n    return "Hello, World!"',
                    'start_line': 1,
                    'end_line': 2,
                    '_distance': 0.1
                }
            ]
            mock_table.search.return_value = mock_search_result

            container = get_container()

            # 1. Index the project
            ingest_component = container.ingest_component()
            index_results = await ingest_component.index_paths([str(temp_project)])

            assert index_results['files'] > 0
            assert index_results['chunks'] > 0

            # Verify indexing called the right components
            mock_sentence_transformers.encode.assert_called()
            mock_table.add.assert_called()

            # 2. Search for code
            search_engine = container.code_search_engine()
            search_results = search_engine.search("hello function", k=5)

            assert len(search_results) > 0
            assert search_results[0]['rel_path'] == 'src/main.py'

            # Verify search used embeddings and vector store
            mock_table.search.assert_called()

    @pytest.mark.asyncio
    async def test_mcp_server_tools_integration(self, temp_project, mock_sentence_transformers, mock_lancedb, mock_fastmcp):
        """Test integration of MCP server tools."""
        with patch('locus.mcp.components.embedding.embedding_component.SentenceTransformer', return_value=mock_sentence_transformers), \
             patch('lancedb.connect', return_value=mock_lancedb), \
             patch('lancedb.pydantic.LanceModel'), \
             patch('lancedb.pydantic.Vector'), \
             patch('fastmcp.FastMCP', return_value=mock_fastmcp), \
             patch('os.getcwd', return_value=str(temp_project)):

            from locus.mcp.server.tools.index_control import index_paths
            from locus.mcp.server.tools.search_codebase import search_codebase
            from locus.mcp.server.tools.get_file_context import get_file_context

            # Setup mocks
            mock_sentence_transformers.encode.return_value.tolist.return_value = [[0.1, 0.2, 0.3]]
            mock_table = MagicMock()
            mock_lancedb.create_table.return_value = mock_table
            mock_lancedb.open_table.return_value = mock_table

            # Mock search results
            mock_search_result = MagicMock()
            mock_search_result.limit.return_value.to_list.return_value = [
                {
                    'chunk_id': 'test-chunk',
                    'rel_path': 'src/main.py',
                    'text': 'def hello_world(): pass',
                    'start_line': 1,
                    'end_line': 1,
                    '_distance': 0.05
                }
            ]
            mock_table.search.return_value = mock_search_result

            # 1. Test indexing tool
            index_results = await index_paths([str(temp_project)])
            assert len(index_results) == 1
            assert "Indexing complete" in index_results[0]["text"]

            # 2. Test search tool
            search_results = search_codebase("hello function")
            assert len(search_results) > 0

            # 3. Test file context tool
            with patch('locus.mcp.server.tools.get_file_context.analyze') as mock_analyze:
                mock_analyze.return_value = [{"text": "File content"}]
                context_results = get_file_context("src/main.py")
                assert len(context_results) > 0

    def test_mcp_app_creation_and_registration(self, mock_fastmcp):
        """Test that MCP app is created and tools are registered correctly."""
        with patch('fastmcp.FastMCP', return_value=mock_fastmcp):
            from locus.mcp.server.mcp_app import get_mcp_app

            app = get_mcp_app()

            # Verify app was created
            assert app is mock_fastmcp

            # Verify tools were registered (via decorator calls)
            assert mock_fastmcp.tool.call_count >= 3  # At least 3 tools registered

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, temp_project, mock_sentence_transformers, mock_lancedb):
        """Test that concurrent MCP operations work correctly."""
        with patch('locus.mcp.components.embedding.embedding_component.SentenceTransformer', return_value=mock_sentence_transformers), \
             patch('lancedb.connect', return_value=mock_lancedb), \
             patch('lancedb.pydantic.LanceModel'), \
             patch('lancedb.pydantic.Vector'):

            # Setup mocks
            mock_sentence_transformers.encode.return_value.tolist.return_value = [[0.1, 0.2, 0.3]]
            mock_table = MagicMock()
            mock_lancedb.create_table.return_value = mock_table
            mock_lancedb.open_table.return_value = mock_table

            container = get_container()
            ingest_component = container.ingest_component()

            # Create multiple indexing tasks
            tasks = []
            for i in range(3):
                task = ingest_component.index_paths([str(temp_project)])
                tasks.append(task)

            # Run concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # All tasks should complete successfully
            assert len(results) == 3
            for result in results:
                assert not isinstance(result, Exception)
                assert result['files'] >= 0

    def test_error_handling_integration(self, temp_project):
        """Test error handling across the entire MCP system."""
        # Test with missing dependencies
        with patch('locus.mcp.components.embedding.embedding_component.SentenceTransformer', side_effect=ImportError("Missing package")):
            container = get_container()

            with pytest.raises(ImportError, match="Missing package"):
                container.embedding_component()

        # Test with vector store errors
        with patch('lancedb.connect', side_effect=Exception("DB connection failed")):
            container = get_container()

            with pytest.raises(Exception, match="DB connection failed"):
                container.vector_store()

    @pytest.mark.asyncio
    async def test_large_project_indexing(self, temp_project, mock_sentence_transformers, mock_lancedb):
        """Test indexing a project with many files."""
        with patch('locus.mcp.components.embedding.embedding_component.SentenceTransformer', return_value=mock_sentence_transformers), \
             patch('lancedb.connect', return_value=mock_lancedb), \
             patch('lancedb.pydantic.LanceModel'), \
             patch('lancedb.pydantic.Vector'):

            # Create many test files
            src_dir = temp_project / "large_src"
            src_dir.mkdir()

            for i in range(50):
                file_path = src_dir / f"module_{i}.py"
                file_path.write_text(f"""
def function_{i}():
    '''Function number {i}'''
    return {i}

class Class_{i}:
    def method_{i}(self):
        return "method_{i}"
""")

            # Mock embeddings for many chunks
            mock_sentence_transformers.encode.return_value.tolist.return_value = [
                [float(i) / 100, float(i+1) / 100, float(i+2) / 100] for i in range(200)
            ]

            mock_table = MagicMock()
            mock_lancedb.create_table.return_value = mock_table
            mock_lancedb.open_table.return_value = mock_table

            container = get_container()
            ingest_component = container.ingest_component()

            # Index the large project
            results = await ingest_component.index_paths([str(temp_project)])

            # Should handle many files
            assert results['files'] >= 50
            assert results['chunks'] > 100

    def test_configuration_integration(self):
        """Test that configuration is properly integrated across components."""
        container = get_container()
        settings = container.settings

        # Verify settings structure
        assert hasattr(settings, 'embedding')
        assert hasattr(settings, 'vector_store')
        assert hasattr(settings, 'index')

        # Verify default values
        assert settings.embedding.provider == "huggingface"
        assert settings.vector_store.provider == "lancedb"
        assert settings.index.chunking_strategy in ["lines", "semantic"]

    @pytest.mark.asyncio
    async def test_chunking_strategy_integration(self, temp_project, sample_code_content, mock_sentence_transformers, mock_lancedb):
        """Test different chunking strategies in the full workflow."""
        with patch('locus.mcp.components.embedding.embedding_component.SentenceTransformer', return_value=mock_sentence_transformers), \
             patch('lancedb.connect', return_value=mock_lancedb), \
             patch('lancedb.pydantic.LanceModel'), \
             patch('lancedb.pydantic.Vector'):

            # Create a file with known content
            test_file = temp_project / "test_chunking.py"
            test_file.write_text(sample_code_content)

            mock_sentence_transformers.encode.return_value.tolist.return_value = [
                [0.1, 0.2, 0.3] for _ in range(10)  # Embeddings for chunks
            ]

            mock_table = MagicMock()
            mock_lancedb.create_table.return_value = mock_table
            mock_lancedb.open_table.return_value = mock_table

            container = get_container()
            ingest_component = container.ingest_component()

            # Test with lines strategy (default)
            results_lines = await ingest_component.index_paths([str(temp_project)])
            lines_chunks = results_lines['chunks']

            # Test with semantic strategy
            # (Note: This would require modifying settings or passing strategy parameter)
            # For now, we just verify the chunking works
            assert lines_chunks > 0

    def test_security_features_integration(self, temp_project):
        """Test security features across the MCP system."""
        with patch('os.getcwd', return_value=str(temp_project)):
            from locus.mcp.server.tools.get_file_context import get_file_context

            # Test path traversal protection
            dangerous_paths = [
                "../../etc/passwd",
                "../../../sensitive_file",
                "/etc/shadow",
                "C:\\Windows\\System32\\config"
            ]

            for path in dangerous_paths:
                result = get_file_context(path)
                assert len(result) == 1
                assert "Error: Invalid path" in result[0].text

    @pytest.mark.asyncio
    async def test_performance_characteristics(self, temp_project, mock_sentence_transformers, mock_lancedb):
        """Test performance characteristics of the MCP system."""
        with patch('locus.mcp.components.embedding.embedding_component.SentenceTransformer', return_value=mock_sentence_transformers), \
             patch('lancedb.connect', return_value=mock_lancedb), \
             patch('lancedb.pydantic.LanceModel'), \
             patch('lancedb.pydantic.Vector'):

            import time

            # Setup mocks
            mock_sentence_transformers.encode.return_value.tolist.return_value = [[0.1, 0.2, 0.3]]
            mock_table = MagicMock()
            mock_lancedb.create_table.return_value = mock_table
            mock_lancedb.open_table.return_value = mock_table

            container = get_container()
            ingest_component = container.ingest_component()

            # Measure indexing time
            start_time = time.time()
            await ingest_component.index_paths([str(temp_project)])
            indexing_time = time.time() - start_time

            # Should complete reasonably quickly (even with mocks)
            assert indexing_time < 5.0  # 5 seconds should be plenty for test project

            # Measure search time
            search_engine = container.code_search_engine()

            start_time = time.time()
            search_engine.search("test query")
            search_time = time.time() - start_time

            # Search should be fast
            assert search_time < 1.0  # 1 second should be plenty

    def test_dependency_injection_integration(self):
        """Test that dependency injection works correctly across all components."""
        container = get_container()

        # Get all components
        embedding_comp = container.embedding_component()
        vector_store = container.vector_store()
        ingest_comp = container.ingest_component()
        search_engine = container.code_search_engine()

        # Verify components are properly wired
        assert ingest_comp.embed_component is embedding_comp
        assert ingest_comp.vector_store is vector_store
        assert search_engine.embedding_component is embedding_comp
        assert search_engine.vector_store is vector_store

        # Verify singleton behavior
        embedding_comp2 = container.embedding_component()
        assert embedding_comp is embedding_comp2


class TestMCPSystemResilience:
    """Test system resilience and recovery."""

    @pytest.mark.asyncio
    async def test_partial_failure_recovery(self, temp_project, mock_sentence_transformers, mock_lancedb):
        """Test system recovery from partial failures."""
        with patch('locus.mcp.components.embedding.embedding_component.SentenceTransformer', return_value=mock_sentence_transformers), \
             patch('lancedb.connect', return_value=mock_lancedb), \
             patch('lancedb.pydantic.LanceModel'), \
             patch('lancedb.pydantic.Vector'):

            # Create some files, make one fail
            failing_file = temp_project / "failing.py"
            failing_file.write_text("# This file will cause issues")

            # Make file reading fail for this specific file
            original_open = open

            def mock_open(path, *args, **kwargs):
                if "failing.py" in str(path):
                    raise PermissionError("Access denied")
                return original_open(path, *args, **kwargs)

            mock_sentence_transformers.encode.return_value.tolist.return_value = [[0.1, 0.2, 0.3]]
            mock_table = MagicMock()
            mock_lancedb.create_table.return_value = mock_table
            mock_lancedb.open_table.return_value = mock_table

            container = get_container()
            ingest_component = container.ingest_component()

            with patch('builtins.open', side_effect=mock_open):
                # Should still process other files despite one failing
                results = await ingest_component.index_paths([str(temp_project)])

                # Should have processed some files (the good ones)
                assert results['files'] > 0

    def test_graceful_degradation(self, temp_project):
        """Test graceful degradation when optional features fail."""
        # Test what happens when search engine fails but other components work
        with patch('locus.search.engine.HybridSearchEngine', side_effect=Exception("Search engine failed")):
            container = get_container()

            # Other components should still work
            embedding_comp = container.embedding_component()
            vector_store = container.vector_store()

            assert embedding_comp is not None
            assert vector_store is not None

            # But search engine should fail
            with pytest.raises(Exception, match="Search engine failed"):
                container.code_search_engine()

    def test_resource_cleanup(self, temp_project, mock_sentence_transformers, mock_lancedb):
        """Test that resources are properly cleaned up."""
        with patch('locus.mcp.components.embedding.embedding_component.SentenceTransformer', return_value=mock_sentence_transformers), \
             patch('lancedb.connect', return_value=mock_lancedb), \
             patch('lancedb.pydantic.LanceModel'), \
             patch('lancedb.pydantic.Vector'):

            mock_table = MagicMock()
            mock_lancedb.create_table.return_value = mock_table
            mock_lancedb.open_table.return_value = mock_table

            container = get_container()

            # Create and use components
            embedding_comp = container.embedding_component()
            vector_store = container.vector_store()

            # Simulate cleanup (if implemented)
            # In a real system, you might have cleanup methods
            del embedding_comp
            del vector_store

            # System should still be able to create new instances
            new_embedding = container.embedding_component()
            assert new_embedding is not None