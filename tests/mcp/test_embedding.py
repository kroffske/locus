"""Tests for embedding component functionality."""

import pytest
from unittest.mock import patch
from locus.mcp.components.embedding.embedding_component import EmbeddingComponent


class TestEmbeddingComponent:
    """Test the EmbeddingComponent class."""

    def test_init_success(self, mock_sentence_transformers):
        """Test successful initialization with mocked SentenceTransformers."""
        component = EmbeddingComponent("test-model", trust_remote_code=True)

        assert component.model is mock_sentence_transformers
        assert (
            component.query_prefix
            == "Represent this query for searching relevant code: "
        )
        mock_sentence_transformers.assert_called_once()

    def test_init_missing_dependency(self):
        """Test initialization fails when SentenceTransformers is not available."""
        with patch(
            "locus.mcp.components.embedding.embedding_component.SentenceTransformer",
            side_effect=ImportError,
        ):
            with pytest.raises(
                ImportError, match="SentenceTransformers is not installed"
            ):
                EmbeddingComponent("test-model")

    def test_embed_chunks(self, mock_sentence_transformers):
        """Test embedding multiple text chunks."""
        # Setup mock to return specific embeddings
        mock_sentence_transformers.encode.return_value.tolist.return_value = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
            [0.7, 0.8, 0.9],
        ]

        component = EmbeddingComponent("test-model")
        texts = ["chunk 1", "chunk 2", "chunk 3"]

        result = component.embed_chunks(texts)

        assert len(result) == 3
        assert result == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]

        # Verify the model was called correctly
        mock_sentence_transformers.encode.assert_called_once_with(
            texts, normalize_embeddings=True
        )

    def test_embed_chunks_empty_list(self, mock_sentence_transformers):
        """Test embedding empty list of chunks."""
        mock_sentence_transformers.encode.return_value.tolist.return_value = []

        component = EmbeddingComponent("test-model")
        result = component.embed_chunks([])

        assert result == []
        mock_sentence_transformers.encode.assert_called_once_with(
            [], normalize_embeddings=True
        )

    def test_embed_chunks_single_item(self, mock_sentence_transformers):
        """Test embedding single chunk."""
        mock_sentence_transformers.encode.return_value.tolist.return_value = [
            [0.1, 0.2, 0.3]
        ]

        component = EmbeddingComponent("test-model")
        result = component.embed_chunks(["single chunk"])

        assert len(result) == 1
        assert result[0] == [0.1, 0.2, 0.3]

    def test_embed_query(self, mock_sentence_transformers):
        """Test embedding a single query with prefix."""
        mock_sentence_transformers.encode.return_value = [[0.1, 0.2, 0.3]]

        component = EmbeddingComponent("test-model")
        query = "search for function"

        result = component.embed_query(query)

        assert result == [0.1, 0.2, 0.3]

        # Verify the query was prefixed and normalized
        expected_query = component.query_prefix + query
        mock_sentence_transformers.encode.assert_called_once_with(
            [expected_query], normalize_embeddings=True
        )

    def test_embed_query_empty_string(self, mock_sentence_transformers):
        """Test embedding empty query string."""
        mock_sentence_transformers.encode.return_value = [[0.0, 0.0, 0.0]]

        component = EmbeddingComponent("test-model")
        result = component.embed_query("")

        assert result == [0.0, 0.0, 0.0]

        # Should still add prefix to empty string
        expected_query = component.query_prefix + ""
        mock_sentence_transformers.encode.assert_called_once_with(
            [expected_query], normalize_embeddings=True
        )

    def test_model_parameters_passed_correctly(self, mock_sentence_transformers):
        """Test that model parameters are passed correctly to SentenceTransformer."""
        with patch(
            "locus.mcp.components.embedding.embedding_component.SentenceTransformer"
        ) as mock_constructor:
            mock_constructor.return_value = mock_sentence_transformers

            EmbeddingComponent("custom-model", trust_remote_code=False)

            mock_constructor.assert_called_once_with(
                "custom-model", trust_remote_code=False
            )

    def test_default_trust_remote_code(self, mock_sentence_transformers):
        """Test that trust_remote_code defaults to True."""
        with patch(
            "locus.mcp.components.embedding.embedding_component.SentenceTransformer"
        ) as mock_constructor:
            mock_constructor.return_value = mock_sentence_transformers

            EmbeddingComponent("test-model")

            mock_constructor.assert_called_once_with(
                "test-model", trust_remote_code=True
            )

    def test_encode_normalization_enabled(self, mock_sentence_transformers):
        """Test that normalization is always enabled for embeddings."""
        component = EmbeddingComponent("test-model")

        # Test chunks
        component.embed_chunks(["test"])
        call_kwargs = mock_sentence_transformers.encode.call_args[1]
        assert call_kwargs["normalize_embeddings"] is True

        # Reset mock
        mock_sentence_transformers.encode.reset_mock()

        # Test query
        component.embed_query("test query")
        call_kwargs = mock_sentence_transformers.encode.call_args[1]
        assert call_kwargs["normalize_embeddings"] is True

    def test_query_prefix_configurable(self, mock_sentence_transformers):
        """Test that query prefix can be modified."""
        component = EmbeddingComponent("test-model")
        original_prefix = component.query_prefix

        # Change prefix
        component.query_prefix = "Custom prefix: "
        component.embed_query("test")

        expected_query = "Custom prefix: test"
        mock_sentence_transformers.encode.assert_called_once_with(
            [expected_query], normalize_embeddings=True
        )

        assert component.query_prefix != original_prefix

    def test_multiple_operations_reuse_model(self, mock_sentence_transformers):
        """Test that multiple operations reuse the same model instance."""
        component = EmbeddingComponent("test-model")

        # Perform multiple operations
        component.embed_chunks(["chunk1", "chunk2"])
        component.embed_query("query1")
        component.embed_chunks(["chunk3"])
        component.embed_query("query2")

        # Model should be called multiple times but initialized only once
        assert mock_sentence_transformers.encode.call_count == 4

    def test_large_batch_handling(self, mock_sentence_transformers):
        """Test handling of large batches."""
        # Setup mock to return appropriate number of embeddings
        num_chunks = 100
        mock_embeddings = [[0.1, 0.2, 0.3] for _ in range(num_chunks)]
        mock_sentence_transformers.encode.return_value.tolist.return_value = (
            mock_embeddings
        )

        component = EmbeddingComponent("test-model")
        large_batch = [f"chunk {i}" for i in range(num_chunks)]

        result = component.embed_chunks(large_batch)

        assert len(result) == num_chunks
        assert all(len(embedding) == 3 for embedding in result)
        mock_sentence_transformers.encode.assert_called_once_with(
            large_batch, normalize_embeddings=True
        )


