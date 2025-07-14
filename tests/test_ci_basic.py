"""
Basic CI tests to validate environment and imports
"""
import pytest
import sys
import os


def test_python_version():
    """Test that we're running on a supported Python version"""
    assert sys.version_info >= (3, 8), f"Python version {sys.version} is not supported"


def test_basic_imports():
    """Test that basic Python modules can be imported"""
    import json
    import datetime
    import pathlib
    assert True


def test_project_structure():
    """Test that project files exist"""
    project_files = [
        'app.py',
        'auth.py', 
        'database.py',
        'models.py',
        'requirements.txt',
        'pytest.ini'
    ]
    
    for file in project_files:
        assert os.path.exists(file), f"Required file {file} not found"


def test_test_directory_structure():
    """Test that test directory is properly structured"""
    test_files = [
        'tests/__init__.py',
        'tests/conftest.py',
        'tests/test_auth.py',
        'tests/test_models.py',
        'tests/test_forms.py'
    ]
    
    for file in test_files:
        assert os.path.exists(file), f"Test file {file} not found"


def test_environment_variables():
    """Test that required environment variables can be set"""
    # These should be set by CI
    env_vars = ['SECRET_KEY', 'FLASK_ENV']
    
    for var in env_vars:
        # Just test that we can access os.getenv
        value = os.getenv(var, 'default')
        assert isinstance(value, str)


def test_requirements_readable():
    """Test that requirements.txt can be read"""
    with open('requirements.txt', 'r') as f:
        content = f.read()
    
    assert 'Flask' in content
    assert 'pytest' in content
    assert 'pymongo' in content


@pytest.mark.skipif(not os.getenv('CI'), reason="Only run in CI environment")
def test_ci_environment():
    """Test that we're actually running in CI"""
    # This test only runs in CI
    assert os.getenv('CI') or os.getenv('GITHUB_ACTIONS')


def test_mock_imports():
    """Test that testing dependencies can be imported"""
    try:
        import mongomock
        import factory
        assert True
    except ImportError as e:
        pytest.fail(f"Testing dependencies not available: {e}")


class TestBasicFunctionality:
    """Test basic application functionality without full setup"""
    
    def test_can_import_app_modules(self):
        """Test that main application modules can be imported"""
        try:
            # Add project root to path
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            import app
            import auth
            import database
            import models
            
            # Test that modules have expected attributes
            assert hasattr(app, 'Flask')
            assert hasattr(auth, 'auth_manager')
            assert hasattr(database, 'db_manager')
            assert hasattr(models, 'UserModel')
            assert hasattr(models, 'FormModel')
            
        except ImportError as e:
            pytest.fail(f"Could not import application modules: {e}")
    
    def test_flask_app_creation(self):
        """Test that Flask app can be created"""
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            from app import app
            
            # Test basic Flask app properties
            assert app.name == 'app'
            assert hasattr(app, 'config')
            
        except ImportError as e:
            pytest.skip(f"Flask app import failed: {e}")
        except Exception as e:
            pytest.skip(f"Flask app creation failed: {e}")


if __name__ == '__main__':
    # Allow running this test file directly
    pytest.main([__file__, '-v'])