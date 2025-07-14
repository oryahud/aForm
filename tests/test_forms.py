"""
Form management tests for aForm application
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime

from tests.conftest import UserFactory, FormFactory, create_test_user, create_test_form, authenticate_user


@pytest.mark.forms
class TestFormCreation:
    """Test form creation functionality"""
    
    def test_create_form_success(self, client, authenticated_session, mock_mongo):
        """Test successful form creation"""
        form_data = {
            'name': 'New Test Form'
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=None), \
             patch('models.FormModel.create_form') as mock_create:
            
            response = client.post('/create-form', 
                                 data=json.dumps(form_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            response_data = json.loads(response.data)
            assert response_data['message'] == 'Form created successfully!'
            assert '/form/New Test Form' in response_data['redirect']
            mock_create.assert_called_once()
    
    def test_create_form_empty_name(self, client, authenticated_session):
        """Test form creation with empty name"""
        form_data = {
            'name': ''
        }
        
        response = client.post('/create-form', 
                             data=json.dumps(form_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert 'Form name is required' in response_data['error']
    
    def test_create_form_duplicate_name(self, client, authenticated_session):
        """Test form creation with duplicate name"""
        form_data = {
            'name': 'Existing Form'
        }
        
        with patch('models.FormModel.get_form_by_name', return_value={'name': 'Existing Form'}):
            response = client.post('/create-form', 
                                 data=json.dumps(form_data),
                                 content_type='application/json')
            
            assert response.status_code == 400
            response_data = json.loads(response.data)
            assert 'Form name already exists' in response_data['error']
    
    def test_create_form_not_authenticated(self, client):
        """Test form creation without authentication"""
        form_data = {
            'name': 'Test Form'
        }
        
        response = client.post('/create-form', 
                             data=json.dumps(form_data),
                             content_type='application/json')
        
        assert response.status_code == 302  # Redirect to login


@pytest.mark.forms
class TestFormEditing:
    """Test form editing functionality"""
    
    def test_edit_form_success(self, client, authenticated_session, mock_mongo):
        """Test successful form editing access"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []}
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form):
            response = client.get('/form/test_form')
            
            assert response.status_code == 200
            assert b'form_builder' in response.data
    
    def test_edit_form_not_found(self, client, authenticated_session):
        """Test editing non-existent form"""
        with patch('models.FormModel.get_form_by_name', return_value=None):
            response = client.get('/form/nonexistent_form')
            
            assert response.status_code == 302  # Redirect to index
    
    def test_edit_form_no_permission(self, client, authenticated_session):
        """Test editing form without permission"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': ['other_user'], 'editor': [], 'viewer': []}
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form):
            response = client.get('/form/test_form')
            
            assert response.status_code == 403
    
    def test_edit_form_not_authenticated(self, client):
        """Test editing form without authentication"""
        response = client.get('/form/test_form')
        
        assert response.status_code == 302  # Redirect to login


@pytest.mark.forms
class TestFormSaving:
    """Test form saving functionality"""
    
    def test_save_form_data_success(self, client, authenticated_session):
        """Test successful form data saving"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []}
        )
        
        form_data = {
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
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.update_form') as mock_update:
            
            response = client.post('/api/form/test_form/save',
                                 data=json.dumps(form_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            response_data = json.loads(response.data)
            assert response_data['message'] == 'Form saved successfully'
            mock_update.assert_called_once()
    
    def test_save_form_data_not_found(self, client, authenticated_session):
        """Test saving data for non-existent form"""
        form_data = {'questions': []}
        
        with patch('models.FormModel.get_form_by_name', return_value=None):
            response = client.post('/api/form/nonexistent_form/save',
                                 data=json.dumps(form_data),
                                 content_type='application/json')
            
            assert response.status_code == 404
    
    def test_save_form_data_no_permission(self, client, authenticated_session):
        """Test saving form data without permission"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': ['other_user'], 'editor': [], 'viewer': []}
        )
        
        form_data = {'questions': []}
        
        with patch('models.FormModel.get_form_by_name', return_value=form):
            response = client.post('/api/form/test_form/save',
                                 data=json.dumps(form_data),
                                 content_type='application/json')
            
            assert response.status_code == 403


@pytest.mark.forms
class TestQuestionManagement:
    """Test question management functionality"""
    
    def test_add_question_success(self, client, authenticated_session):
        """Test successful question addition"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []},
            questions=[
                {
                    'id': 'q_1',
                    'title': 'Question 1',
                    'text': 'First question',
                    'type': 'text',
                    'required': False
                }
            ]
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.update_form') as mock_update:
            
            response = client.post('/api/form/test_form/question')
            
            assert response.status_code == 200
            response_data = json.loads(response.data)
            assert 'question' in response_data
            assert response_data['question']['id'] == 'q_2'
            assert response_data['question']['title'] == 'Question 2'
            mock_update.assert_called_once()
    
    def test_add_question_not_found(self, client, authenticated_session):
        """Test adding question to non-existent form"""
        with patch('models.FormModel.get_form_by_name', return_value=None):
            response = client.post('/api/form/nonexistent_form/question')
            
            assert response.status_code == 404
    
    def test_add_question_no_permission(self, client, authenticated_session):
        """Test adding question without permission"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': ['other_user'], 'editor': [], 'viewer': []}
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form):
            response = client.post('/api/form/test_form/question')
            
            assert response.status_code == 403


@pytest.mark.forms
class TestFormPublishing:
    """Test form publishing functionality"""
    
    def test_publish_form_success(self, client, authenticated_session):
        """Test successful form publishing"""
        form = FormFactory(
            name='test_form',
            status='draft',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []}
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.update_form') as mock_update:
            
            response = client.post('/api/form/test_form/publish')
            
            assert response.status_code == 200
            response_data = json.loads(response.data)
            assert response_data['message'] == 'Form published successfully!'
            assert 'share_url' in response_data
            assert 'submit/test_form' in response_data['share_url']
            mock_update.assert_called_once()
    
    def test_publish_form_not_admin(self, client, authenticated_session):
        """Test publishing form without admin permission"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': ['other_user'], 'editor': [authenticated_session['id']], 'viewer': []}
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form):
            response = client.post('/api/form/test_form/publish')
            
            assert response.status_code == 403
            response_data = json.loads(response.data)
            assert 'Only form admins can publish forms' in response_data['error']
    
    def test_hide_form_success(self, client, authenticated_session):
        """Test successful form hiding"""
        form = FormFactory(
            name='test_form',
            status='published',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []}
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.update_form') as mock_update:
            
            response = client.post('/api/form/test_form/hide')
            
            assert response.status_code == 200
            response_data = json.loads(response.data)
            assert response_data['message'] == 'Form hidden successfully!'
            mock_update.assert_called_once()
    
    def test_hide_form_not_admin(self, client, authenticated_session):
        """Test hiding form without admin permission"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': ['other_user'], 'editor': [authenticated_session['id']], 'viewer': []}
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form):
            response = client.post('/api/form/test_form/hide')
            
            assert response.status_code == 403


@pytest.mark.forms
class TestFormDeletion:
    """Test form deletion functionality"""
    
    def test_delete_form_success(self, client, authenticated_session):
        """Test successful form deletion"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []}
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.delete_form', return_value=True) as mock_delete:
            
            response = client.delete('/api/form/test_form/delete')
            
            assert response.status_code == 200
            response_data = json.loads(response.data)
            assert response_data['message'] == 'Form deleted successfully'
            mock_delete.assert_called_once_with('test_form')
    
    def test_delete_form_not_found(self, client, authenticated_session):
        """Test deleting non-existent form"""
        with patch('models.FormModel.get_form_by_name', return_value=None):
            response = client.delete('/api/form/nonexistent_form/delete')
            
            assert response.status_code == 404
    
    def test_delete_form_not_admin(self, client, authenticated_session):
        """Test deleting form without admin permission"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': ['other_user'], 'editor': [authenticated_session['id']], 'viewer': []}
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form):
            response = client.delete('/api/form/test_form/delete')
            
            assert response.status_code == 403
    
    def test_delete_form_failure(self, client, authenticated_session):
        """Test form deletion failure"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []}
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.delete_form', return_value=False):
            
            response = client.delete('/api/form/test_form/delete')
            
            assert response.status_code == 500


@pytest.mark.forms
class TestFormListing:
    """Test form listing functionality"""
    
    def test_index_page_authenticated(self, client, authenticated_session):
        """Test index page for authenticated user"""
        forms = [
            FormFactory(name='form1'),
            FormFactory(name='form2')
        ]
        
        with patch('auth.auth_manager.get_user_forms', return_value=forms):
            response = client.get('/')
            
            assert response.status_code == 200
            assert b'form1' in response.data
            assert b'form2' in response.data
    
    def test_index_page_not_authenticated(self, client):
        """Test index page without authentication"""
        response = client.get('/')
        
        assert response.status_code == 302  # Redirect to login
    
    def test_my_forms_page(self, client, authenticated_session):
        """Test my forms page"""
        forms = [FormFactory(name='user_form')]
        
        with patch('auth.auth_manager.get_user_forms', return_value=forms):
            response = client.get('/my-forms')
            
            assert response.status_code == 200
            assert b'user_form' in response.data
    
    def test_my_forms_page_not_authenticated(self, client):
        """Test my forms page without authentication"""
        response = client.get('/my-forms')
        
        assert response.status_code == 302  # Redirect to login


@pytest.mark.forms
class TestSubmissionViewing:
    """Test submission viewing functionality"""
    
    def test_view_submissions_success(self, client, authenticated_session):
        """Test successful submission viewing"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []},
            submissions=[
                {
                    'id': 'sub_1',
                    'submitted_at': datetime.now(),
                    'responses': {'q_1': 'Response 1'}
                }
            ]
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form):
            response = client.get('/form/test_form/submissions')
            
            assert response.status_code == 200
            assert b'submissions' in response.data.lower()
    
    def test_view_submissions_not_found(self, client, authenticated_session):
        """Test viewing submissions for non-existent form"""
        with patch('models.FormModel.get_form_by_name', return_value=None):
            response = client.get('/form/nonexistent_form/submissions')
            
            assert response.status_code == 302  # Redirect to index
    
    def test_view_submissions_no_permission(self, client, authenticated_session):
        """Test viewing submissions without permission"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': ['other_user'], 'editor': [], 'viewer': []}
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form):
            response = client.get('/form/test_form/submissions')
            
            assert response.status_code == 403
    
    def test_view_submissions_as_viewer(self, client, authenticated_session):
        """Test viewing submissions as viewer"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': ['other_user'], 'editor': [], 'viewer': [authenticated_session['id']]}
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form):
            response = client.get('/form/test_form/submissions')
            
            assert response.status_code == 200


@pytest.mark.forms
class TestSubmissionDeletion:
    """Test submission deletion functionality"""
    
    def test_delete_submission_success(self, client):
        """Test successful submission deletion"""
        form = FormFactory(
            name='test_form',
            submissions=[
                {
                    'id': 'sub_1',
                    'responses': {'q_1': 'Response 1'}
                }
            ]
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.delete_submission', return_value=True) as mock_delete:
            
            response = client.delete('/api/form/test_form/submission/sub_1/delete')
            
            assert response.status_code == 200
            response_data = json.loads(response.data)
            assert response_data['message'] == 'Submission deleted successfully'
            mock_delete.assert_called_once_with('test_form', 'sub_1')
    
    def test_delete_submission_form_not_found(self, client):
        """Test deleting submission from non-existent form"""
        with patch('models.FormModel.get_form_by_name', return_value=None):
            response = client.delete('/api/form/nonexistent_form/submission/sub_1/delete')
            
            assert response.status_code == 404
    
    def test_delete_submission_not_found(self, client):
        """Test deleting non-existent submission"""
        form = FormFactory(name='test_form', submissions=[])
        
        with patch('models.FormModel.get_form_by_name', return_value=form):
            response = client.delete('/api/form/test_form/submission/nonexistent_sub/delete')
            
            assert response.status_code == 404
    
    def test_delete_submission_failure(self, client):
        """Test submission deletion failure"""
        form = FormFactory(
            name='test_form',
            submissions=[{'id': 'sub_1', 'responses': {}}]
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.delete_submission', return_value=False):
            
            response = client.delete('/api/form/test_form/submission/sub_1/delete')
            
            assert response.status_code == 500