"""Tests for dependency injection container functionality."""
import pytest
from unittest.mock import Mock, patch
from locus.mcp.di.container import get_container


class TestDIContainer:
    """Test the dependency injection container."""

    def test_get_container_singleton(self):
        """Test that get_container returns the same instance."""
        container1 = get_container()
        container2 = get_container()

        assert container1 is container2

    def test_container_has_required_components(self):
        """Test that container provides all required components."""
        container = get_container()

        # Check that all expected component methods exist
        assert hasattr(container, 'embedding_component')
        assert hasattr(container, 'vector_store')
        assert hasattr(container, 'ingest_component')
        assert hasattr(container, 'code_search_engine')

        # Check that they are callable
        assert callable(container.embedding_component)
        assert callable(container.vector_store)
        assert callable(container.ingest_component)
        assert callable(container.code_search_engine)

    @patch('locus.mcp.di.container.load_settings')
    def test_embedding_component_creation(self, mock_load_settings):
        """Test embedding component creation from container."""
        # Mock settings
        mock_settings_instance = Mock()
        mock_settings_instance.embedding.provider = "huggingface"
        mock_settings_instance.embedding.model_name = "test-model"
        mock_settings_instance.embedding.trust_remote_code = True
        mock_load_settings.return_value = mock_settings_instance

        with patch('locus.mcp.components.embedding.embedding_component.EmbeddingComponent') as mock_embedding:
            mock_embedding_instance = Mock()
            mock_embedding.return_value = mock_embedding_instance

            # Reset the singleton
            import locus.mcp.di.container
            locus.mcp.di.container._container_instance = None

            container = get_container()
            embedding_comp = container.embedding_component()

            assert embedding_comp is mock_embedding_instance
            mock_embedding.assert_called_once_with(
                model_name="test-model",
                trust_remote_code=True
            )

    @patch('locus.mcp.di.container.load_settings')
    def test_vector_store_creation(self, mock_load_settings):
        """Test vector store creation from container."""
        mock_settings_instance = Mock()
        mock_settings_instance.vector_store.type = "lancedb"
        mock_settings_instance.vector_store.path = "/test/db"
        mock_load_settings.return_value = mock_settings_instance

        with patch('locus.mcp.components.vector_store.lancedb_store.LanceDBVectorStore') as mock_store:
            mock_store_instance = Mock()
            mock_store.return_value = mock_store_instance

            # Reset the singleton
            import locus.mcp.di.container
            locus.mcp.di.container._container_instance = None

            container = get_container()
            vector_store = container.vector_store()

            assert vector_store is mock_store_instance
            mock_store.assert_called_once_with(db_path="/test/db")

    @patch('locus.mcp.di.container.Settings')
    def test_ingest_component_creation(self, mock_settings):
        """Test ingest component creation with dependencies."""
        mock_settings_instance = Mock()
        mock_settings.return_value = mock_settings_instance

        with patch('locus.mcp.components.ingest.code_ingest_component.CodeIngestComponent') as mock_ingest, \
             patch.object(get_container(), 'embedding_component') as mock_embed_method, \
             patch.object(get_container(), 'vector_store') as mock_store_method:

            mock_ingest_instance = Mock()
            mock_ingest.return_value = mock_ingest_instance

            mock_embed_comp = Mock()
            mock_embed_method.return_value = mock_embed_comp

            mock_vector_store = Mock()
            mock_store_method.return_value = mock_vector_store

            container = get_container()
            ingest_comp = container.ingest_component()

            assert ingest_comp is mock_ingest_instance
            mock_ingest.assert_called_once_with(
                embed_component=mock_embed_comp,
                vector_store=mock_vector_store
            )

    @patch('locus.mcp.di.container.Settings')
    def test_code_search_engine_creation(self, mock_settings):
        """Test code search engine creation."""
        mock_settings_instance = Mock()
        mock_settings.return_value = mock_settings_instance

        with patch('locus.search.engine.HybridSearchEngine') as mock_engine, \
             patch.object(get_container(), 'embedding_component') as mock_embed_method, \
             patch.object(get_container(), 'vector_store') as mock_store_method:

            mock_engine_instance = Mock()
            mock_engine.return_value = mock_engine_instance

            mock_embed_comp = Mock()
            mock_embed_method.return_value = mock_embed_comp

            mock_vector_store = Mock()
            mock_store_method.return_value = mock_vector_store

            container = get_container()
            search_engine = container.code_search_engine()

            assert search_engine is mock_engine_instance
            mock_engine.assert_called_once_with(
                embedding_component=mock_embed_comp,
                vector_store=mock_vector_store
            )

    def test_component_caching(self):
        """Test that components are cached and reused."""
        container = get_container()

        with patch('locus.mcp.components.embedding.embedding_component.EmbeddingComponent') as mock_embedding:
            mock_embedding_instance = Mock()
            mock_embedding.return_value = mock_embedding_instance

            # Call multiple times
            comp1 = container.embedding_component()
            comp2 = container.embedding_component()

            # Should return the same instance
            assert comp1 is comp2
            # Constructor should only be called once
            mock_embedding.assert_called_once()

    def test_dependency_resolution_order(self):
        """Test that dependencies are resolved in correct order."""
        container = get_container()

        call_order = []

        def mock_embedding_constructor(*args, **kwargs):
            call_order.append('embedding')
            return Mock()

        def mock_vector_store_constructor(*args, **kwargs):
            call_order.append('vector_store')
            return Mock()

        def mock_ingest_constructor(*args, **kwargs):
            call_order.append('ingest')
            return Mock()

        with patch('locus.mcp.components.embedding.embedding_component.EmbeddingComponent', side_effect=mock_embedding_constructor), \
             patch('locus.mcp.components.vector_store.lancedb_store.LanceDBVectorStore', side_effect=mock_vector_store_constructor), \
             patch('locus.mcp.components.ingest.code_ingest_component.CodeIngestComponent', side_effect=mock_ingest_constructor):

            # Request ingest component, which depends on others
            container.ingest_component()

            # Dependencies should be created before dependents
            assert 'embedding' in call_order
            assert 'vector_store' in call_order
            assert 'ingest' in call_order

            # Ingest should be created after its dependencies
            ingest_index = call_order.index('ingest')
            embedding_index = call_order.index('embedding')
            vector_store_index = call_order.index('vector_store')

            assert embedding_index < ingest_index
            assert vector_store_index < ingest_index

    @patch('locus.mcp.di.container.Settings')
    def test_settings_loading(self, mock_settings):
        """Test that settings are loaded correctly."""
        mock_settings_instance = Mock()
        mock_settings_instance.embedding.provider = "test_provider"
        mock_settings_instance.embedding.model_name = "test_model"
        mock_settings_instance.vector_store.provider = "test_db"
        mock_settings_instance.vector_store.db_path = "/test/path"
        mock_settings.return_value = mock_settings_instance

        container = get_container()

        # Settings should be loaded when container is accessed
        assert container.settings is mock_settings_instance
        mock_settings.assert_called_once()

    def test_container_isolation(self):
        """Test that different container instances are independent."""
        # This test ensures that if we ever change from singleton pattern,
        # each container instance works independently
        container1 = get_container()
        container2 = get_container()

        # Currently they should be the same (singleton)
        assert container1 is container2

        # But let's test that they could work independently
        with patch('locus.mcp.components.embedding.embedding_component.EmbeddingComponent') as mock_embedding:
            mock_embedding.return_value = Mock()

            comp1 = container1.embedding_component()
            comp2 = container2.embedding_component()

            # Should be the same due to caching
            assert comp1 is comp2

    def test_error_handling_in_component_creation(self):
        """Test error handling when component creation fails."""
        container = get_container()

        with patch('locus.mcp.components.embedding.embedding_component.EmbeddingComponent', side_effect=Exception("Component creation failed")):
            with pytest.raises(Exception, match="Component creation failed"):
                container.embedding_component()

    @patch('locus.mcp.di.container.Settings')
    def test_unsupported_provider_handling(self, mock_settings):
        """Test handling of unsupported providers in settings."""
        mock_settings_instance = Mock()
        mock_settings_instance.embedding.provider = "unsupported_provider"
        mock_settings.return_value = mock_settings_instance

        container = get_container()

        # Should handle unsupported providers gracefully
        # (Implementation depends on how container handles this)
        try:
            container.embedding_component()
        except Exception as e:
            # Should be a meaningful error
            assert "unsupported" in str(e).lower() or "provider" in str(e).lower()

    def test_container_thread_safety(self):
        """Test that container is thread-safe."""
        import threading
        import time

        results = []
        errors = []

        def create_component():
            try:
                container = get_container()
                # Add small delay to increase chance of race conditions
                time.sleep(0.001)
                with patch('locus.mcp.components.embedding.embedding_component.EmbeddingComponent') as mock_embedding:
                    mock_embedding.return_value = Mock()
                    comp = container.embedding_component()
                    results.append(comp)
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=create_component)
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Should not have any errors
        assert len(errors) == 0, f"Thread safety errors: {errors}"

        # All results should be the same instance (cached)
        if results:
            first_result = results[0]
            assert all(result is first_result for result in results)


