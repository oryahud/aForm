"""
Database model tests for aForm application
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from pymongo.errors import DuplicateKeyError

from models import UserModel, FormModel
from tests.conftest import UserFactory, FormFactory, create_test_user, create_test_form


@pytest.mark.database
class TestUserModel:
    """Test UserModel class"""
    
    def test_create_user_success(self, mock_mongo):
        """Test successful user creation"""
        user_info = {
            'email': 'test@example.com',
            'name': 'Test User',
            'picture': 'http://example.com/pic.jpg'
        }
        
        user = UserModel.create_user(user_info)
        
        assert user['email'] == 'test@example.com'
        assert user['name'] == 'Test User'
        assert user['role'] == 'user'
        assert user['status'] == 'active'
        assert 'id' in user
        assert 'created_at' in user
        assert 'last_login' in user
    
    def test_create_user_duplicate_email(self, mock_mongo):
        """Test user creation with duplicate email"""
        user_info = {
            'email': 'duplicate@example.com',
            'name': 'Test User'
        }
        
        # Create first user
        UserModel.create_user(user_info)
        
        # Try to create duplicate
        with pytest.raises(ValueError, match="User with this email already exists"):
            UserModel.create_user(user_info)
    
    def test_update_user_success(self, mock_mongo):
        """Test successful user update"""
        user = create_test_user(mock_mongo, UserFactory(id='user_123'))
        
        update_data = {
            'name': 'Updated Name',
            'picture': 'http://example.com/new_pic.jpg'
        }
        
        updated_user = UserModel.update_user('user_123', update_data)
        
        assert updated_user['name'] == 'Updated Name'
        assert updated_user['picture'] == 'http://example.com/new_pic.jpg'
        assert 'last_login' in updated_user
    
    def test_update_user_not_found(self, mock_mongo):
        """Test user update when user not found"""
        update_data = {'name': 'Updated Name'}
        
        with pytest.raises(ValueError, match="User not found"):
            UserModel.update_user('nonexistent_id', update_data)
    
    def test_get_user_by_email_found(self, mock_mongo):
        """Test getting user by email when found"""
        user = create_test_user(mock_mongo, UserFactory(email='test@example.com'))
        
        found_user = UserModel.get_user_by_email('test@example.com')
        
        assert found_user is not None
        assert found_user['email'] == 'test@example.com'
        assert found_user['id'] == user['id']
    
    def test_get_user_by_email_not_found(self, mock_mongo):
        """Test getting user by email when not found"""
        found_user = UserModel.get_user_by_email('nonexistent@example.com')
        
        assert found_user is None
    
    def test_get_user_by_id_found(self, mock_mongo):
        """Test getting user by ID when found"""
        user = create_test_user(mock_mongo, UserFactory(id='user_123'))
        
        found_user = UserModel.get_user_by_id('user_123')
        
        assert found_user is not None
        assert found_user['id'] == 'user_123'
        assert found_user['email'] == user['email']
    
    def test_get_user_by_id_not_found(self, mock_mongo):
        """Test getting user by ID when not found"""
        found_user = UserModel.get_user_by_id('nonexistent_id')
        
        assert found_user is None
    
    def test_get_all_users(self, mock_mongo):
        """Test getting all users"""
        user1 = create_test_user(mock_mongo, UserFactory())
        user2 = create_test_user(mock_mongo, UserFactory())
        
        users = UserModel.get_all_users()
        
        assert len(users) == 2
        user_emails = [u['email'] for u in users]
        assert user1['email'] in user_emails
        assert user2['email'] in user_emails
    
    def test_delete_user_success(self, mock_mongo):
        """Test successful user deletion"""
        user = create_test_user(mock_mongo, UserFactory(id='user_123'))
        
        result = UserModel.delete_user('user_123')
        
        assert result is True
        
        # Verify user is deleted
        found_user = UserModel.get_user_by_id('user_123')
        assert found_user is None
    
    def test_delete_user_not_found(self, mock_mongo):
        """Test user deletion when user not found"""
        result = UserModel.delete_user('nonexistent_id')
        
        assert result is False


@pytest.mark.database
class TestFormModel:
    """Test FormModel class"""
    
    def test_create_form_success(self, mock_mongo):
        """Test successful form creation"""
        form_data = {
            'name': 'test_form',
            'status': 'draft',
            'created_by': 'user_123',
            'created_by_name': 'Test User',
            'permissions': {
                'admin': ['user_123'],
                'editor': [],
                'viewer': []
            },
            'questions': [
                {
                    'id': 'q_1',
                    'title': 'Question 1',
                    'text': 'Test question',
                    'type': 'text',
                    'required': False
                }
            ]
        }
        
        form = FormModel.create_form(form_data)
        
        assert form['name'] == 'test_form'
        assert form['status'] == 'draft'
        assert form['created_by'] == 'user_123'
        assert 'created_at' in form
        assert 'updated_at' in form
        assert len(form['questions']) == 1
    
    def test_create_form_duplicate_name(self, mock_mongo):
        """Test form creation with duplicate name"""
        form_data = FormFactory(name='duplicate_form')
        
        # Create first form
        FormModel.create_form(form_data)
        
        # Try to create duplicate
        with pytest.raises(ValueError, match="Form with this name already exists"):
            FormModel.create_form(form_data)
    
    def test_update_form_success(self, mock_mongo):
        """Test successful form update"""
        form = create_test_form(mock_mongo, FormFactory(name='test_form'))
        
        update_data = {
            'status': 'published',
            'questions': [
                {
                    'id': 'q_1',
                    'title': 'Updated Question',
                    'text': 'Updated question text',
                    'type': 'text',
                    'required': True
                }
            ]
        }
        
        updated_form = FormModel.update_form('test_form', update_data)
        
        assert updated_form['status'] == 'published'
        assert updated_form['questions'][0]['title'] == 'Updated Question'
        assert updated_form['questions'][0]['required'] is True
        assert 'updated_at' in updated_form
    
    def test_update_form_not_found(self, mock_mongo):
        """Test form update when form not found"""
        update_data = {'status': 'published'}
        
        with pytest.raises(ValueError, match="Form not found"):
            FormModel.update_form('nonexistent_form', update_data)
    
    def test_get_form_by_name_found(self, mock_mongo):
        """Test getting form by name when found"""
        form = create_test_form(mock_mongo, FormFactory(name='test_form'))
        
        found_form = FormModel.get_form_by_name('test_form')
        
        assert found_form is not None
        assert found_form['name'] == 'test_form'
        assert found_form['created_by'] == form['created_by']
    
    def test_get_form_by_name_not_found(self, mock_mongo):
        """Test getting form by name when not found"""
        found_form = FormModel.get_form_by_name('nonexistent_form')
        
        assert found_form is None
    
    def test_get_all_forms(self, mock_mongo):
        """Test getting all forms"""
        form1 = create_test_form(mock_mongo, FormFactory(name='form1'))
        form2 = create_test_form(mock_mongo, FormFactory(name='form2'))
        
        forms = FormModel.get_all_forms()
        
        assert len(forms) == 2
        form_names = [f['name'] for f in forms]
        assert 'form1' in form_names
        assert 'form2' in form_names
    
    def test_get_user_forms(self, mock_mongo):
        """Test getting forms accessible to user"""
        # Create forms with different permissions
        form1 = create_test_form(mock_mongo, FormFactory(
            name='admin_form',
            permissions={'admin': ['user_123'], 'editor': [], 'viewer': []}
        ))
        form2 = create_test_form(mock_mongo, FormFactory(
            name='editor_form',
            permissions={'admin': ['other_user'], 'editor': ['user_123'], 'viewer': []}
        ))
        form3 = create_test_form(mock_mongo, FormFactory(
            name='viewer_form',
            permissions={'admin': ['other_user'], 'editor': [], 'viewer': ['user_123']}
        ))
        form4 = create_test_form(mock_mongo, FormFactory(
            name='no_access_form',
            permissions={'admin': ['other_user'], 'editor': [], 'viewer': []}
        ))
        
        user_forms = FormModel.get_user_forms('user_123')
        
        assert len(user_forms) == 3
        form_names = [f['name'] for f in user_forms]
        assert 'admin_form' in form_names
        assert 'editor_form' in form_names
        assert 'viewer_form' in form_names
        assert 'no_access_form' not in form_names
    
    def test_delete_form_success(self, mock_mongo):
        """Test successful form deletion"""
        form = create_test_form(mock_mongo, FormFactory(name='test_form'))
        
        result = FormModel.delete_form('test_form')
        
        assert result is True
        
        # Verify form is deleted
        found_form = FormModel.get_form_by_name('test_form')
        assert found_form is None
    
    def test_delete_form_not_found(self, mock_mongo):
        """Test form deletion when form not found"""
        result = FormModel.delete_form('nonexistent_form')
        
        assert result is False
    
    def test_add_submission_success(self, mock_mongo):
        """Test successful submission addition"""
        form = create_test_form(mock_mongo, FormFactory(name='test_form'))
        
        submission_data = {
            'id': 'submission_123',
            'responses': {'q_1': 'Test response'}
        }
        
        result = FormModel.add_submission('test_form', submission_data)
        
        assert result is True
        
        # Verify submission was added
        updated_form = FormModel.get_form_by_name('test_form')
        assert len(updated_form['submissions']) == 1
        assert updated_form['submissions'][0]['id'] == 'submission_123'
        assert 'submitted_at' in updated_form['submissions'][0]
    
    def test_add_submission_form_not_found(self, mock_mongo):
        """Test submission addition when form not found"""
        submission_data = {
            'id': 'submission_123',
            'responses': {'q_1': 'Test response'}
        }
        
        result = FormModel.add_submission('nonexistent_form', submission_data)
        
        assert result is False
    
    def test_delete_submission_success(self, mock_mongo):
        """Test successful submission deletion"""
        form_data = FormFactory(
            name='test_form',
            submissions=[
                {'id': 'submission_123', 'responses': {'q_1': 'Response 1'}},
                {'id': 'submission_456', 'responses': {'q_1': 'Response 2'}}
            ]
        )
        form = create_test_form(mock_mongo, form_data)
        
        result = FormModel.delete_submission('test_form', 'submission_123')
        
        assert result is True
        
        # Verify submission was deleted
        updated_form = FormModel.get_form_by_name('test_form')
        assert len(updated_form['submissions']) == 1
        assert updated_form['submissions'][0]['id'] == 'submission_456'
    
    def test_delete_submission_not_found(self, mock_mongo):
        """Test submission deletion when submission not found"""
        form = create_test_form(mock_mongo, FormFactory(name='test_form'))
        
        result = FormModel.delete_submission('test_form', 'nonexistent_submission')
        
        assert result is True  # MongoDB update returns success even if no match
    
    def test_delete_submission_form_not_found(self, mock_mongo):
        """Test submission deletion when form not found"""
        result = FormModel.delete_submission('nonexistent_form', 'submission_123')
        
        assert result is False
    
    def test_add_collaborator_success(self, mock_mongo):
        """Test successful collaborator addition"""
        form = create_test_form(mock_mongo, FormFactory(name='test_form'))
        
        result = FormModel.add_collaborator('test_form', 'user_456', 'editor')
        
        assert result is True
        
        # Verify collaborator was added
        updated_form = FormModel.get_form_by_name('test_form')
        assert 'user_456' in updated_form['permissions']['editor']
    
    def test_add_collaborator_form_not_found(self, mock_mongo):
        """Test collaborator addition when form not found"""
        result = FormModel.add_collaborator('nonexistent_form', 'user_456', 'editor')
        
        assert result is False
    
    def test_remove_collaborator_success(self, mock_mongo):
        """Test successful collaborator removal"""
        form_data = FormFactory(
            name='test_form',
            permissions={
                'admin': ['user_123'],
                'editor': ['user_456'],
                'viewer': ['user_789']
            }
        )
        form = create_test_form(mock_mongo, form_data)
        
        result = FormModel.remove_collaborator('test_form', 'user_456')
        
        assert result is True
        
        # Verify collaborator was removed
        updated_form = FormModel.get_form_by_name('test_form')
        assert 'user_456' not in updated_form['permissions']['editor']
        assert 'user_789' in updated_form['permissions']['viewer']  # Other collaborators remain
    
    def test_remove_collaborator_from_multiple_roles(self, mock_mongo):
        """Test collaborator removal from multiple roles"""
        form_data = FormFactory(
            name='test_form',
            permissions={
                'admin': ['user_123'],
                'editor': ['user_456'],
                'viewer': ['user_456']  # Same user in multiple roles
            }
        )
        form = create_test_form(mock_mongo, form_data)
        
        result = FormModel.remove_collaborator('test_form', 'user_456')
        
        assert result is True
        
        # Verify collaborator was removed from all roles
        updated_form = FormModel.get_form_by_name('test_form')
        assert 'user_456' not in updated_form['permissions']['editor']
        assert 'user_456' not in updated_form['permissions']['viewer']
    
    def test_remove_collaborator_not_found(self, mock_mongo):
        """Test collaborator removal when collaborator not found"""
        form = create_test_form(mock_mongo, FormFactory(name='test_form'))
        
        result = FormModel.remove_collaborator('test_form', 'nonexistent_user')
        
        assert result is True  # MongoDB update returns success even if no match
    
    def test_remove_collaborator_form_not_found(self, mock_mongo):
        """Test collaborator removal when form not found"""
        result = FormModel.remove_collaborator('nonexistent_form', 'user_456')
        
        assert result is False


@pytest.mark.database
class TestDatabaseConnection:
    """Test database connection and configuration"""
    
    def test_database_initialization(self, mock_mongo):
        """Test database initialization"""
        from database import db_manager
        
        assert db_manager.db is not None
        assert db_manager.users_collection is not None
        assert db_manager.forms_collection is not None
    
    def test_collection_access(self, mock_mongo):
        """Test collection access methods"""
        from database import db_manager
        
        users_collection = db_manager.get_users_collection()
        forms_collection = db_manager.get_forms_collection()
        database = db_manager.get_database()
        
        assert users_collection is not None
        assert forms_collection is not None
        assert database is not None