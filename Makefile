# aForm Makefile
# Convenient commands for development and testing

.PHONY: help install test test-unit test-integration test-coverage test-fast clean lint format type-check security run-dev setup-dev docs

# Default target
help:
	@echo "aForm Development Commands"
	@echo "========================="
	@echo ""
	@echo "Setup:"
	@echo "  install       Install all dependencies"
	@echo "  setup-dev     Set up development environment"
	@echo ""
	@echo "Testing:"
	@echo "  test          Run all tests"
	@echo "  test-unit     Run unit tests only"
	@echo "  test-integration  Run integration tests only"
	@echo "  test-coverage Run tests with coverage report"
	@echo "  test-fast     Run tests excluding slow ones"
	@echo "  test-auth     Run authentication tests"
	@echo "  test-forms    Run form management tests"
	@echo "  test-collab   Run collaboration tests"
	@echo "  test-api      Run API tests"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint          Run code linting"
	@echo "  format        Format code with black and isort"
	@echo "  type-check    Run type checking with mypy"
	@echo "  security      Run security scans"
	@echo ""
	@echo "Development:"
	@echo "  run-dev       Run development server"
	@echo "  clean         Clean up generated files"

# Installation and setup
install:
	pip install -r requirements.txt

setup-dev:
	pip install -r requirements.txt
	pip install pytest-cov pytest-xdist flake8 black isort mypy bandit safety
	@echo "✅ Development environment set up!"
	@echo "📋 Don't forget to:"
	@echo "   1. Set up MongoDB (local or Atlas)"
	@echo "   2. Create .env file with configuration"
	@echo "   3. Set up Google OAuth credentials"

# Testing commands
test:
	python run_tests.py --verbose

test-unit:
	python run_tests.py --unit --verbose

test-integration:
	python run_tests.py --integration --verbose

test-coverage:
	python run_tests.py --coverage --verbose
	@echo "📊 Coverage report generated: htmlcov/index.html"

test-fast:
	python run_tests.py --fast --parallel 4

test-auth:
	python run_tests.py --auth --verbose

test-forms:
	python run_tests.py --forms --verbose

test-collab:
	python run_tests.py --collaboration --verbose

test-api:
	python run_tests.py --api --verbose

# Code quality
lint:
	@echo "🔍 Running flake8..."
	flake8 . --exclude=tests --max-line-length=127 --extend-ignore=E203,W503
	@echo "✅ Linting passed!"

format:
	@echo "🎨 Formatting code with black..."
	black . --exclude=tests
	@echo "📝 Sorting imports with isort..."
	isort . --profile=black --skip=tests
	@echo "✅ Code formatted!"

type-check:
	@echo "🔍 Running type checks..."
	mypy . --ignore-missing-imports --exclude=tests
	@echo "✅ Type checking passed!"

security:
	@echo "🔒 Running security scans..."
	bandit -r . -x tests/ -ll
	safety check
	@echo "✅ Security scans passed!"

# Development
run-dev:
	python main.py

clean:
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	@echo "✅ Cleanup complete!"

# Advanced testing targets
test-verbose:
	pytest tests/ -v --tb=long

test-parallel:
	pytest tests/ -n 4

test-specific:
	@echo "Usage: make test-file FILE=tests/test_auth.py"
	@echo "       make test-function FUNC=test_login_required"

test-file:
	pytest $(FILE) -v

test-function:
	pytest -k $(FUNC) -v

# Database commands
db-reset:
	@echo "⚠️  This will reset the MongoDB database!"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read dummy
	python -c "from database import db_manager; db_manager.get_database().drop_collection('users'); db_manager.get_database().drop_collection('forms')"
	@echo "✅ Database reset complete!"

# Reporting
test-report:
	python run_tests.py --coverage --verbose
	@echo ""
	@echo "📊 Test Results Summary:"
	@echo "========================"
	@echo "📁 Coverage Report: htmlcov/index.html"
	@echo "📋 Full coverage: open htmlcov/index.html"

# CI simulation
ci-test:
	@echo "🚀 Running CI simulation..."
	make lint
	make type-check
	make security
	make test-coverage
	@echo "✅ CI simulation complete!"

# Documentation
docs:
	@echo "📚 Test Documentation"
	@echo "===================="
	@echo ""
	@echo "Test Structure:"
	@echo "  tests/test_auth.py          - Authentication tests"
	@echo "  tests/test_models.py        - Database model tests"
	@echo "  tests/test_forms.py         - Form management tests"
	@echo "  tests/test_collaboration.py - Collaboration tests"
	@echo "  tests/test_public_forms.py  - Public form and submission tests"
	@echo "  tests/test_integration.py   - End-to-end integration tests"
	@echo ""
	@echo "Test Categories:"
	@echo "  @pytest.mark.unit           - Unit tests"
	@echo "  @pytest.mark.integration    - Integration tests"
	@echo "  @pytest.mark.auth           - Authentication tests"
	@echo "  @pytest.mark.database       - Database tests"
	@echo "  @pytest.mark.forms          - Form tests"
	@echo "  @pytest.mark.collaboration  - Collaboration tests"
	@echo "  @pytest.mark.api            - API tests"
	@echo ""
	@echo "Quick Commands:"
	@echo "  make test                   - Run all tests"
	@echo "  make test-coverage          - Generate coverage report"
	@echo "  make test-fast              - Skip slow tests"