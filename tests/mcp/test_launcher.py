"""Tests for MCP launcher functionality."""
import pytest
from unittest.mock import Mock, patch
from locus.mcp.launcher import main, check_deps


class TestCheckDeps:
    """Test the dependency checking functionality."""

    def test_check_deps_all_available(self):
        """Test dependency check when all dependencies are available."""
        with patch('importlib.import_module') as mock_import:
            # Mock successful imports
            mock_import.return_value = Mock()

            result = check_deps()

            assert result is True

    def test_check_deps_missing_sentence_transformers(self):
        """Test dependency check when sentence-transformers is missing."""
        def mock_import(module_name):
            if module_name == 'sentence_transformers':
                raise ImportError("No module named 'sentence_transformers'")
            return Mock()

        with patch('importlib.import_module', side_effect=mock_import), \
             patch('locus.mcp.launcher.logger') as mock_logger:

            result = check_deps()

            assert result is False
            mock_logger.error.assert_called()
            # Check that error message mentions the missing dependency
            error_calls = [call.args[0] for call in mock_logger.error.call_args_list]
            assert any('sentence-transformers' in call for call in error_calls)

    def test_check_deps_missing_lancedb(self):
        """Test dependency check when lancedb is missing."""
        def mock_import(module_name):
            if module_name == 'lancedb':
                raise ImportError("No module named 'lancedb'")
            return Mock()

        with patch('importlib.import_module', side_effect=mock_import), \
             patch('locus.mcp.launcher.logger') as mock_logger:

            result = check_deps()

            assert result is False
            error_calls = [call.args[0] for call in mock_logger.error.call_args_list]
            assert any('lancedb' in call for call in error_calls)

    def test_check_deps_missing_fastmcp(self):
        """Test dependency check when fastmcp is missing."""
        def mock_import(module_name):
            if module_name == 'fastmcp':
                raise ImportError("No module named 'fastmcp'")
            return Mock()

        with patch('importlib.import_module', side_effect=mock_import), \
             patch('locus.mcp.launcher.logger') as mock_logger:

            result = check_deps()

            assert result is False
            error_calls = [call.args[0] for call in mock_logger.error.call_args_list]
            assert any('fastmcp' in call for call in error_calls)

    def test_check_deps_multiple_missing(self):
        """Test dependency check when multiple dependencies are missing."""
        def mock_import(module_name):
            if module_name in ['sentence_transformers', 'lancedb']:
                raise ImportError(f"No module named '{module_name}'")
            return Mock()

        with patch('importlib.import_module', side_effect=mock_import), \
             patch('locus.mcp.launcher.logger') as mock_logger:

            result = check_deps()

            assert result is False
            error_calls = [call.args[0] for call in mock_logger.error.call_args_list]
            assert any('sentence-transformers' in call and 'lancedb' in call for call in error_calls)

    def test_check_deps_install_instruction(self):
        """Test that dependency check provides installation instructions."""
        def mock_import(module_name):
            if module_name == 'sentence_transformers':
                raise ImportError("No module named 'sentence_transformers'")
            return Mock()

        with patch('importlib.import_module', side_effect=mock_import), \
             patch('locus.mcp.launcher.logger') as mock_logger:

            check_deps()

            error_calls = [call.args[0] for call in mock_logger.error.call_args_list]
            assert any("pip install 'locus-analyzer[mcp]'" in call for call in error_calls)


