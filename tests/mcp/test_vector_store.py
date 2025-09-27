"""Tests for vector store component functionality."""
import pytest
from unittest.mock import patch, MagicMock
from locus.mcp.components.vector_store.lancedb_store import LanceDBVectorStore, CodeChunkModel


class TestCodeChunkModel:
    """Test the CodeChunkModel placeholder."""

    def test_code_chunk_model_exists(self):
        """Test that CodeChunkModel is defined."""
        assert CodeChunkModel is not None


class TestLanceDBVectorStore:
    """Test the LanceDBVectorStore class."""

    def test_init_success(self, mock_lancedb, temp_db_path):
        """Test successful initialization with mocked LanceDB."""
        with patch('lancedb.pydantic.LanceModel'), \
             patch('lancedb.pydantic.Vector'):

            store = LanceDBVectorStore(temp_db_path, "test_table")

            assert store.db_path == temp_db_path
            assert store.table_name == "test_table"
            mock_lancedb.assert_called_once_with(temp_db_path)

    def test_init_missing_dependency(self, temp_db_path):
        """Test initialization fails when LanceDB is not available."""
        with patch('lancedb.connect', side_effect=ImportError):
            with pytest.raises(ImportError, match="LanceDB is not installed"):
                LanceDBVectorStore(temp_db_path)

    def test_default_table_name(self, mock_lancedb, temp_db_path):
        """Test that default table name is used."""
        with patch('lancedb.pydantic.LanceModel'), \
             patch('lancedb.pydantic.Vector'):

            store = LanceDBVectorStore(temp_db_path)
            assert store.table_name == "code_chunks"

    def test_upsert_creates_table_if_not_exists(self, mock_lancedb, temp_db_path):
        """Test that upsert creates table if it doesn't exist."""
        with patch('lancedb.pydantic.LanceModel'), \
             patch('lancedb.pydantic.Vector'):

            # Mock table not existing
            mock_lancedb.open_table.side_effect = FileNotFoundError()

            store = LanceDBVectorStore(temp_db_path, "test_table")

            sample_data = [
                {
                    'chunk_id': 'chunk1',
                    'repo_root': '/test',
                    'rel_path': 'test.py',
                    'start_line': 1,
                    'end_line': 10,
                    'text': 'test code',
                    'vector': [0.1, 0.2, 0.3],
                    'language': 'python',
                    'symbols': ['test_func']
                }
            ]

            store.upsert(sample_data)

            # Should create table
            mock_lancedb.create_table.assert_called_once()

    def test_upsert_uses_existing_table(self, mock_lancedb, temp_db_path):
        """Test that upsert uses existing table when available."""
        with patch('lancedb.pydantic.LanceModel'), \
             patch('lancedb.pydantic.Vector'):

            mock_table = MagicMock()
            mock_lancedb.open_table.return_value = mock_table

            store = LanceDBVectorStore(temp_db_path, "test_table")

            sample_data = [
                {
                    'chunk_id': 'chunk1',
                    'repo_root': '/test',
                    'rel_path': 'test.py',
                    'start_line': 1,
                    'end_line': 10,
                    'text': 'test code',
                    'vector': [0.1, 0.2, 0.3],
                    'language': 'python',
                    'symbols': ['test_func']
                }
            ]

            store.upsert(sample_data)

            # Should use existing table
            mock_lancedb.open_table.assert_called_once_with("test_table")
            mock_table.add.assert_called_once()

    def test_upsert_empty_data(self, mock_lancedb, temp_db_path):
        """Test upserting empty data list."""
        with patch('lancedb.pydantic.LanceModel'), \
             patch('lancedb.pydantic.Vector'):

            mock_table = MagicMock()
            mock_lancedb.open_table.return_value = mock_table

            store = LanceDBVectorStore(temp_db_path)
            store.upsert([])

            # Should not call add with empty data
            mock_table.add.assert_not_called()

    def test_search_basic(self, mock_lancedb, temp_db_path):
        """Test basic search functionality."""
        with patch('lancedb.pydantic.LanceModel'), \
             patch('lancedb.pydantic.Vector'):

            mock_table = MagicMock()
            mock_search_result = MagicMock()
            mock_search_result.limit.return_value.where.return_value.to_list.return_value = [
                {
                    'chunk_id': 'chunk1',
                    'rel_path': 'test.py',
                    'text': 'test function',
                    'start_line': 1,
                    'end_line': 5,
                    '_distance': 0.1
                }
            ]
            mock_table.search.return_value = mock_search_result
            mock_lancedb.open_table.return_value = mock_table

            store = LanceDBVectorStore(temp_db_path)
            query_vector = [0.1, 0.2, 0.3]

            results = store.search(query_vector, k=5)

            assert len(results) == 1
            assert results[0]['chunk_id'] == 'chunk1'
            assert results[0]['rel_path'] == 'test.py'

            mock_table.search.assert_called_once_with(query_vector)
            mock_search_result.limit.assert_called_once_with(5)

    def test_search_with_where_clause(self, mock_lancedb, temp_db_path):
        """Test search with where clause filtering."""
        with patch('lancedb.pydantic.LanceModel'), \
             patch('lancedb.pydantic.Vector'):

            mock_table = MagicMock()
            mock_search_result = MagicMock()
            mock_search_result.limit.return_value.where.return_value.to_list.return_value = []
            mock_table.search.return_value = mock_search_result
            mock_lancedb.open_table.return_value = mock_table

            store = LanceDBVectorStore(temp_db_path)
            query_vector = [0.1, 0.2, 0.3]

            store.search(query_vector, k=10, where="rel_path LIKE '%.py'")

            mock_search_result.limit.return_value.where.assert_called_once_with("rel_path LIKE '%.py'")

    def test_search_no_where_clause(self, mock_lancedb, temp_db_path):
        """Test search without where clause."""
        with patch('lancedb.pydantic.LanceModel'), \
             patch('lancedb.pydantic.Vector'):

            mock_table = MagicMock()
            mock_search_result = MagicMock()
            mock_search_result.limit.return_value.to_list.return_value = []
            mock_table.search.return_value = mock_search_result
            mock_lancedb.open_table.return_value = mock_table

            store = LanceDBVectorStore(temp_db_path)
            query_vector = [0.1, 0.2, 0.3]

            store.search(query_vector, k=10)

            # Should not call where when no clause provided
            mock_search_result.limit.return_value.where.assert_not_called()
            mock_search_result.limit.return_value.to_list.assert_called_once()

    def test_search_table_not_found(self, mock_lancedb, temp_db_path):
        """Test search when table doesn't exist."""
        with patch('lancedb.pydantic.LanceModel'), \
             patch('lancedb.pydantic.Vector'):

            mock_lancedb.open_table.side_effect = FileNotFoundError()

            store = LanceDBVectorStore(temp_db_path)
            query_vector = [0.1, 0.2, 0.3]

            results = store.search(query_vector)

            assert results == []

    def test_delete_by_file(self, mock_lancedb, temp_db_path):
        """Test deleting entries by file path."""
        with patch('lancedb.pydantic.LanceModel'), \
             patch('lancedb.pydantic.Vector'):

            mock_table = MagicMock()
            mock_lancedb.open_table.return_value = mock_table

            store = LanceDBVectorStore(temp_db_path)
            store.delete_by_file("test/file.py")

            mock_table.delete.assert_called_once_with("rel_path = 'test/file.py'")

    def test_delete_by_file_table_not_found(self, mock_lancedb, temp_db_path):
        """Test delete by file when table doesn't exist."""
        with patch('lancedb.pydantic.LanceModel'), \
             patch('lancedb.pydantic.Vector'):

            mock_lancedb.open_table.side_effect = FileNotFoundError()

            store = LanceDBVectorStore(temp_db_path)

            # Should not raise error when table doesn't exist
            store.delete_by_file("nonexistent/file.py")

    def test_get_table_creates_if_needed(self, mock_lancedb, temp_db_path):
        """Test that get_table creates table if it doesn't exist."""
        with patch('lancedb.pydantic.LanceModel'), \
             patch('lancedb.pydantic.Vector'):

            mock_lancedb.open_table.side_effect = FileNotFoundError()

            store = LanceDBVectorStore(temp_db_path, "new_table")
            table = store._get_table()

            # Should create table when it doesn't exist
            mock_lancedb.create_table.assert_called_once()
            assert table is not None

    def test_data_validation(self, mock_lancedb, temp_db_path):
        """Test that data is properly formatted for LanceDB."""
        with patch('lancedb.pydantic.LanceModel'), \
             patch('lancedb.pydantic.Vector'):

            mock_table = MagicMock()
            mock_lancedb.open_table.return_value = mock_table

            store = LanceDBVectorStore(temp_db_path)

            # Test with CodeChunkModel-like objects
            from types import SimpleNamespace
            chunk_objects = [
                SimpleNamespace(
                    chunk_id='chunk1',
                    repo_root='/test',
                    rel_path='test.py',
                    start_line=1,
                    end_line=10,
                    text='test code',
                    vector=[0.1, 0.2, 0.3],
                    language='python',
                    symbols=['test_func']
                )
            ]

            store.upsert(chunk_objects)

            # Should convert objects to dicts for LanceDB
            mock_table.add.assert_called_once()
            call_args = mock_table.add.call_args[0][0]
            assert isinstance(call_args, list)

    def test_multiple_operations_reuse_connection(self, mock_lancedb, temp_db_path):
        """Test that multiple operations reuse the same database connection."""
        with patch('lancedb.pydantic.LanceModel'), \
             patch('lancedb.pydantic.Vector'):

            mock_table = MagicMock()
            mock_lancedb.open_table.return_value = mock_table

            store = LanceDBVectorStore(temp_db_path)

            # Perform multiple operations
            store.search([0.1, 0.2, 0.3])
            store.upsert([{'chunk_id': 'test', 'vector': [0.1, 0.2]}])
            store.delete_by_file("test.py")

            # DB should be connected only once
            mock_lancedb.assert_called_once_with(temp_db_path)


