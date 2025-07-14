"""
Integration tests for aForm application
These tests verify end-to-end functionality across multiple components
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime

from tests.conftest import UserFactory, FormFactory, create_test_user, create_test_form, authenticate_user


@pytest.mark.integration
class TestCompleteFormWorkflow:
    """Test complete form creation and management workflow"""
    
    def test_complete_form_lifecycle(self, client, authenticated_session, mock_mongo):
        """Test complete form lifecycle from creation to deletion"""
        # 1. Create a form
        form_data = {'name': 'Integration Test Form'}
        
        with patch('models.FormModel.get_form_by_name', return_value=None), \
             patch('models.FormModel.create_form') as mock_create:
            
            response = client.post('/create-form',
                                 data=json.dumps(form_data),
                                 content_type='application/json')
            assert response.status_code == 200
            mock_create.assert_called_once()
        
        # 2. Edit the form (add questions)
        form = FormFactory(
            name='Integration Test Form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []},
            questions=[{'id': 'q_1', 'title': 'Question 1', 'type': 'text', 'required': False}]
        )
        
        updated_questions = [
            {'id': 'q_1', 'title': 'Name', 'text': 'What is your name?', 'type': 'text', 'required': True},
            {'id': 'q_2', 'title': 'Email', 'text': 'What is your email?', 'type': 'email', 'required': False}
        ]
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.update_form') as mock_update:
            
            response = client.post('/api/form/Integration Test Form/save',
                                 data=json.dumps({'questions': updated_questions}),
                                 content_type='application/json')
            assert response.status_code == 200
            mock_update.assert_called_once()
        
        # 3. Publish the form
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.update_form') as mock_update:
            
            response = client.post('/api/form/Integration Test Form/publish')
            assert response.status_code == 200
            mock_update.assert_called_once()
        
        # 4. Submit to the form (as public user)
        published_form = {**form, 'status': 'published', 'questions': updated_questions}
        submission_data = {
            'responses': {
                'q_1': 'John Doe',
                'q_2': 'john@example.com'
            }
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=published_form), \
             patch('models.FormModel.add_submission', return_value=True) as mock_add_sub:
            
            response = client.post('/api/form/Integration Test Form/submit',
                                 data=json.dumps(submission_data),
                                 content_type='application/json')
            assert response.status_code == 200
            mock_add_sub.assert_called_once()
        
        # 5. View submissions
        form_with_submissions = {
            **published_form,
            'submissions': [
                {
                    'id': 'sub_1',
                    'submitted_at': datetime.now(),
                    'responses': {'q_1': 'John Doe', 'q_2': 'john@example.com'}
                }
            ]
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form_with_submissions):
            response = client.get('/form/Integration Test Form/submissions')
            assert response.status_code == 200
        
        # 6. Delete the form
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.delete_form', return_value=True) as mock_delete:
            
            response = client.delete('/api/form/Integration Test Form/delete')
            assert response.status_code == 200
            mock_delete.assert_called_once()
    
    def test_form_collaboration_workflow(self, client, authenticated_session, mock_mongo, mock_mail):
        """Test complete collaboration workflow"""
        # 1. Create form
        form = FormFactory(
            name='Collaboration Form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []}
        )
        
        # 2. Create users to invite
        editor_user = UserFactory(id='editor_123', email='editor@example.com', name='Editor User')
        viewer_user = UserFactory(id='viewer_123', email='viewer@example.com', name='Viewer User')
        
        # 3. Invite editor
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.UserModel.get_user_by_email', return_value=editor_user), \
             patch('models.FormModel.add_collaborator', return_value=True), \
             patch('app.send_invitation_email', return_value=True):
            
            invitation_data = {'email': 'editor@example.com', 'role': 'editor'}
            response = client.post('/api/form/Collaboration Form/invite',
                                 data=json.dumps(invitation_data),
                                 content_type='application/json')
            assert response.status_code == 200
        
        # 4. Invite viewer
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.UserModel.get_user_by_email', return_value=viewer_user), \
             patch('models.FormModel.add_collaborator', return_value=True), \
             patch('app.send_invitation_email', return_value=True):
            
            invitation_data = {'email': 'viewer@example.com', 'role': 'viewer'}
            response = client.post('/api/form/Collaboration Form/invite',
                                 data=json.dumps(invitation_data),
                                 content_type='application/json')
            assert response.status_code == 200
        
        # 5. Get collaborators list
        form_with_collabs = FormFactory(
            name='Collaboration Form',
            permissions={
                'admin': [authenticated_session['id']], 
                'editor': ['editor_123'], 
                'viewer': ['viewer_123']
            }
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form_with_collabs), \
             patch('models.UserModel.get_all_users', return_value=[authenticated_session, editor_user, viewer_user]):
            
            response = client.get('/api/form/Collaboration Form/collaborators')
            assert response.status_code == 200
            collaborators = json.loads(response.data)['collaborators']
            assert len(collaborators) == 3
        
        # 6. Remove collaborator
        with patch('models.FormModel.get_form_by_name', return_value=form_with_collabs), \
             patch('models.FormModel.remove_collaborator', return_value=True):
            
            response = client.delete('/api/form/Collaboration Form/collaborators/viewer_123')
            assert response.status_code == 200


@pytest.mark.integration
class TestUserJourney:
    """Test complete user journey scenarios"""
    
    def test_new_user_oauth_journey(self, client, mock_google_oauth):
        """Test new user OAuth authentication journey"""
        # 1. User tries to access protected resource
        response = client.get('/')
        assert response.status_code == 302  # Redirect to login
        
        # 2. User clicks login
        mock_google_oauth.authorize_redirect.return_value = MagicMock(status_code=302)
        response = client.get('/login')
        assert response.status_code == 302
        
        # 3. OAuth callback creates new user
        user_info = {
            'email': 'newuser@example.com',
            'name': 'New User',
            'picture': 'http://example.com/pic.jpg'
        }
        
        mock_response = MagicMock()
        mock_response.json.return_value = {'access_token': 'test_token'}
        
        mock_userinfo = MagicMock()
        mock_userinfo.json.return_value = user_info
        
        with patch('requests.post', return_value=mock_response), \
             patch('requests.get', return_value=mock_userinfo), \
             patch('models.UserModel.get_user_by_email', return_value=None), \
             patch('models.UserModel.create_user') as mock_create:
            
            new_user = UserFactory(**user_info)
            mock_create.return_value = new_user
            
            response = client.get('/auth/callback?code=test_code')
            assert response.status_code == 302  # Redirect to dashboard
            mock_create.assert_called_once()
        
        # 4. User can now access dashboard
        with client.session_transaction() as sess:
            sess['user'] = new_user
        
        with patch('auth.auth_manager.get_user_forms', return_value=[]):
            response = client.get('/')
            assert response.status_code == 200
    
    def test_form_creator_to_public_submission_journey(self, client, authenticated_session, mock_mongo):
        """Test journey from form creation to public submission"""
        # 1. User creates form
        with patch('models.FormModel.get_form_by_name', return_value=None), \
             patch('models.FormModel.create_form') as mock_create:
            
            form_data = {'name': 'Public Survey'}
            response = client.post('/create-form',
                                 data=json.dumps(form_data),
                                 content_type='application/json')
            assert response.status_code == 200
        
        # 2. User designs form
        form = FormFactory(
            name='Public Survey',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []},
            status='draft'
        )
        
        questions = [
            {
                'id': 'q_1',
                'title': 'Satisfaction',
                'text': 'How satisfied are you with our service?',
                'type': 'radio',
                'required': True
            },
            {
                'id': 'q_2',
                'title': 'Comments',
                'text': 'Any additional comments?',
                'type': 'textarea',
                'required': False
            }
        ]
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.update_form') as mock_update:
            
            response = client.post('/api/form/Public Survey/save',
                                 data=json.dumps({'questions': questions}),
                                 content_type='application/json')
            assert response.status_code == 200
        
        # 3. User publishes form
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.update_form') as mock_publish:
            
            response = client.post('/api/form/Public Survey/publish')
            assert response.status_code == 200
            response_data = json.loads(response.data)
            assert 'share_url' in response_data
        
        # 4. Public user visits form
        published_form = {**form, 'status': 'published', 'questions': questions}
        
        with patch('models.FormModel.get_form_by_name', return_value=published_form):
            # Clear session to simulate public user
            with client.session_transaction() as sess:
                sess.clear()
            
            response = client.get('/submit/Public Survey')
            assert response.status_code == 200
            assert b'How satisfied are you' in response.data
        
        # 5. Public user submits form
        submission_data = {
            'responses': {
                'q_1': 'Very Satisfied',
                'q_2': 'Great service, keep it up!'
            }
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=published_form), \
             patch('models.FormModel.add_submission', return_value=True):
            
            response = client.post('/api/form/Public Survey/submit',
                                 data=json.dumps(submission_data),
                                 content_type='application/json')
            assert response.status_code == 200
        
        # 6. Form owner views submissions
        # Re-authenticate as form owner
        with client.session_transaction() as sess:
            sess['user'] = authenticated_session
        
        form_with_submissions = {
            **published_form,
            'submissions': [
                {
                    'id': 'sub_1',
                    'submitted_at': datetime.now(),
                    'responses': {
                        'q_1': 'Very Satisfied',
                        'q_2': 'Great service, keep it up!'
                    }
                }
            ]
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form_with_submissions):
            response = client.get('/form/Public Survey/submissions')
            assert response.status_code == 200
            assert b'Very Satisfied' in response.data


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Test error handling across multiple components"""
    
    def test_database_failure_handling(self, client, authenticated_session):
        """Test handling of database failures across operations"""
        # Test form creation failure
        with patch('models.FormModel.get_form_by_name', return_value=None), \
             patch('models.FormModel.create_form', side_effect=Exception("Database error")):
            
            form_data = {'name': 'Test Form'}
            response = client.post('/create-form',
                                 data=json.dumps(form_data),
                                 content_type='application/json')
            # Should handle gracefully (implementation specific)
            assert response.status_code in [200, 500]  # Depends on error handling
        
        # Test form update failure
        form = FormFactory(
            name='test_form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []}
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.update_form', side_effect=ValueError("Update failed")):
            
            response = client.post('/api/form/test_form/save',
                                 data=json.dumps({'questions': []}),
                                 content_type='application/json')
            assert response.status_code == 500
        
        # Test submission failure
        published_form = FormFactory(name='test_form', status='published')
        
        with patch('models.FormModel.get_form_by_name', return_value=published_form), \
             patch('models.FormModel.add_submission', return_value=False):
            
            submission_data = {'responses': {'q_1': 'test'}}
            response = client.post('/api/form/test_form/submit',
                                 data=json.dumps(submission_data),
                                 content_type='application/json')
            assert response.status_code == 500
    
    def test_permission_edge_cases(self, client, authenticated_session):
        """Test permission edge cases across operations"""
        # Form with no permissions set
        form_no_perms = FormFactory(name='test_form')
        del form_no_perms['permissions']
        
        with patch('models.FormModel.get_form_by_name', return_value=form_no_perms):
            response = client.get('/form/test_form')
            assert response.status_code == 403
        
        # Form with empty permissions
        form_empty_perms = FormFactory(
            name='test_form',
            permissions={'admin': [], 'editor': [], 'viewer': []}
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form_empty_perms):
            response = client.get('/form/test_form')
            assert response.status_code == 403
        
        # Form with malformed permissions
        form_bad_perms = FormFactory(
            name='test_form',
            permissions={'admin': 'not_a_list', 'editor': None}
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form_bad_perms):
            # Should handle gracefully without crashing
            response = client.get('/form/test_form')
            assert response.status_code in [403, 500]


@pytest.mark.integration
class TestDataConsistency:
    """Test data consistency across operations"""
    
    def test_form_question_consistency(self, client, authenticated_session):
        """Test consistency between form questions and submissions"""
        # Create form with specific questions
        form = FormFactory(
            name='test_form',
            status='published',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []},
            questions=[
                {'id': 'q_1', 'title': 'Name', 'type': 'text', 'required': True},
                {'id': 'q_2', 'title': 'Age', 'type': 'number', 'required': False}
            ]
        )
        
        # Submit with matching question IDs
        submission_data = {
            'responses': {
                'q_1': 'John Doe',
                'q_2': 25
            }
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.add_submission', return_value=True) as mock_add:
            
            response = client.post('/api/form/test_form/submit',
                                 data=json.dumps(submission_data),
                                 content_type='application/json')
            assert response.status_code == 200
            
            # Verify submission structure matches form questions
            call_args = mock_add.call_args
            submission = call_args[0][1]
            
            assert 'q_1' in submission['responses']
            assert 'q_2' in submission['responses']
            assert submission['responses']['q_1'] == 'John Doe'
            assert submission['responses']['q_2'] == 25
        
        # Submit with extra question IDs (should be accepted)
        submission_with_extra = {
            'responses': {
                'q_1': 'Jane Doe',
                'q_2': 30,
                'q_3': 'Extra data'  # Not in form definition
            }
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.add_submission', return_value=True):
            
            response = client.post('/api/form/test_form/submit',
                                 data=json.dumps(submission_with_extra),
                                 content_type='application/json')
            assert response.status_code == 200  # Should accept extra data
        
        # Submit with missing question IDs (should be accepted)
        submission_partial = {
            'responses': {
                'q_1': 'Bob Smith'
                # q_2 missing
            }
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.add_submission', return_value=True):
            
            response = client.post('/api/form/test_form/submit',
                                 data=json.dumps(submission_partial),
                                 content_type='application/json')
            assert response.status_code == 200  # Should accept partial data
    
    def test_user_permission_consistency(self, client, authenticated_session):
        """Test consistency of user permissions across operations"""
        # User starts as form admin
        form = FormFactory(
            name='test_form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []}
        )
        
        # Verify admin can perform admin operations
        with patch('models.FormModel.get_form_by_name', return_value=form):
            # Can edit form
            response = client.get('/form/test_form')
            assert response.status_code == 200
            
            # Can view submissions
            response = client.get('/form/test_form/submissions')
            assert response.status_code == 200
        
        # Simulate user being downgraded to editor
        form_downgraded = FormFactory(
            name='test_form',
            permissions={'admin': ['other_user'], 'editor': [authenticated_session['id']], 'viewer': []}
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form_downgraded):
            # Can still edit form
            response = client.get('/form/test_form')
            assert response.status_code == 200
            
            # Can still view submissions
            response = client.get('/form/test_form/submissions')
            assert response.status_code == 200
            
            # Cannot invite users (admin only)
            invitation_data = {'email': 'user@example.com', 'role': 'viewer'}
            response = client.post('/api/form/test_form/invite',
                                 data=json.dumps(invitation_data),
                                 content_type='application/json')
            assert response.status_code == 403
        
        # Simulate user being removed from form
        form_no_access = FormFactory(
            name='test_form',
            permissions={'admin': ['other_user'], 'editor': [], 'viewer': []}
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form_no_access):
            # Cannot access form
            response = client.get('/form/test_form')
            assert response.status_code == 403
            
            # Cannot view submissions
            response = client.get('/form/test_form/submissions')
            assert response.status_code == 403