# TESTS.md — Minimal, Fast, Reliable

A dedicated, minimal guide for writing effective tests.

<test_organization>
## I. Test Organization

### Structure
```
tests/
├─ conftest.py              # Shared fixtures (e.g., temp project structure)
├─ test_core.py             # Core business logic tests
├─ test_formatting.py       # Presentation logic only (no I/O)
├─ test_orchestration.py    # Workflow coordination tests
├─ test_cli.py              # CLI argument parsing and flows
└─ test_utils.py            # Utility function tests
```

### Layer-Based Testing Strategy
- **Core Layer**: Test pure logic with mock data, no I/O
- **Presentation Layer**: Test formatting transformations
- **Orchestration Layer**: Test error handling and workflow coordination
- **Integration**: Test full workflows with realistic data

### Quick Commands
```bash
pytest -q
pytest tests/test_core.py -q
pytest tests/test_core.py::test_function_name -q
pytest --cov=src --cov-report=term-missing
pytest --lf -q
```
</test_organization>

<testing_rules>
## II. Testing Rules

### Core Principles
-   **Tiny Tests**: One behavior, few assertions
-   **Use Fixtures**: No repeated setup; use temp dirs/files
-   **Deterministic**: No network/external state; fix random seeds
-   **Test Edges**: Empty data, invalid inputs, boundary conditions
-   **Fast Execution**: Tests should run in milliseconds, not seconds
-   **Clear Names**: Test names should describe the exact scenario being tested

### Test Categories

**Unit Tests** (Majority of tests):
- Test individual functions in isolation
- Use mocks for external dependencies
- Focus on business logic correctness

**Integration Tests** (Smaller number):
- Test module interactions
- Use real data structures but avoid I/O
- Focus on interface contracts

**End-to-End Tests** (Few critical paths):
- Test complete workflows
- Use temporary files/directories
- Focus on user-facing functionality
</testing_rules>

<test_patterns>
## III. Test Patterns & Examples

### Basic Test Structure

```python
from pathlib import Path

def test_function_behavior(tmp_path: Path):
    # Arrange - Setup test data
    test_file = tmp_path / "test.py"
    test_file.write_text("print('hello')")

    # Act - Execute the function
    result = your_function(test_file)

    # Assert - Verify the outcome
    assert result.is_valid
    assert "hello" in result.content
```

### Pure Function Testing

```python
class MockData:
    def __init__(self, name, value=None):
        self.name, self.value = name, value

def test_pure_function():
    # Arrange
    data = [MockData("a"), MockData("b", "test")]

    # Act
    result = format_data(data, include_values=True)

    # Assert
    assert "a" in result
    assert "b" in result
    assert "test" in result
```

### Parametrized Testing

```python
import pytest

@pytest.mark.parametrize("input_data,expected", [
    ([], 0),
    ([1], 1),
    ([1, 2, 3], 6),
    ([-1, 1], 0),
])
def test_sum_function(input_data, expected):
    result = sum_function(input_data)
    assert result == expected
```
</test_patterns>

<exception_testing>
## IV. Exception Testing Patterns

### Testing Specific Exceptions

```python
import pytest

def test_compute_metrics_raises_insufficient_data():
    """Test that empty data raises appropriate exception."""
    empty_data = []

    with pytest.raises(InsufficientDataError, match="No data for metrics computation"):
        compute_metrics(empty_data)

def test_compute_metrics_raises_validation_error():
    """Test that invalid data raises appropriate exception."""
    invalid_data = ["not", "valid", "format"]

    with pytest.raises(DataValidationError, match="Invalid data format"):
        compute_metrics(invalid_data)

def test_compute_metrics_raises_configuration_error():
    """Test that missing configuration raises appropriate exception."""
    valid_data = [{{"id": 1, "value": 10}}]

    with pytest.raises(ConfigurationError, match="Missing required field"):
        compute_metrics(valid_data, id_field=None, value_field="value")
```

### Testing Error Propagation

