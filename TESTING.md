# Testing Guide for aForm

This document provides comprehensive information about testing the aForm application.

## Overview

The aForm test suite provides comprehensive coverage of all application functionality including:

- **Authentication & Authorization** - OAuth, permissions, role-based access
- **Database Operations** - MongoDB models, data consistency, error handling
- **Form Management** - Creation, editing, publishing, deletion
- **Collaboration** - User invitations, role management, email notifications
- **Public Forms** - Form submission, validation, security
- **Integration** - End-to-end workflows, error scenarios

## Test Structure

```
tests/
├── __init__.py                 # Test package
├── conftest.py                # Test configuration and fixtures
├── test_auth.py               # Authentication tests
├── test_models.py             # Database model tests
├── test_forms.py              # Form management tests
├── test_collaboration.py      # Collaboration tests
├── test_public_forms.py       # Public form and submission tests
└── test_integration.py        # Integration tests
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run All Tests

```bash
# Using the test runner
python run_tests.py

# Using pytest directly
pytest tests/

# Using make
make test
```

### 3. Run with Coverage

```bash
python run_tests.py --coverage
# OR
make test-coverage
```

## Test Categories

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Unit tests (isolated component testing)
- `@pytest.mark.integration` - Integration tests (end-to-end workflows)
- `@pytest.mark.auth` - Authentication and authorization tests
- `@pytest.mark.database` - Database operation tests
- `@pytest.mark.forms` - Form management tests
- `@pytest.mark.collaboration` - Collaboration feature tests
- `@pytest.mark.api` - API endpoint tests

### Running Specific Test Categories

```bash
# Run only unit tests
python run_tests.py --unit

# Run only authentication tests
python run_tests.py --auth

# Run only database tests
python run_tests.py --database

# Run specific test file
python run_tests.py --file tests/test_auth.py

# Run specific test function
pytest tests/test_auth.py::TestAuthManager::test_login_required
```

## Test Configuration

### Environment Setup

Tests use the following configuration:

- **Database**: MongoDB with mongomock for isolated testing
- **Authentication**: Mocked Google OAuth for predictable testing
- **Email**: Mocked Flask-Mail for email testing
- **Sessions**: Flask test client session management

### Key Fixtures

Located in `tests/conftest.py`:

- `app` - Flask application configured for testing
- `client` - Flask test client
- `mock_mongo` - MongoDB mock for database testing
- `authenticated_session` - Pre-authenticated user session
- `sample_user` - Factory-generated test user
- `sample_form` - Factory-generated test form

### Factory Classes

Test data is generated using factory classes:

```python
# Create test user
user = UserFactory(email='test@example.com', role='admin')

# Create test form
form = FormFactory(name='test_form', status='published')
```

## Running Tests

### Basic Commands

```bash
# All tests
pytest tests/

# Verbose output
pytest tests/ -v

# Parallel execution
pytest tests/ -n 4

# Stop on first failure
pytest tests/ -x

# Coverage report
pytest tests/ --cov=. --cov-report=html
```

### Using the Test Runner

The `run_tests.py` script provides convenient testing commands:

```bash
# Basic usage
python run_tests.py

# Specific categories
python run_tests.py --auth --verbose
python run_tests.py --integration --coverage

# Performance options
python run_tests.py --fast --parallel 4

# Coverage reporting
python run_tests.py --coverage
```

### Using Make Commands

```bash
make test              # Run all tests
make test-unit         # Unit tests only
make test-integration  # Integration tests only
make test-coverage     # Tests with coverage
make test-fast         # Skip slow tests
make test-auth         # Authentication tests
make test-forms        # Form management tests
make test-collab       # Collaboration tests
make test-api          # API tests
```

## Test Details

### Authentication Tests (`test_auth.py`)

Tests OAuth authentication, user management, and permission systems:

- User creation and updates
- Session management
- Role-based permissions
- Form-level access controls
- Authentication decorators
- OAuth callback handling

### Database Model Tests (`test_models.py`)

Tests MongoDB operations and data models:

- User CRUD operations
- Form CRUD operations
- Data validation
- Error handling
- Index creation
- Query optimization

### Form Management Tests (`test_forms.py`)

Tests form lifecycle and management:

- Form creation and validation
- Question management
- Form publishing/hiding
- Permission enforcement
- Form deletion
- Submission viewing

### Collaboration Tests (`test_collaboration.py`)

Tests multi-user collaboration features:

- User invitations
- Role assignment (admin/editor/viewer)
- Permission enforcement
- Collaborator management
- Email notifications

### Public Form Tests (`test_public_forms.py`)

Tests public form access and submissions:

- Public form rendering
- Form submission validation
- Data handling and storage
- Security measures
- Anonymous access

### Integration Tests (`test_integration.py`)

Tests complete end-to-end workflows:

- Full form lifecycle
- User journey scenarios
- Error handling across components
- Data consistency
- Permission changes

## Mocking Strategy

### Database Mocking

Uses `mongomock` to provide isolated MongoDB testing:

```python
@pytest.fixture
def mock_mongo():
    with patch('database.MongoClient') as mock_client:
        mock_db = mongomock.MongoClient().aform_test
        # Setup mock database
        yield mock_db
