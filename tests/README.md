# PhreakBot Test Suite

Comprehensive test suite for PhreakBot IRC bot with unit tests, integration tests, and protocol compliance tests.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Coverage](#test-coverage)
- [Writing Tests](#writing-tests)
- [Continuous Integration](#continuous-integration)

## Overview

The PhreakBot test suite provides comprehensive coverage of:
- ✅ **Unit Tests**: Core functionality, security features, module system
- ✅ **Integration Tests**: Database operations, external systems
- ✅ **IRC Protocol Tests**: Protocol compliance and message handling
- ✅ **Module Tests**: Module loading, unloading, and execution

### Test Statistics

```
Total Test Files: 4+
Total Test Cases: 50+
Code Coverage Target: >80%
```

## Test Structure

```
tests/
├── unit/                      # Unit tests
│   ├── test_core.py          # Core bot functionality
│   ├── test_modules.py       # Module system tests
│   └── __init__.py
├── integration/               # Integration tests
│   ├── test_database.py      # Database operations
│   └── __init__.py
├── fixtures/                  # Test fixtures and helpers
│   └── __init__.py
└── conftest.py               # Shared pytest configuration
```

## Running Tests

### Prerequisites

Install test dependencies:

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
# Run all tests with coverage
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=. --cov-report=html
```

### Run Specific Test Categories

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only module tests
pytest -m module

# Run only IRC protocol tests
pytest -m irc
```

### Run Specific Test Files

```bash
# Run core functionality tests
pytest tests/unit/test_core.py

# Run module system tests
pytest tests/unit/test_modules.py

# Run database tests
pytest tests/integration/test_database.py
```

### Run Specific Test Classes or Methods

```bash
# Run a specific test class
pytest tests/unit/test_core.py::TestInputSanitization

# Run a specific test method
pytest tests/unit/test_core.py::TestInputSanitization::test_sanitize_input_sql_injection

# Run tests matching a pattern
pytest -k "sanitize"
```

### Skip Slow Tests

```bash
# Skip tests marked as slow
pytest -m "not slow"
```

### Skip Tests Requiring External Resources

```bash
# Skip database tests
pytest -m "not requires_db"

# Skip IRC tests
pytest -m "not requires_irc"
```

## Test Coverage

### View Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=. --cov-report=html

# Open in browser
open htmlcov/index.html
```

### Coverage Configuration

Coverage settings are configured in `.coveragerc`:

- **Source**: All Python files in project root
- **Omit**: Test files, virtual environments, cache files
- **Target**: >80% coverage
- **Reports**: Terminal, HTML, XML

### Current Coverage Areas

✅ **High Coverage (>80%)**
- Input sanitization methods
- Rate limiting logic
- SQL safety validation
- Permission validation
- Caching system
- Module loading/unloading

⚠️ **Medium Coverage (50-80%)**
- Database operations (mocked)
- IRC event handling
- Configuration management

❌ **Low Coverage (<50%)**
- Async IRC connection handling
- Live IRC protocol interactions
- External API integrations

## Writing Tests

### Test File Naming

- Unit tests: `test_*.py`
- Integration tests: `test_*.py`
- Place in appropriate directory (`unit/` or `integration/`)

### Test Function Naming

- Test functions: `test_*`
- Test classes: `Test*`
- Descriptive names: `test_sanitize_input_removes_null_bytes`

### Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit
def test_something():
    pass

@pytest.mark.integration
@pytest.mark.requires_db
def test_database_operation():
    pass

@pytest.mark.slow
def test_long_running():
    pass
```

### Available Markers

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.irc`: IRC protocol tests
- `@pytest.mark.module`: Module tests
- `@pytest.mark.slow`: Slow-running tests
- `@pytest.mark.requires_db`: Requires database
- `@pytest.mark.requires_irc`: Requires IRC server

### Fixtures

Common fixtures are available in `conftest.py`:

```python
def test_with_bot(bot):
    """Test using bot fixture."""
    assert bot.nickname == "TestBot"

def test_with_config(mock_config):
    """Test using config fixture."""
    with open(mock_config) as f:
        config = json.load(f)
    assert config["trigger"] == "!"
```

### Mocking

Use `unittest.mock` for mocking:

```python
from unittest.mock import Mock, patch, MagicMock

def test_with_mock():
    with patch('phreakbot.psycopg2.pool.ThreadedConnectionPool'):
        bot = PhreakBot(config_path)
        # Test code
```

### Async Tests

For async functions, use `pytest-asyncio`:

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result == expected
```

## Test Examples

### Example: Unit Test

```python
@pytest.mark.unit
def test_sanitize_input_removes_sql_injection(bot):
    """Test that SQL injection patterns are removed."""
    dangerous = "'; DROP TABLE users--"
    result = bot._sanitize_input(dangerous, allow_special_chars=False)

    assert "DROP" not in result or "--" not in result
```

### Example: Integration Test

```python
@pytest.mark.integration
@pytest.mark.requires_db
def test_database_user_lookup(bot):
    """Test user lookup from database."""
    # Mock database response
    bot.db_connection.cursor().fetchall.return_value = [
        {"id": 1, "username": "testuser"}
    ]

    result = bot.db_get_userinfo_by_userhost("test!user@host")
    assert result["username"] == "testuser"
```

### Example: Module Test

```python
@pytest.mark.module
def test_module_loads_successfully(bot, test_module):
    """Test that a valid module loads."""
    result = bot.load_module(test_module)

    assert result is True
    assert "test_module" in bot.modules
```

## Continuous Integration

### GitHub Actions (Recommended)

Create `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: |
        pytest --cov=. --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

### Local Pre-commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
pytest -m "not slow and not requires_db and not requires_irc"
```

## Troubleshooting

### Common Issues

#### Import Errors

```
ModuleNotFoundError: No module named 'phreakbot'
```

**Solution**: Tests add parent directory to path. Ensure you're running from project root.

#### Database Connection Failures

```
psycopg2.OperationalError: could not connect to server
```

**Solution**: Run without database tests: `pytest -m "not requires_db"`

#### Async Warnings

```
RuntimeWarning: coroutine was never awaited
```

**Solution**: Use `@pytest.mark.asyncio` decorator and `await` async functions.

### Debug Mode

Run tests with detailed output:

```bash
# Show print statements
pytest -s

# Show local variables on failure
pytest -l

# Drop into debugger on failure
pytest --pdb

# Full traceback
pytest --tb=long
```

## Best Practices

1. **Keep Tests Isolated**: Each test should be independent
2. **Use Fixtures**: Reuse common setup code
3. **Mock External Dependencies**: Database, IRC, API calls
4. **Test Edge Cases**: Null values, empty strings, large inputs
5. **Descriptive Names**: Test names should describe what they test
6. **Fast Tests**: Keep unit tests under 1 second
7. **Coverage Goals**: Aim for >80% coverage
8. **Document Complex Tests**: Add comments explaining non-obvious logic

## Contributing

When adding new features to PhreakBot:

1. Write tests first (TDD approach)
2. Ensure tests pass: `pytest`
3. Check coverage: `pytest --cov=.`
4. Add appropriate markers
5. Update this README if adding new test categories

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [unittest.mock documentation](https://docs.python.org/3/library/unittest.mock.html)
- [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)

## Test Results

To view test results from latest run:

```bash
# View last test results
cat .pytest_cache/v/cache/lastfailed

# View coverage report
cat htmlcov/index.html
```

---

**Last Updated**: 2025-11-27
**PhreakBot Version**: 0.1.28
**Test Framework**: pytest 7.4.3+