```python
def test_orchestration_handles_core_errors(mock_compute_metrics):
    """Test that orchestration layer handles core errors gracefully."""
    # Arrange
    mock_compute_metrics.side_effect = InsufficientDataError("No data")
    cfg = create_test_config()
    ctx = create_test_context(data=[])

    # Act
    result = build_metrics_section(cfg, ctx)

    # Assert
    assert result.is_placeholder
    assert "No data available" in result.content
    assert not result.has_error  # Error was handled gracefully

def test_orchestration_handles_unexpected_errors(mock_compute_metrics):
    """Test that orchestration layer handles unexpected errors."""
    # Arrange
    mock_compute_metrics.side_effect = RuntimeError("Unexpected error")
    cfg = create_test_config()
    ctx = create_test_context()

    # Act & Assert
    with pytest.raises(RuntimeError):  # Unexpected errors should bubble up
        build_metrics_section(cfg, ctx)
```

### Testing Error Messages

```python
def test_error_messages_are_helpful():
    """Test that error messages provide actionable information."""
    invalid_config = {{"missing": "required_field"}}

    with pytest.raises(ConfigurationError) as exc_info:
        validate_config(invalid_config)

    error_message = str(exc_info.value)
    assert "required_field" in error_message
    assert "missing" in error_message
    assert "expected fields" in error_message  # Helpful guidance
```
</exception_testing>

<fixture_patterns>
## V. Fixture Patterns

### Data Fixtures

```python
# conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def sample_data():
    """Provide consistent test data across tests."""
    return [
        {{"id": 1, "name": "Alice", "value": 100}},
        {{"id": 2, "name": "Bob", "value": 200}},
        {{"id": 3, "name": "Charlie", "value": 150}},
    ]

@pytest.fixture
def empty_data():
    """Provide empty data for testing edge cases."""
    return []

@pytest.fixture
def malformed_data():
    """Provide malformed data for testing error handling."""
    return [
        {{"id": "not_a_number", "name": None, "value": "invalid"}},
        {{"missing_id": True, "name": "Alice"}},
    ]
```

### Configuration Fixtures

```python
@pytest.fixture
def test_config():
    """Provide standard test configuration."""
    return AppConfig(
        data_mapping=DataMappingConfig(
            id_field="id",
            name_field="name",
            value_field="value"
        ),
        business_rules=BusinessRulesConfig(
            min_threshold=50,
            max_samples=1000
        )
    )

@pytest.fixture
def minimal_config():
    """Provide minimal configuration for basic tests."""
    return AppConfig(
        data_mapping=DataMappingConfig(
            id_field="id",
            name_field="name",
            value_field="value"
        )
    )
```

### File System Fixtures

```python
@pytest.fixture
def project_structure(tmp_path):
    """Create realistic project structure for testing."""
    # Create directory structure
    src_dir = tmp_path / "src"
    tests_dir = tmp_path / "tests"
    src_dir.mkdir()
    tests_dir.mkdir()

    # Create sample files
    (src_dir / "main.py").write_text("def main(): pass")
    (src_dir / "utils.py").write_text("def helper(): return True")
    (tests_dir / "test_main.py").write_text("def test_main(): assert True")

    return tmp_path

@pytest.fixture
def sample_source_file(tmp_path):
    """Create sample source file for parsing tests."""
    source_file = tmp_path / "example.py"
    source_file.write_text('''
def calculate_sum(a, b):
    """Calculate sum of two numbers."""
    return a + b

class DataProcessor:
    """Process data efficiently."""

    def process(self, data):
        return [x * 2 for x in data]
    ''')
    return source_file
```
</fixture_patterns>

<test_data_management>
## VI. Test Data Management

### Test Data Principles
- **Minimal**: Use the smallest data set that proves the behavior
- **Realistic**: Use data that resembles production scenarios
- **Isolated**: Each test should create its own data
- **Cleaned**: Remove test data after each test

### Mock vs. Real Data Guidelines

**Use Mocks When**:
- Testing error conditions
- Isolating unit behavior
- Avoiding slow operations
- Testing edge cases that are hard to create with real data

```python
@patch('module.expensive_external_call')
def test_function_handles_external_failure(mock_call):
    mock_call.side_effect = ConnectionError("Network unavailable")

    result = function_that_calls_external_service()

    assert result.has_fallback_data
```

