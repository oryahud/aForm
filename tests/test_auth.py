"""
Authentication tests for aForm application
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from auth import auth_manager, login_required, role_required, permission_required
from models import UserModel
from tests.conftest import UserFactory, create_test_user


@pytest.mark.auth
class TestAuthManager:
    """Test AuthManager class"""
    
    def test_init_app_with_google_credentials(self, app):
        """Test initialization with Google OAuth credentials"""
        app.config['GOOGLE_CLIENT_ID'] = 'test_client_id'
        app.config['GOOGLE_CLIENT_SECRET'] = 'test_client_secret'
        
        with patch('auth.OAuth') as mock_oauth:
            mock_google = MagicMock()
            mock_oauth.return_value.register.return_value = mock_google
            
            auth_manager.init_app(app)
            
            assert auth_manager.google is not None
            mock_oauth.return_value.register.assert_called_once()
    
    def test_init_app_without_google_credentials(self, app):
        """Test initialization without Google OAuth credentials"""
        app.config['GOOGLE_CLIENT_ID'] = None
        app.config['GOOGLE_CLIENT_SECRET'] = None
        
        auth_manager.init_app(app)
        
        assert auth_manager.google is None
    
    def test_load_users(self, mock_mongo):
        """Test loading users from database"""
        # Create test users
        user1 = create_test_user(mock_mongo, UserFactory())
        user2 = create_test_user(mock_mongo, UserFactory())
        
        users = auth_manager.load_users()
        
        assert len(users) == 2
        assert any(u['email'] == user1['email'] for u in users)
        assert any(u['email'] == user2['email'] for u in users)
    
    def test_get_user_by_email(self, mock_mongo):
        """Test getting user by email"""
        user = create_test_user(mock_mongo, UserFactory(email='test@example.com'))
        
        found_user = auth_manager.get_user_by_email('test@example.com')
        
        assert found_user is not None
        assert found_user['email'] == 'test@example.com'
    
    def test_get_user_by_email_not_found(self, mock_mongo):
        """Test getting user by email when not found"""
        found_user = auth_manager.get_user_by_email('nonexistent@example.com')
        
        assert found_user is None
    
    def test_create_or_update_user_new_user(self, mock_mongo):
        """Test creating new user"""
        user_info = {
            'email': 'new@example.com',
            'name': 'New User',
            'picture': 'http://example.com/pic.jpg'
        }
        
        with patch('models.UserModel.create_user') as mock_create:
            mock_create.return_value = UserFactory(**user_info)
            
            user = auth_manager.create_or_update_user(user_info)
            
            mock_create.assert_called_once_with(user_info)
            assert user['email'] == 'new@example.com'
    
    def test_create_or_update_user_existing_user(self, mock_mongo):
        """Test updating existing user"""
        existing_user = create_test_user(mock_mongo, UserFactory(email='existing@example.com'))
        
        user_info = {
            'email': 'existing@example.com',
            'name': 'Updated Name',
            'picture': 'http://example.com/new_pic.jpg'
        }
        
        with patch('models.UserModel.update_user') as mock_update:
            mock_update.return_value = {**existing_user, 'name': 'Updated Name'}
            
            user = auth_manager.create_or_update_user(user_info)
            
            mock_update.assert_called_once()
            assert user['name'] == 'Updated Name'
    
    def test_get_current_user_authenticated(self, client, sample_user):
        """Test getting current user when authenticated"""
        with client.session_transaction() as sess:
            sess['user'] = sample_user
        
        with client.application.test_request_context():
            current_user = auth_manager.get_current_user()
            
            assert current_user is not None
            assert current_user['email'] == sample_user['email']
    
    def test_get_current_user_not_authenticated(self, client):
        """Test getting current user when not authenticated"""
        with client.application.test_request_context():
            current_user = auth_manager.get_current_user()
            
            assert current_user is None
    
    def test_is_authenticated_true(self, client, sample_user):
        """Test authentication check when user is authenticated"""
        with client.session_transaction() as sess:
            sess['user'] = sample_user
        
        with client.application.test_request_context():
            assert auth_manager.is_authenticated() is True
    
    def test_is_authenticated_false(self, client):
        """Test authentication check when user is not authenticated"""
        with client.application.test_request_context():
            assert auth_manager.is_authenticated() is False
    
    def test_has_role_admin(self, client, admin_user):
        """Test role check for admin user"""
        with client.session_transaction() as sess:
            sess['user'] = admin_user
        
        with client.application.test_request_context():
            assert auth_manager.has_role('admin') is True
            assert auth_manager.has_role('user') is False
    
    def test_has_role_user(self, client, sample_user):
        """Test role check for regular user"""
        with client.session_transaction() as sess:
            sess['user'] = sample_user
        
        with client.application.test_request_context():
            assert auth_manager.has_role('user') is True
            assert auth_manager.has_role('admin') is False
    
    def test_has_role_not_authenticated(self, client):
        """Test role check when not authenticated"""
        with client.application.test_request_context():
            assert auth_manager.has_role('user') is False
            assert auth_manager.has_role('admin') is False
    
    def test_has_permission_admin(self, client, admin_user):
        """Test permission check for admin user"""
        with client.session_transaction() as sess:
            sess['user'] = admin_user
        
        with client.application.test_request_context():
            assert auth_manager.has_permission('create_form') is True
            assert auth_manager.has_permission('manage_users') is True
    
    def test_has_permission_user(self, client, sample_user):
        """Test permission check for regular user"""
        with client.session_transaction() as sess:
            sess['user'] = sample_user
        
        with client.application.test_request_context():
            assert auth_manager.has_permission('create_form') is True
            assert auth_manager.has_permission('manage_users') is False
    
    def test_has_form_permission_admin(self, client, admin_user, sample_form):
        """Test form permission check for admin user"""
        with client.session_transaction() as sess:
            sess['user'] = admin_user
        
        with client.application.test_request_context():
            assert auth_manager.has_form_permission(sample_form, 'admin') is True
            assert auth_manager.has_form_permission(sample_form, 'edit') is True
    
    def test_has_form_permission_form_admin(self, client, sample_user, sample_form):
        """Test form permission check for form admin"""
        sample_form['permissions']['admin'] = [sample_user['id']]
        
        with client.session_transaction() as sess:
            sess['user'] = sample_user
        
        with client.application.test_request_context():
            assert auth_manager.has_form_permission(sample_form, 'admin') is True
            assert auth_manager.has_form_permission(sample_form, 'edit') is True
    
    def test_has_form_permission_editor(self, client, sample_user, sample_form):
        """Test form permission check for editor"""
        sample_form['permissions']['editor'] = [sample_user['id']]
        
        with client.session_transaction() as sess:
            sess['user'] = sample_user
        
        with client.application.test_request_context():
            assert auth_manager.has_form_permission(sample_form, 'admin') is False
            assert auth_manager.has_form_permission(sample_form, 'edit') is True
            assert auth_manager.has_form_permission(sample_form, 'view_submissions') is True
    
    def test_has_form_permission_viewer(self, client, sample_user, sample_form):
        """Test form permission check for viewer"""
        sample_form['permissions']['viewer'] = [sample_user['id']]
        
        with client.session_transaction() as sess:
            sess['user'] = sample_user
        
        with client.application.test_request_context():
            assert auth_manager.has_form_permission(sample_form, 'admin') is False
            assert auth_manager.has_form_permission(sample_form, 'edit') is False
            assert auth_manager.has_form_permission(sample_form, 'view_submissions') is True
    
    def test_has_form_permission_no_access(self, client, sample_user, sample_form):
        """Test form permission check when user has no access"""
        with client.session_transaction() as sess:
            sess['user'] = sample_user
        
        with client.application.test_request_context():
            assert auth_manager.has_form_permission(sample_form, 'admin') is False
            assert auth_manager.has_form_permission(sample_form, 'edit') is False
            assert auth_manager.has_form_permission(sample_form, 'view_submissions') is False
    
    def test_get_user_forms_admin(self, client, admin_user):
        """Test getting user forms for admin user"""
        with client.session_transaction() as sess:
            sess['user'] = admin_user
        
        with patch('models.FormModel.get_all_forms') as mock_get_all:
            mock_get_all.return_value = [{'name': 'form1'}, {'name': 'form2'}]
            
            with client.application.test_request_context():
                forms = auth_manager.get_user_forms()
                
                assert len(forms) == 2
                mock_get_all.assert_called_once()
    
    def test_get_user_forms_regular_user(self, client, sample_user):
        """Test getting user forms for regular user"""
        with client.session_transaction() as sess:
            sess['user'] = sample_user
        
        with patch('models.FormModel.get_user_forms') as mock_get_user_forms:
            mock_get_user_forms.return_value = [{'name': 'user_form'}]
            
            with client.application.test_request_context():
                forms = auth_manager.get_user_forms()
                
                assert len(forms) == 1
                mock_get_user_forms.assert_called_once_with(sample_user['id'])


@pytest.mark.auth
class TestDecorators:
    """Test authentication decorators"""
    
    def test_login_required_authenticated(self, client, sample_user):
        """Test login_required decorator with authenticated user"""
        @login_required
        def protected_view():
            return 'success'
        
        with client.session_transaction() as sess:
            sess['user'] = sample_user
        
        with client.application.test_request_context():
            result = protected_view()
            assert result == 'success'
    
    def test_login_required_not_authenticated(self, client):
        """Test login_required decorator without authentication"""
        @login_required
        def protected_view():
            return 'success'
        
        with client.application.test_request_context():
            result = protected_view()
            # Should redirect to login
            assert result.status_code == 302
    
    def test_role_required_correct_role(self, client, admin_user):
        """Test role_required decorator with correct role"""
        @role_required('admin')
        def admin_view():
            return 'admin_success'
        
        with client.session_transaction() as sess:
            sess['user'] = admin_user
        
        with client.application.test_request_context():
            result = admin_view()
            assert result == 'admin_success'
    
    def test_role_required_incorrect_role(self, client, sample_user):
        """Test role_required decorator with incorrect role"""
        @role_required('admin')
        def admin_view():
            return 'admin_success'
        
        with client.session_transaction() as sess:
            sess['user'] = sample_user
        
        with client.application.test_request_context():
            result = admin_view()
            # Should return 403
            assert result[1] == 403
    
    def test_permission_required_has_permission(self, client, sample_user):
        """Test permission_required decorator with permission"""
        @permission_required('create_form')
        def create_form_view():
            return 'create_success'
        
        with client.session_transaction() as sess:
            sess['user'] = sample_user
        
        with client.application.test_request_context():
            result = create_form_view()
            assert result == 'create_success'
    
    def test_permission_required_no_permission(self, client, sample_user):
        """Test permission_required decorator without permission"""
        @permission_required('manage_users')
        def manage_users_view():
            return 'manage_success'
        
        with client.session_transaction() as sess:
            sess['user'] = sample_user
        
        with client.application.test_request_context():
            result = manage_users_view()
            # Should return 403
            assert result[1] == 403


@pytest.mark.auth
class TestAuthRoutes:
    """Test authentication routes"""
    
    def test_login_redirect_to_google(self, client, mock_google_oauth):
        """Test login route redirects to Google OAuth"""
        mock_google_oauth.authorize_redirect.return_value = MagicMock(status_code=302)
        
        response = client.get('/login')
        
        assert response.status_code == 302
        mock_google_oauth.authorize_redirect.assert_called_once()
    
    def test_login_already_authenticated(self, client, authenticated_session):
        """Test login route when already authenticated"""
        response = client.get('/login')
        
        assert response.status_code == 302
        assert response.location.endswith('/')
    
    def test_login_page_not_authenticated(self, client):
        """Test login page when not authenticated"""
        response = client.get('/login-page')
        
        assert response.status_code == 200
        assert b'login' in response.data.lower()
    
    def test_login_page_authenticated(self, client, authenticated_session):
        """Test login page when authenticated"""
        response = client.get('/login-page')
        
        assert response.status_code == 302
        assert response.location.endswith('/')
    
    def test_logout(self, client, authenticated_session):
        """Test logout route"""
        response = client.get('/logout')
        
        assert response.status_code == 302
        assert response.location.endswith('/login-page')
    
    def test_dev_login_development(self, client):
        """Test development login route"""
        with patch.dict('os.environ', {'FLASK_ENV': 'development'}):
            response = client.get('/dev-login')
            
            assert response.status_code == 302
            assert response.location.endswith('/')
    
    def test_dev_login_production(self, client):
        """Test development login route in production"""
        with patch.dict('os.environ', {'FLASK_ENV': 'production'}):
            response = client.get('/dev-login')
            
            assert response.status_code == 302
            assert response.location.endswith('/login-page')
    
    def test_auth_callback_success(self, client, mock_google_oauth):
        """Test successful OAuth callback"""
        mock_response = MagicMock()
        mock_response.json.return_value = {'access_token': 'test_token'}
        
        mock_userinfo = MagicMock()
        mock_userinfo.json.return_value = {
            'email': 'test@example.com',
            'name': 'Test User',
            'picture': 'http://example.com/pic.jpg'
        }
        
        with patch('requests.post', return_value=mock_response), \
             patch('requests.get', return_value=mock_userinfo), \
             patch('auth.auth_manager.create_or_update_user') as mock_create:
            
            mock_create.return_value = UserFactory(email='test@example.com')
            
            response = client.get('/auth/callback?code=test_code')
            
            assert response.status_code == 302
            assert response.location.endswith('/')
    
    def test_auth_callback_no_code(self, client):
        """Test OAuth callback without code"""
        response = client.get('/auth/callback')
        
        assert response.status_code == 200
        assert b'error' in response.data.lower()
    
    def test_test_callback_route(self, client):
        """Test callback test route"""
        response = client.get('/test-callback')
        
        assert response.status_code == 200
        assert b'Callback Test' in response.data