class TestLanceDBVectorStoreIntegration:
    """Integration tests for LanceDBVectorStore."""

    def test_full_workflow(self, mock_lancedb, temp_db_path):
        """Test a complete workflow of upsert, search, and delete."""
        with patch('lancedb.pydantic.LanceModel'), \
             patch('lancedb.pydantic.Vector'):

            # Setup mocks
            mock_table = MagicMock()
            mock_search_result = MagicMock()
            mock_search_result.limit.return_value.to_list.return_value = [
                {
                    'chunk_id': 'chunk1',
                    'rel_path': 'test.py',
                    'text': 'def test(): pass',
                    'start_line': 1,
                    'end_line': 1,
                    '_distance': 0.05
                }
            ]
            mock_table.search.return_value = mock_search_result
            mock_lancedb.open_table.return_value = mock_table

            store = LanceDBVectorStore(temp_db_path)

            # 1. Upsert data
            test_data = [
                {
                    'chunk_id': 'chunk1',
                    'repo_root': '/project',
                    'rel_path': 'test.py',
                    'start_line': 1,
                    'end_line': 1,
                    'text': 'def test(): pass',
                    'vector': [0.1, 0.2, 0.3],
                    'language': 'python',
                    'symbols': ['test']
                }
            ]
            store.upsert(test_data)

            # 2. Search for similar content
            results = store.search([0.1, 0.2, 0.3], k=5)
            assert len(results) == 1
            assert results[0]['chunk_id'] == 'chunk1'

            # 3. Delete by file
            store.delete_by_file('test.py')

            # Verify all operations were called
            mock_table.add.assert_called_once()
            mock_table.search.assert_called_once()
            mock_table.delete.assert_called_once()

    def test_error_handling_resilience(self, mock_lancedb, temp_db_path):
        """Test that the store handles various error conditions gracefully."""
        with patch('lancedb.pydantic.LanceModel'), \
             patch('lancedb.pydantic.Vector'):

            # Test with database connection errors
            mock_lancedb.side_effect = Exception("Connection failed")

            with pytest.raises(Exception, match="Connection failed"):
                LanceDBVectorStore(temp_db_path)

    def test_large_batch_operations(self, mock_lancedb, temp_db_path):
        """Test handling of large batch operations."""
        with patch('lancedb.pydantic.LanceModel'), \
             patch('lancedb.pydantic.Vector'):

            mock_table = MagicMock()
            mock_lancedb.open_table.return_value = mock_table

            store = LanceDBVectorStore(temp_db_path)

            # Large batch of data
            large_batch = []
            for i in range(1000):
                large_batch.append({
                    'chunk_id': f'chunk{i}',
                    'repo_root': '/project',
                    'rel_path': f'file{i}.py',
                    'start_line': 1,
                    'end_line': 10,
                    'text': f'function_{i}',
                    'vector': [0.1 * i, 0.2 * i, 0.3 * i],
                    'language': 'python',
                    'symbols': [f'func_{i}']
                })

            store.upsert(large_batch)

            # Should handle large batch
            mock_table.add.assert_called_once()
            call_args = mock_table.add.call_args[0][0]
            assert len(call_args) == 1000