**Use Real Data When**:
- Testing data transformations
- Integration testing
- Validating business logic
- End-to-end scenarios

```python
def test_data_transformation_with_real_data():
    real_data = load_test_dataset("small_sample.json")

    result = transform_data(real_data)

    assert len(result) == expected_output_size
    assert all(item.has_required_fields() for item in result)
```

### Performance Testing

```python
import time
import pytest

def test_function_performance():
    """Test that function completes within acceptable time."""
    large_dataset = create_large_test_dataset(size=10000)

    start_time = time.time()
    result = process_large_dataset(large_dataset)
    end_time = time.time()

    execution_time = end_time - start_time
    assert execution_time < 1.0  # Should complete within 1 second
    assert len(result) == 10000

@pytest.mark.slow
def test_memory_usage():
    """Test memory usage with large datasets (marked as slow test)."""
    # This test only runs when explicitly requested
    huge_dataset = create_test_dataset(size=1000000)

    result = memory_efficient_process(huge_dataset)

    assert result.memory_footprint < 100_000_000  # 100MB limit
```
</test_data_management>

<test_debugging>
## VII. Test Debugging & Maintenance

### Debugging Failed Tests

```python
def test_with_debug_output(caplog):
    """Example of test with debug information."""
    import logging

    with caplog.at_level(logging.DEBUG):
        result = complex_function_with_logging()

    # Check both result and log output
    assert result.success
    assert "Processing started" in caplog.text
    assert "Processing completed" in caplog.text

def test_with_intermediate_assertions():
    """Break complex tests into steps for easier debugging."""
    # Step 1: Setup
    data = create_test_data()
    assert len(data) > 0, "Test data should not be empty"

    # Step 2: First transformation
    processed = first_transformation(data)
    assert processed.is_valid, f"First transformation failed: {{processed.error}}"

    # Step 3: Second transformation
    final_result = second_transformation(processed)
    assert final_result.success, f"Final result invalid: {{final_result}}"
```

### Test Maintenance

```python
# Use constants for test values to avoid magic numbers
TEST_USER_ID = 12345
TEST_USER_NAME = "TestUser"
EXPECTED_RESULT_COUNT = 3

def test_with_clear_constants():
    user = create_user(TEST_USER_ID, TEST_USER_NAME)
    results = process_user_data(user)

    assert len(results) == EXPECTED_RESULT_COUNT
    assert results[0].user_id == TEST_USER_ID

# Group related tests in classes
class TestDataValidation:
    """Tests for data validation functionality."""

    def test_valid_data_passes(self):
        valid_data = {{"id": 1, "name": "Alice"}}
        assert validate_data(valid_data).is_valid

    def test_missing_id_fails(self):
        invalid_data = {{"name": "Alice"}}
        result = validate_data(invalid_data)
        assert not result.is_valid
        assert "id" in result.error_message
```
</test_debugging>

<continuous_testing>
## VIII. Continuous Testing Strategy

### Test Categories for CI/CD

```bash
pytest -m "not slow" --maxfail=1
pytest --cov=src --cov-report=xml
pytest -m "integration" --verbose
pytest -m "performance" --benchmark-only
```

### Test Markers

```python
import pytest

@pytest.mark.unit
def test_unit_function():
    """Fast unit test."""
    pass

@pytest.mark.integration
def test_integration_workflow():
    """Slower integration test."""
    pass

@pytest.mark.slow
def test_large_dataset_processing():
    """Very slow test with large data."""
    pass

@pytest.mark.performance
def test_performance_benchmark():
    """Performance/benchmark test."""
    pass
```

### Configuration for Different Environments

```ini
# pytest.ini
[tool:pytest]
markers =
    unit: Fast unit tests
    integration: Integration tests
    slow: Slow tests that process large datasets
    performance: Performance/benchmark tests

# Default: run only fast tests
addopts = -m "not slow and not performance" --strict-markers

# Test discovery
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```
</continuous_testing>

This testing guide provides comprehensive patterns for building a robust, maintainable test suite that scales with your project.