class TestEmbeddingComponentIntegration:
    """Integration tests for EmbeddingComponent."""

    def test_realistic_code_chunks(self, mock_sentence_transformers):
        """Test embedding realistic code chunks."""
        mock_sentence_transformers.encode.return_value.tolist.return_value = [
            [0.1, 0.2, 0.3, 0.4],
            [0.5, 0.6, 0.7, 0.8],
        ]

        component = EmbeddingComponent("nomic-ai/CodeRankEmbed-v1")

        code_chunks = [
            "def hello_world():\n    return 'Hello, World!'",
            "class Calculator:\n    def add(self, a, b):\n        return a + b",
        ]

        embeddings = component.embed_chunks(code_chunks)

        assert len(embeddings) == 2
        assert len(embeddings[0]) == 4  # Embedding dimension
        assert len(embeddings[1]) == 4

    def test_search_query_embedding(self, mock_sentence_transformers):
        """Test embedding search queries with appropriate prefix."""
        mock_sentence_transformers.encode.return_value = [[0.9, 0.8, 0.7, 0.6]]

        component = EmbeddingComponent("nomic-ai/CodeRankEmbed-v1")
        query = "find authentication functions"

        embedding = component.embed_query(query)

        assert len(embedding) == 4
        # Verify prefix was added
        expected_call = [component.query_prefix + query]
        mock_sentence_transformers.encode.assert_called_with(
            expected_call, normalize_embeddings=True
        )

    def test_consistency_between_calls(self, mock_sentence_transformers):
        """Test that identical inputs produce identical outputs."""
        mock_sentence_transformers.encode.return_value.tolist.return_value = [
            [0.1, 0.2, 0.3]
        ]

        component = EmbeddingComponent("test-model")

        # Same chunk embedded twice
        result1 = component.embed_chunks(["identical chunk"])
        result2 = component.embed_chunks(["identical chunk"])

        assert result1 == result2

    def test_error_handling_in_encode(self, mock_sentence_transformers):
        """Test error handling when encoding fails."""
        mock_sentence_transformers.encode.side_effect = RuntimeError("Model error")

        component = EmbeddingComponent("test-model")

        with pytest.raises(RuntimeError, match="Model error"):
            component.embed_chunks(["test chunk"])

        with pytest.raises(RuntimeError, match="Model error"):
            component.embed_query("test query")