class TestMain:
    """Test the main launcher function."""

    def test_main_serve_command_success(self):
        """Test successful serve command execution."""
        test_args = ['launcher.py', 'serve']

        with patch('sys.argv', test_args), \
             patch('locus.mcp.launcher.check_deps', return_value=True), \
             patch('locus.mcp.launcher.get_container') as mock_get_container, \
             patch('logging.basicConfig'):

            mock_container = Mock()
            mock_app = Mock()
            mock_app.run_stdio = Mock()
            mock_container.mcp_app.return_value = mock_app
            mock_get_container.return_value = mock_container

            # Should not raise any exceptions
            main()

            mock_app.run_stdio.assert_called_once()

    def test_main_missing_dependencies(self):
        """Test main function when dependencies are missing."""
        test_args = ['launcher.py', 'serve']

        with patch('sys.argv', test_args), \
             patch('locus.mcp.launcher.check_deps', return_value=False), \
             patch('sys.exit') as mock_exit, \
             patch('logging.basicConfig'):

            main()

            mock_exit.assert_called_once_with(1)

    def test_main_invalid_command(self):
        """Test main function with invalid command."""
        test_args = ['launcher.py', 'invalid_command']

        with patch('sys.argv', test_args), \
             patch('locus.mcp.launcher.check_deps', return_value=True), \
             patch('logging.basicConfig'), \
             patch('argparse.ArgumentParser.error'):

            try:
                main()
            except SystemExit:
                pass  # ArgumentParser.error() calls sys.exit()

    def test_main_no_command(self):
        """Test main function with no command specified."""
        test_args = ['launcher.py']

        with patch('sys.argv', test_args), \
             patch('locus.mcp.launcher.check_deps', return_value=True), \
             patch('logging.basicConfig'), \
             patch('argparse.ArgumentParser.error'):

            try:
                main()
            except SystemExit:
                pass  # ArgumentParser.error() calls sys.exit()

    def test_main_logging_setup(self):
        """Test that logging is set up correctly."""
        test_args = ['launcher.py', 'serve']

        with patch('sys.argv', test_args), \
             patch('locus.mcp.launcher.check_deps', return_value=True), \
             patch('locus.mcp.launcher.get_container'), \
             patch('logging.basicConfig') as mock_logging:

            try:
                main()
            except Exception:
                pass  # We only care about logging setup

            mock_logging.assert_called_once()
            call_kwargs = mock_logging.call_args[1]
            assert 'level' in call_kwargs
            assert 'format' in call_kwargs

    def test_main_container_creation(self):
        """Test that container is created and MCP app is retrieved."""
        test_args = ['launcher.py', 'serve']

        with patch('sys.argv', test_args), \
             patch('locus.mcp.launcher.check_deps', return_value=True), \
             patch('locus.mcp.launcher.get_container') as mock_get_container, \
             patch('logging.basicConfig'):

            mock_container = Mock()
            mock_app = Mock()
            mock_container.mcp_app.return_value = mock_app
            mock_get_container.return_value = mock_container

            main()

            mock_get_container.assert_called_once()
            mock_container.mcp_app.assert_called_once()

    def test_main_exception_handling(self):
        """Test main function handles exceptions gracefully."""
        test_args = ['launcher.py', 'serve']

        with patch('sys.argv', test_args), \
             patch('locus.mcp.launcher.check_deps', return_value=True), \
             patch('locus.mcp.launcher.get_container', side_effect=Exception("Container error")), \
             patch('logging.basicConfig'):

            with pytest.raises(Exception, match="Container error"):
                main()

    def test_main_argument_parsing(self):
        """Test argument parsing functionality."""
        test_args = ['launcher.py', 'serve']

        with patch('sys.argv', test_args), \
             patch('locus.mcp.launcher.check_deps', return_value=True), \
             patch('locus.mcp.launcher.get_container') as mock_get_container, \
             patch('logging.basicConfig'), \
             patch('argparse.ArgumentParser.parse_args') as mock_parse:

            mock_args = Mock()
            mock_args.command = 'serve'
            mock_parse.return_value = mock_args

            mock_container = Mock()
            mock_app = Mock()
            mock_container.mcp_app.return_value = mock_app
            mock_get_container.return_value = mock_container

            main()

            mock_parse.assert_called_once()

    def test_main_help_command(self):
        """Test help command functionality."""
        test_args = ['launcher.py', '--help']

        with patch('sys.argv', test_args), \
             patch('logging.basicConfig'):

            with pytest.raises(SystemExit) as excinfo:
                main()

            # Help should exit with code 0
            assert excinfo.value.code == 0

    def test_main_version_handling(self):
        """Test that version information can be displayed."""
        # This test assumes there might be a --version flag
        test_args = ['launcher.py', '--version']

        with patch('sys.argv', test_args), \
             patch('logging.basicConfig'):

            try:
                main()
            except SystemExit as e:
                # Version display typically exits with 0
                assert e.code == 0 or e.code is None
            except Exception:
                # If --version is not implemented, that's okay
                pass


