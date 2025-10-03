# Smart Contract Rewriter Platform - Test Suite

This directory contains comprehensive tests for the Smart Contract Rewriter Platform microservices.

## 📋 Test Structure

```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── unit/                    # Unit tests for individual components
│   ├── test_contract_service.py
│   ├── test_ai_service.py
│   ├── test_auth_service.py
│   └── test_notification_service.py
├── integration/             # Integration tests between services
│   ├── test_contract_analysis_flow.py
│   └── test_ai_integration.py
└── e2e/                     # End-to-end tests
    └── test_full_workflow.py
```

## 🚀 Running Tests

### **Install Test Dependencies**
```bash
pip install -r requirements-test.txt
```

### **Run All Tests**
```bash
# Run all tests with coverage
pytest --cov=microservices tests/ -v

# Run specific test categories
pytest tests/unit/ -v           # Unit tests only
pytest tests/integration/ -v    # Integration tests only
pytest tests/e2e/ -v           # End-to-end tests only
```

### **Generate Coverage Report**
```bash
# Generate HTML coverage report
pytest --cov=microservices --cov-report=html tests/

# View coverage report
open htmlcov/index.html
```

## 📊 Test Coverage Goals

- **Unit Tests**: 85%+ coverage for core business logic
- **Integration Tests**: Key service interactions validated
- **E2E Tests**: Critical user workflows covered

## 🧪 Test Categories

### **Unit Tests**
- Service endpoint functionality
- Data model validation
- Error handling
- Business logic correctness

### **Integration Tests**
- Service-to-service communication
- Database interactions
- External API integrations (mocked)

### **End-to-End Tests**
- Complete user workflows
- Multi-service orchestration
- Performance benchmarks

## 🔧 Test Configuration

Tests use:
- **pytest** for test framework
- **httpx** for async HTTP testing
- **pytest-asyncio** for async test support
- **pytest-mock** for mocking dependencies
- **pytest-cov** for coverage reporting

## 📝 Writing Tests

### **Test Naming Convention**
```python
def test_should_return_success_when_valid_contract_provided():
    """
    Test function names should be descriptive and follow the pattern:
    test_should_{expected_behavior}_when_{condition}
    """
    pass
```

### **Test Organization**
- One test file per service
- Group related tests in classes
- Use descriptive test names
- Include docstrings for complex tests

## 🐛 Debugging Tests

```bash
# Run tests with detailed output
pytest -v -s tests/

# Run specific test
pytest tests/unit/test_contract_service.py::test_analyze_contract_success -v

# Run tests with debugger
pytest --pdb tests/unit/test_contract_service.py
```

## 🚀 Continuous Integration

Tests are configured to run automatically on:
- Pull requests
- Main branch commits
- Scheduled nightly runs

See `.github/workflows/test.yml` for CI configuration.