class TestContainerIntegration:
    """Integration tests for the DI container."""

    def test_full_component_chain(self):
        """Test that the full component chain can be created."""
        with patch('locus.mcp.components.embedding.embedding_component.EmbeddingComponent') as mock_embedding, \
             patch('locus.mcp.components.vector_store.lancedb_store.LanceDBVectorStore') as mock_vector_store, \
             patch('locus.mcp.components.ingest.code_ingest_component.CodeIngestComponent') as mock_ingest, \
             patch('locus.search.engine.HybridSearchEngine') as mock_search:

            # Setup mocks
            mock_embedding.return_value = Mock()
            mock_vector_store.return_value = Mock()
            mock_ingest.return_value = Mock()
            mock_search.return_value = Mock()

            container = get_container()

            # Create all components
            embedding = container.embedding_component()
            vector_store = container.vector_store()
            ingest = container.ingest_component()
            search_engine = container.code_search_engine()

            # All should be created successfully
            assert embedding is not None
            assert vector_store is not None
            assert ingest is not None
            assert search_engine is not None

            # Verify dependencies were passed correctly
            mock_ingest.assert_called_with(
                embed_component=embedding,
                vector_store=vector_store
            )
            mock_search.assert_called_with(
                embedding_component=embedding,
                vector_store=vector_store
            )

    def test_container_with_real_settings(self):
        """Test container behavior with realistic settings."""
        # This test uses the actual Settings class to test integration
        container = get_container()

        # Should be able to access settings
        assert hasattr(container, 'settings')
        assert container.settings is not None

        # Settings should have expected structure
        settings = container.settings
        assert hasattr(settings, 'embedding')
        assert hasattr(settings, 'vector_store')
        assert hasattr(settings, 'index')

    def test_container_error_propagation(self):
        """Test that errors in dependencies propagate correctly."""
        container = get_container()

        # If embedding component fails, ingest should also fail
        with patch('locus.mcp.components.embedding.embedding_component.EmbeddingComponent', side_effect=ImportError("Missing dependency")):
            with pytest.raises(ImportError, match="Missing dependency"):
                container.ingest_component()

    def test_container_cleanup_and_recreation(self):
        """Test container behavior with cleanup and recreation."""
        # Get initial container
        container1 = get_container()

        with patch('locus.mcp.components.embedding.embedding_component.EmbeddingComponent') as mock_embedding:
            mock_embedding.return_value = Mock()
            comp1 = container1.embedding_component()

        # Get container again (should be same instance)
        container2 = get_container()

        with patch('locus.mcp.components.embedding.embedding_component.EmbeddingComponent') as mock_embedding2:
            mock_embedding2.return_value = Mock()
            comp2 = container2.embedding_component()

        # Should be the same due to caching
        assert comp1 is comp2
        assert container1 is container2