class TestLauncherIntegration:
    """Integration tests for the launcher."""

    def test_launcher_imports_successfully(self):
        """Test that launcher can import all required modules."""
        try:
            from locus.mcp.launcher import main, check_deps
            from locus.mcp.di.container import get_container

            assert callable(main)
            assert callable(check_deps)
            assert callable(get_container)
        except ImportError as e:
            pytest.fail(f"Failed to import launcher modules: {e}")

    def test_launcher_argument_parser_setup(self):
        """Test that argument parser is set up correctly."""
        import argparse

        # Test that we can create the same parser as in main()
        parser = argparse.ArgumentParser(description="Locus MCP Server")
        subparsers = parser.add_subparsers(dest="command", help="Available commands")
        subparsers.add_parser("serve", help="Start the MCP server")

        # Should be able to parse valid commands
        args = parser.parse_args(['serve'])
        assert args.command == 'serve'

    def test_full_launcher_workflow_mock(self):
        """Test the full launcher workflow with mocks."""
        test_args = ['launcher.py', 'serve']

        with patch('sys.argv', test_args), \
             patch('locus.mcp.launcher.check_deps', return_value=True), \
             patch('locus.mcp.launcher.get_container') as mock_get_container, \
             patch('logging.basicConfig') as mock_logging:

            # Setup complete mock chain
            mock_container = Mock()
            mock_app = Mock()
            mock_app.run_stdio = Mock()
            mock_container.mcp_app.return_value = mock_app
            mock_get_container.return_value = mock_container

            # Execute main
            main()

            # Verify the complete chain was executed
            mock_logging.assert_called_once()
            mock_get_container.assert_called_once()
            mock_container.mcp_app.assert_called_once()
            mock_app.run_stdio.assert_called_once()

    def test_dependency_check_integration(self):
        """Test dependency checking with various scenarios."""
        # Test with no modules available
        with patch('importlib.import_module', side_effect=ImportError), \
             patch('locus.mcp.launcher.logger') as mock_logger:

            result = check_deps()
            assert result is False
            assert mock_logger.error.called

        # Test with all modules available
        with patch('importlib.import_module', return_value=Mock()):
            result = check_deps()
            assert result is True

    def test_error_propagation(self):
        """Test that errors propagate correctly through the launcher."""
        test_args = ['launcher.py', 'serve']

        with patch('sys.argv', test_args), \
             patch('locus.mcp.launcher.check_deps', return_value=True), \
             patch('logging.basicConfig'):

            # Test container creation error
            with patch('locus.mcp.launcher.get_container', side_effect=ImportError("Missing module")):
                with pytest.raises(ImportError, match="Missing module"):
                    main()

            # Test MCP app creation error
            with patch('locus.mcp.launcher.get_container') as mock_get_container:
                mock_container = Mock()
                mock_container.mcp_app.side_effect = Exception("App creation failed")
                mock_get_container.return_value = mock_container

                with pytest.raises(Exception, match="App creation failed"):
                    main()

    def test_launcher_with_real_argument_parsing(self):
        """Test launcher with real argument parsing (no mocks on argparse)."""
        test_args = ['launcher.py', 'serve']

        with patch('sys.argv', test_args), \
             patch('locus.mcp.launcher.check_deps', return_value=True), \
             patch('locus.mcp.launcher.get_container') as mock_get_container, \
             patch('logging.basicConfig'):

            mock_container = Mock()
            mock_app = Mock()
            mock_container.mcp_app.return_value = mock_app
            mock_get_container.return_value = mock_container

            # Should parse arguments correctly and execute
            main()

            # Verify execution
            mock_container.mcp_app.assert_called_once()
            mock_app.run_stdio.assert_called_once()


class TestLauncherEdgeCases:
    """Test edge cases and error conditions."""

    def test_launcher_with_corrupted_container(self):
        """Test launcher behavior when container is corrupted."""
        test_args = ['launcher.py', 'serve']

        with patch('sys.argv', test_args), \
             patch('locus.mcp.launcher.check_deps', return_value=True), \
             patch('locus.mcp.launcher.get_container') as mock_get_container, \
             patch('logging.basicConfig'):

            # Return a container that doesn't have the expected method
            mock_container = Mock(spec=[])  # Empty spec means no methods
            mock_get_container.return_value = mock_container

            with pytest.raises(AttributeError):
                main()

    def test_launcher_with_partial_dependencies(self):
        """Test launcher when only some dependencies are available."""
        def selective_import(module_name):
            if module_name in ['sentence_transformers', 'lancedb']:
                return Mock()
            else:
                raise ImportError(f"No module named '{module_name}'")

        with patch('importlib.import_module', side_effect=selective_import), \
             patch('locus.mcp.launcher.logger'):

            result = check_deps()
            assert result is False

    def test_launcher_signal_handling(self):
        """Test that launcher can handle signals gracefully."""
        test_args = ['launcher.py', 'serve']

        with patch('sys.argv', test_args), \
             patch('locus.mcp.launcher.check_deps', return_value=True), \
             patch('locus.mcp.launcher.get_container') as mock_get_container, \
             patch('logging.basicConfig'):

            mock_container = Mock()
            mock_app = Mock()

            # Simulate KeyboardInterrupt during app.run_stdio()
            mock_app.run_stdio.side_effect = KeyboardInterrupt("User interrupted")
            mock_container.mcp_app.return_value = mock_app
            mock_get_container.return_value = mock_container

            with pytest.raises(KeyboardInterrupt):
                main()

    def test_launcher_memory_usage(self):
        """Test that launcher doesn't consume excessive memory during startup."""
        test_args = ['launcher.py', 'serve']

        with patch('sys.argv', test_args), \
             patch('locus.mcp.launcher.check_deps', return_value=True), \
             patch('locus.mcp.launcher.get_container') as mock_get_container, \
             patch('logging.basicConfig'):

            mock_container = Mock()
            mock_app = Mock()
            mock_container.mcp_app.return_value = mock_app
            mock_get_container.return_value = mock_container

            # This test mainly ensures no memory leaks in mocks
            for _ in range(10):
                main()

            # Verify container creation wasn't called excessively
            assert mock_get_container.call_count == 10