```

### Authentication Mocking

OAuth and email services are mocked for predictable testing:

```python
# Mock Google OAuth
@pytest.fixture
def mock_google_oauth():
    with patch('auth.OAuth') as mock_oauth:
        yield mock_oauth

# Mock email sending
@pytest.fixture
def mock_mail():
    with patch('app.mail') as mock_mail:
        yield mock_mail
```

## Continuous Integration

### GitHub Actions

The `.github/workflows/tests.yml` file configures automated testing:

- **Matrix Testing**: Multiple Python and MongoDB versions
- **Test Execution**: Unit tests, integration tests, coverage
- **Code Quality**: Linting, formatting, type checking
- **Security**: Bandit and safety scans
- **Artifacts**: Coverage reports and test results

### Running CI Locally

Simulate CI environment locally:

```bash
make ci-test
```

## Coverage Reporting

### Generate Coverage Report

```bash
# HTML report
python run_tests.py --coverage

# Terminal report
pytest tests/ --cov=. --cov-report=term-missing

# XML report (for CI)
pytest tests/ --cov=. --cov-report=xml
```

### Coverage Targets

- **Overall Coverage**: >90%
- **Critical Components**: >95%
- **New Code**: 100%

### Viewing Reports

```bash
# Open HTML coverage report
open htmlcov/index.html

# View in browser
python -m http.server 8000 --directory htmlcov
```

## Writing New Tests

### Test Structure

Follow this structure for new tests:

```python
@pytest.mark.category
class TestFeatureName:
    """Test feature description"""
    
    def test_successful_operation(self, client, authenticated_session):
        """Test successful operation scenario"""
        # Arrange
        test_data = {'key': 'value'}
        
        # Act
        with patch('module.function') as mock_func:
            response = client.post('/api/endpoint', json=test_data)
        
        # Assert
        assert response.status_code == 200
        mock_func.assert_called_once()
    
    def test_error_scenario(self, client):
        """Test error handling"""
        # Test error cases
        pass
```

### Best Practices

1. **Isolation**: Each test should be independent
2. **Mocking**: Mock external dependencies (database, email, OAuth)
3. **Data**: Use factories for test data generation
4. **Assertions**: Test both positive and negative scenarios
5. **Documentation**: Clear test names and docstrings
6. **Coverage**: Aim for high code coverage
7. **Performance**: Keep tests fast and efficient

### Test Naming

Use descriptive test names:

```python
def test_create_form_success(self):           # ✅ Clear intent
def test_create_form_duplicate_name(self):    # ✅ Specific scenario
def test_create_form_no_permission(self):     # ✅ Error case
def test_form_creation(self):                 # ❌ Too vague
```

## Debugging Tests

### Running Individual Tests

```bash
# Specific test file
pytest tests/test_auth.py -v

# Specific test class
pytest tests/test_auth.py::TestAuthManager -v

# Specific test function
pytest tests/test_auth.py::TestAuthManager::test_login_required -v

# Tests matching pattern
pytest -k "test_auth" -v
```

### Debug Output

```bash
# Print statements in tests
pytest tests/ -s

# Debug on failure
pytest tests/ --pdb

# Verbose traceback
pytest tests/ --tb=long
```

### Common Issues

1. **Database State**: Ensure proper cleanup between tests
2. **Mocking**: Verify mocks are properly configured
3. **Authentication**: Check session setup for protected routes
4. **Async Operations**: Handle timing issues in integration tests

## Performance Testing

### Fast Test Execution

```bash
# Skip slow tests
python run_tests.py --fast

# Parallel execution
python run_tests.py --parallel 4

# Minimal output
pytest tests/ -q
```

### Profiling Tests

```bash
# Profile test execution
pytest tests/ --profile

# Time individual tests
pytest tests/ --durations=10
```

## Test Data Management

### Factories

Use factory classes for consistent test data:

```python
# User factory
user = UserFactory(
    email='test@example.com',
    role='admin'
)

# Form factory
form = FormFactory(
    name='test_form',
    status='published',
    permissions={'admin': ['user_123']}
)
```

### Database Cleanup

The `cleanup_db` fixture ensures clean state:

```python
@pytest.fixture
def cleanup_db(mock_mongo):
    yield
    # Clear all collections after test
    mock_mongo.users.delete_many({})
    mock_mongo.forms.delete_many({})
```

## Security Testing

Tests include security considerations:

- **Input Validation**: Malicious data handling
- **Access Control**: Permission enforcement
- **Data Exposure**: Sensitive data protection
- **Session Security**: Authentication bypass attempts

## Troubleshooting

### Common Test Failures

1. **Import Errors**: Check PYTHONPATH and dependencies
2. **Database Errors**: Verify MongoDB mock setup
3. **Authentication Errors**: Check session fixtures
4. **Permission Errors**: Verify user roles and form permissions

### Getting Help

1. Check test output and traceback
2. Run individual failing tests with `-v` flag
3. Review test fixtures and mocks
4. Check recent code changes
5. Consult this documentation

## Contributing

When contributing new features:

1. **Write tests first** (TDD approach)
2. **Test all scenarios** (success, failure, edge cases)
3. **Maintain coverage** (aim for >90%)
4. **Update documentation** (add new test categories)
5. **Run full test suite** before submitting

---

For more information, see the main README.md or contact the development team.