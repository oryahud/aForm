"""
Collaboration tests for aForm application
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime

from tests.conftest import UserFactory, FormFactory, create_test_user, create_test_form


@pytest.mark.collaboration
class TestUserInvitation:
    """Test user invitation functionality"""
    
    def test_invite_user_success(self, client, authenticated_session, mock_mail):
        """Test successful user invitation"""
        # Create form with admin permission for authenticated user
        form = FormFactory(
            name='test_form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []}
        )
        
        # Create target user to invite
        invited_user = UserFactory(id='invited_user_123', email='invited@example.com')
        
        invitation_data = {
            'email': 'invited@example.com',
            'role': 'editor'
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.UserModel.get_user_by_email', return_value=invited_user), \
             patch('models.FormModel.add_collaborator', return_value=True) as mock_add:
            
            response = client.post('/api/form/test_form/invite',
                                 data=json.dumps(invitation_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            response_data = json.loads(response.data)
            assert 'invited as editor' in response_data['message']
            assert response_data['user']['email'] == 'invited@example.com'
            assert response_data['user']['role'] == 'editor'
            mock_add.assert_called_once_with('test_form', 'invited_user_123', 'editor')
    
    def test_invite_user_form_not_found(self, client, authenticated_session):
        """Test inviting user to non-existent form"""
        invitation_data = {
            'email': 'user@example.com',
            'role': 'editor'
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=None):
            response = client.post('/api/form/nonexistent_form/invite',
                                 data=json.dumps(invitation_data),
                                 content_type='application/json')
            
            assert response.status_code == 404
            response_data = json.loads(response.data)
            assert 'Form not found' in response_data['error']
    
    def test_invite_user_not_admin(self, client, authenticated_session):
        """Test inviting user without admin permission"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': ['other_user'], 'editor': [authenticated_session['id']], 'viewer': []}
        )
        
        invitation_data = {
            'email': 'user@example.com',
            'role': 'editor'
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form):
            response = client.post('/api/form/test_form/invite',
                                 data=json.dumps(invitation_data),
                                 content_type='application/json')
            
            assert response.status_code == 403
            response_data = json.loads(response.data)
            assert 'Only form admins can invite users' in response_data['error']
    
    def test_invite_user_empty_email(self, client, authenticated_session):
        """Test inviting user with empty email"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []}
        )
        
        invitation_data = {
            'email': '',
            'role': 'editor'
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form):
            response = client.post('/api/form/test_form/invite',
                                 data=json.dumps(invitation_data),
                                 content_type='application/json')
            
            assert response.status_code == 400
            response_data = json.loads(response.data)
            assert 'Email is required' in response_data['error']
    
    def test_invite_user_invalid_role(self, client, authenticated_session):
        """Test inviting user with invalid role"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []}
        )
        
        invitation_data = {
            'email': 'user@example.com',
            'role': 'invalid_role'
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form):
            response = client.post('/api/form/test_form/invite',
                                 data=json.dumps(invitation_data),
                                 content_type='application/json')
            
            assert response.status_code == 400
            response_data = json.loads(response.data)
            assert 'Invalid role' in response_data['error']
    
    def test_invite_user_not_found(self, client, authenticated_session):
        """Test inviting non-existent user"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []}
        )
        
        invitation_data = {
            'email': 'nonexistent@example.com',
            'role': 'editor'
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.UserModel.get_user_by_email', return_value=None):
            
            response = client.post('/api/form/test_form/invite',
                                 data=json.dumps(invitation_data),
                                 content_type='application/json')
            
            assert response.status_code == 404
            response_data = json.loads(response.data)
            assert 'User not found' in response_data['error']
    
    def test_invite_user_already_has_access(self, client, authenticated_session):
        """Test inviting user who already has access"""
        invited_user = UserFactory(id='invited_user_123', email='invited@example.com')
        form = FormFactory(
            name='test_form',
            permissions={
                'admin': [authenticated_session['id']], 
                'editor': ['invited_user_123'], 
                'viewer': []
            }
        )
        
        invitation_data = {
            'email': 'invited@example.com',
            'role': 'viewer'
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.UserModel.get_user_by_email', return_value=invited_user):
            
            response = client.post('/api/form/test_form/invite',
                                 data=json.dumps(invitation_data),
                                 content_type='application/json')
            
            assert response.status_code == 400
            response_data = json.loads(response.data)
            assert 'already has access' in response_data['error']
    
    def test_invite_user_with_email_sending(self, client, authenticated_session, mock_mail):
        """Test user invitation with email sending"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []}
        )
        
        invited_user = UserFactory(id='invited_user_123', email='invited@example.com')
        
        invitation_data = {
            'email': 'invited@example.com',
            'role': 'editor'
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.UserModel.get_user_by_email', return_value=invited_user), \
             patch('models.FormModel.add_collaborator', return_value=True), \
             patch('app.send_invitation_email', return_value=True) as mock_send_email:
            
            response = client.post('/api/form/test_form/invite',
                                 data=json.dumps(invitation_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            response_data = json.loads(response.data)
            assert '(email sent)' in response_data['message']
            mock_send_email.assert_called_once()


@pytest.mark.collaboration
class TestCollaboratorManagement:
    """Test collaborator management functionality"""
    
    def test_get_collaborators_success(self, client, authenticated_session):
        """Test successful collaborator retrieval"""
        # Create users
        admin_user = UserFactory(id='admin_123', name='Admin User', email='admin@example.com')
        editor_user = UserFactory(id='editor_123', name='Editor User', email='editor@example.com')
        viewer_user = UserFactory(id='viewer_123', name='Viewer User', email='viewer@example.com')
        
        form = FormFactory(
            name='test_form',
            created_by='admin_123',
            permissions={
                'admin': ['admin_123'], 
                'editor': ['editor_123'], 
                'viewer': ['viewer_123']
            }
        )
        
        all_users = [admin_user, editor_user, viewer_user]
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.UserModel.get_all_users', return_value=all_users):
            
            response = client.get('/api/form/test_form/collaborators')
            
            assert response.status_code == 200
            response_data = json.loads(response.data)
            collaborators = response_data['collaborators']
            
            assert len(collaborators) == 3
            
            # Check admin user
            admin_collab = next(c for c in collaborators if c['role'] == 'admin')
            assert admin_collab['name'] == 'Admin User'
            assert admin_collab['is_creator'] is True
            
            # Check editor user
            editor_collab = next(c for c in collaborators if c['role'] == 'editor')
            assert editor_collab['name'] == 'Editor User'
            assert editor_collab['is_creator'] is False
            
            # Check viewer user
            viewer_collab = next(c for c in collaborators if c['role'] == 'viewer')
            assert viewer_collab['name'] == 'Viewer User'
            assert viewer_collab['is_creator'] is False
    
    def test_get_collaborators_form_not_found(self, client, authenticated_session):
        """Test getting collaborators for non-existent form"""
        with patch('models.FormModel.get_form_by_name', return_value=None):
            response = client.get('/api/form/nonexistent_form/collaborators')
            
            assert response.status_code == 404
            response_data = json.loads(response.data)
            assert 'Form not found' in response_data['error']
    
    def test_get_collaborators_no_permission(self, client, authenticated_session):
        """Test getting collaborators without permission"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': ['other_user'], 'editor': [], 'viewer': []}
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form):
            response = client.get('/api/form/test_form/collaborators')
            
            assert response.status_code == 403
            response_data = json.loads(response.data)
            assert 'Access denied' in response_data['error']
    
    def test_get_collaborators_as_editor(self, client, authenticated_session):
        """Test getting collaborators as editor"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': ['other_user'], 'editor': [authenticated_session['id']], 'viewer': []}
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.UserModel.get_all_users', return_value=[]):
            
            response = client.get('/api/form/test_form/collaborators')
            
            assert response.status_code == 200


@pytest.mark.collaboration
class TestCollaboratorRemoval:
    """Test collaborator removal functionality"""
    
    def test_remove_collaborator_success(self, client, authenticated_session):
        """Test successful collaborator removal"""
        form = FormFactory(
            name='test_form',
            created_by=authenticated_session['id'],
            permissions={
                'admin': [authenticated_session['id']], 
                'editor': ['user_to_remove'], 
                'viewer': []
            }
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.remove_collaborator', return_value=True) as mock_remove:
            
            response = client.delete('/api/form/test_form/collaborators/user_to_remove')
            
            assert response.status_code == 200
            response_data = json.loads(response.data)
            assert 'Collaborator removed successfully' in response_data['message']
            mock_remove.assert_called_once_with('test_form', 'user_to_remove')
    
    def test_remove_collaborator_form_not_found(self, client, authenticated_session):
        """Test removing collaborator from non-existent form"""
        with patch('models.FormModel.get_form_by_name', return_value=None):
            response = client.delete('/api/form/nonexistent_form/collaborators/user_123')
            
            assert response.status_code == 404
            response_data = json.loads(response.data)
            assert 'Form not found' in response_data['error']
    
    def test_remove_collaborator_not_admin(self, client, authenticated_session):
        """Test removing collaborator without admin permission"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': ['other_user'], 'editor': [authenticated_session['id']], 'viewer': []}
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form):
            response = client.delete('/api/form/test_form/collaborators/user_123')
            
            assert response.status_code == 403
            response_data = json.loads(response.data)
            assert 'Only form admins can remove collaborators' in response_data['error']
    
    def test_remove_collaborator_creator(self, client, authenticated_session):
        """Test removing form creator (should fail)"""
        form = FormFactory(
            name='test_form',
            created_by='form_creator',
            permissions={'admin': [authenticated_session['id'], 'form_creator'], 'editor': [], 'viewer': []}
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form):
            response = client.delete('/api/form/test_form/collaborators/form_creator')
            
            assert response.status_code == 400
            response_data = json.loads(response.data)
            assert 'Cannot remove form creator' in response_data['error']
    
    def test_remove_collaborator_not_found(self, client, authenticated_session):
        """Test removing non-existent collaborator"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []}
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form):
            response = client.delete('/api/form/test_form/collaborators/nonexistent_user')
            
            assert response.status_code == 404
            response_data = json.loads(response.data)
            assert 'User not found in collaborators' in response_data['error']
    
    def test_remove_collaborator_failure(self, client, authenticated_session):
        """Test collaborator removal failure"""
        form = FormFactory(
            name='test_form',
            permissions={
                'admin': [authenticated_session['id']], 
                'editor': ['user_to_remove'], 
                'viewer': []
            }
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.remove_collaborator', return_value=False):
            
            response = client.delete('/api/form/test_form/collaborators/user_to_remove')
            
            assert response.status_code == 500
            response_data = json.loads(response.data)
            assert 'Failed to remove collaborator' in response_data['error']


@pytest.mark.collaboration
class TestPermissionLevels:
    """Test different permission levels and access controls"""
    
    def test_admin_permissions(self, client, authenticated_session):
        """Test admin permissions for form management"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []}
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form):
            # Admin can access form editor
            response = client.get('/form/test_form')
            assert response.status_code == 200
            
            # Admin can view submissions
            response = client.get('/form/test_form/submissions')
            assert response.status_code == 200
            
            # Admin can get collaborators
            with patch('models.UserModel.get_all_users', return_value=[]):
                response = client.get('/api/form/test_form/collaborators')
                assert response.status_code == 200
    
    def test_editor_permissions(self, client, authenticated_session):
        """Test editor permissions for form management"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': ['other_user'], 'editor': [authenticated_session['id']], 'viewer': []}
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form):
            # Editor can access form editor
            response = client.get('/form/test_form')
            assert response.status_code == 200
            
            # Editor can view submissions
            response = client.get('/form/test_form/submissions')
            assert response.status_code == 200
            
            # Editor can get collaborators
            with patch('models.UserModel.get_all_users', return_value=[]):
                response = client.get('/api/form/test_form/collaborators')
                assert response.status_code == 200
            
            # Editor cannot invite users (admin only)
            invitation_data = {'email': 'user@example.com', 'role': 'viewer'}
            response = client.post('/api/form/test_form/invite',
                                 data=json.dumps(invitation_data),
                                 content_type='application/json')
            assert response.status_code == 403
    
    def test_viewer_permissions(self, client, authenticated_session):
        """Test viewer permissions for form management"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': ['other_user'], 'editor': [], 'viewer': [authenticated_session['id']]}
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form):
            # Viewer cannot access form editor
            response = client.get('/form/test_form')
            assert response.status_code == 403
            
            # Viewer can view submissions
            response = client.get('/form/test_form/submissions')
            assert response.status_code == 200
            
            # Viewer cannot get collaborators (edit permission required)
            response = client.get('/api/form/test_form/collaborators')
            assert response.status_code == 403
    
    def test_no_permissions(self, client, authenticated_session):
        """Test access without any permissions"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': ['other_user'], 'editor': [], 'viewer': []}
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form):
            # No access to form editor
            response = client.get('/form/test_form')
            assert response.status_code == 403
            
            # No access to submissions
            response = client.get('/form/test_form/submissions')
            assert response.status_code == 403
            
            # No access to collaborators
            response = client.get('/api/form/test_form/collaborators')
            assert response.status_code == 403


@pytest.mark.collaboration
class TestEmailInvitations:
    """Test email invitation functionality"""
    
    def test_email_invitation_configured(self, client, authenticated_session, mock_mail):
        """Test email invitation when mail is configured"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []}
        )
        
        invited_user = UserFactory(id='invited_user', email='invited@example.com')
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.UserModel.get_user_by_email', return_value=invited_user), \
             patch('models.FormModel.add_collaborator', return_value=True), \
             patch('app.send_invitation_email', return_value=True) as mock_send:
            
            invitation_data = {'email': 'invited@example.com', 'role': 'editor'}
            response = client.post('/api/form/test_form/invite',
                                 data=json.dumps(invitation_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            mock_send.assert_called_once_with(
                to_email='invited@example.com',
                inviter_name=authenticated_session['name'],
                form_name='test_form',
                role='editor',
                form_url='http://localhost/form/test_form'
            )
    
    def test_email_invitation_failed(self, client, authenticated_session):
        """Test email invitation when sending fails"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []}
        )
        
        invited_user = UserFactory(id='invited_user', email='invited@example.com')
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.UserModel.get_user_by_email', return_value=invited_user), \
             patch('models.FormModel.add_collaborator', return_value=True), \
             patch('app.send_invitation_email', return_value=False):
            
            invitation_data = {'email': 'invited@example.com', 'role': 'editor'}
            response = client.post('/api/form/test_form/invite',
                                 data=json.dumps(invitation_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            response_data = json.loads(response.data)
            assert '(email failed)' in response_data['message']
    
    def test_email_invitation_not_configured(self, client, authenticated_session):
        """Test email invitation when mail is not configured"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []}
        )
        
        invited_user = UserFactory(id='invited_user', email='invited@example.com')
        
        # Mock mail not configured scenario
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.UserModel.get_user_by_email', return_value=invited_user), \
             patch('models.FormModel.add_collaborator', return_value=True), \
             patch('app.send_invitation_email') as mock_send:
            
            # Simulate email not configured (returns True but prints message)
            mock_send.return_value = True
            
            invitation_data = {'email': 'invited@example.com', 'role': 'editor'}
            response = client.post('/api/form/test_form/invite',
                                 data=json.dumps(invitation_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            mock_send.assert_called_once()