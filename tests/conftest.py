"""
Test configuration and fixtures for aForm application
"""
import pytest
import mongomock
from unittest.mock import patch, MagicMock
import os
import tempfile
from datetime import datetime

# Import application modules
import sys
import os

# Add the parent directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from app import app as flask_app
    from database import db_manager
    from models import UserModel, FormModel
    from auth import auth_manager
    import factory
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Python path: {sys.path}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Project root: {project_root}")
    raise


@pytest.fixture
def app():
    """Create Flask app for testing"""
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    flask_app.config['SECRET_KEY'] = 'test_secret_key'
    
    # Mock MongoDB for testing
    with patch('database.MongoClient') as mock_client:
        mock_db = mongomock.MongoClient().aform_test
        mock_client.return_value = MagicMock()
        mock_client.return_value.__getitem__.return_value = mock_db
        
        # Initialize database manager with mock
        db_manager.client = mock_client.return_value
        db_manager.db = mock_db
        db_manager.users_collection = mock_db.users
        db_manager.forms_collection = mock_db.forms
        
        yield flask_app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def mock_mongo():
    """Mock MongoDB client for testing"""
    with patch('database.MongoClient') as mock_client:
        mock_db = mongomock.MongoClient().aform_test
        mock_client.return_value = MagicMock()
        mock_client.return_value.__getitem__.return_value = mock_db
        
        # Setup database manager
        db_manager.client = mock_client.return_value
        db_manager.db = mock_db
        db_manager.users_collection = mock_db.users
        db_manager.forms_collection = mock_db.forms
        
        yield mock_db


@pytest.fixture
def mock_google_oauth():
    """Mock Google OAuth for testing"""
    with patch('auth.OAuth') as mock_oauth:
        mock_google = MagicMock()
        mock_oauth.return_value.register.return_value = mock_google
        auth_manager.google = mock_google
        yield mock_google


@pytest.fixture
def mock_mail():
    """Mock Flask-Mail for testing"""
    with patch('app.mail') as mock_mail:
        mock_mail.send = MagicMock()
        yield mock_mail


class UserFactory(factory.Factory):
    """Factory for creating test users"""
    class Meta:
        model = dict
    
    id = factory.Sequence(lambda n: f"user_{n}")
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    name = factory.Sequence(lambda n: f"User {n}")
    picture = ""
    role = "user"
    created_at = factory.LazyFunction(datetime.now)
    last_login = factory.LazyFunction(datetime.now)
    status = "active"


class FormFactory(factory.Factory):
    """Factory for creating test forms"""
    class Meta:
        model = dict
    
    name = factory.Sequence(lambda n: f"test_form_{n}")
    status = "draft"
    created_by = "user_1"
    created_by_name = "Test User"
    created_at = factory.LazyFunction(datetime.now)
    updated_at = factory.LazyFunction(datetime.now)
    permissions = {
        'admin': ['user_1'],
        'editor': [],
        'viewer': []
    }
    invites = []
    submissions = []
    questions = [
        {
            'id': 'q_1',
            'title': 'Question 1',
            'text': 'Test question',
            'type': 'text',
            'required': False
        }
    ]


@pytest.fixture
def sample_user():
    """Create a sample user for testing"""
    return UserFactory()


@pytest.fixture
def sample_form():
    """Create a sample form for testing"""
    return FormFactory()


@pytest.fixture
def admin_user():
    """Create an admin user for testing"""
    return UserFactory(role='admin')


@pytest.fixture
def authenticated_session(client, sample_user):
    """Create authenticated session for testing"""
    with client.session_transaction() as sess:
        sess['user'] = sample_user
    return sample_user


@pytest.fixture
def admin_session(client, admin_user):
    """Create admin authenticated session for testing"""
    with client.session_transaction() as sess:
        sess['user'] = admin_user
    return admin_user


@pytest.fixture
def sample_submission():
    """Create a sample form submission for testing"""
    return {
        'id': 'submission_1',
        'submitted_at': datetime.now(),
        'responses': {
            'q_1': 'Sample response'
        }
    }


@pytest.fixture
def cleanup_db(mock_mongo):
    """Clean up database after each test"""
    yield
    # Clear all collections
    mock_mongo.users.delete_many({})
    mock_mongo.forms.delete_many({})


# Test utilities
def create_test_user(mock_mongo, user_data=None):
    """Helper to create a test user in database"""
    if user_data is None:
        user_data = UserFactory()
    
    mock_mongo.users.insert_one(user_data)
    return user_data


def create_test_form(mock_mongo, form_data=None):
    """Helper to create a test form in database"""
    if form_data is None:
        form_data = FormFactory()
    
    mock_mongo.forms.insert_one(form_data)
    return form_data


def authenticate_user(client, user_data):
    """Helper to authenticate a user in test client"""
    with client.session_transaction() as sess:
        sess['user'] = user_data
    return user_data