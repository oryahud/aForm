"""
Public form and submission tests for aForm application
"""
import pytest
import json
import uuid
from unittest.mock import patch, MagicMock
from datetime import datetime

from tests.conftest import UserFactory, FormFactory, create_test_form


@pytest.mark.api
class TestPublicFormAccess:
    """Test public form access functionality"""
    
    def test_public_form_published(self, client):
        """Test accessing published public form"""
        form = FormFactory(
            name='test_form',
            status='published',
            questions=[
                {
                    'id': 'q_1',
                    'title': 'Name',
                    'text': 'What is your name?',
                    'type': 'text',
                    'required': True
                },
                {
                    'id': 'q_2',
                    'title': 'Email',
                    'text': 'What is your email?',
                    'type': 'email',
                    'required': False
                }
            ]
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form):
            response = client.get('/submit/test_form')
            
            assert response.status_code == 200
            assert b'test_form' in response.data
            assert b'What is your name?' in response.data
            assert b'What is your email?' in response.data
    
    def test_public_form_draft(self, client):
        """Test accessing draft public form (should fail)"""
        form = FormFactory(
            name='test_form',
            status='draft'
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form):
            response = client.get('/submit/test_form')
            
            assert response.status_code == 404
            assert b'Form not found or not published' in response.data
    
    def test_public_form_not_found(self, client):
        """Test accessing non-existent public form"""
        with patch('models.FormModel.get_form_by_name', return_value=None):
            response = client.get('/submit/nonexistent_form')
            
            assert response.status_code == 404
            assert b'Form not found or not published' in response.data
    
    def test_public_form_no_status(self, client):
        """Test accessing form without status field"""
        form = FormFactory(name='test_form')
        del form['status']  # Remove status field
        
        with patch('models.FormModel.get_form_by_name', return_value=form):
            response = client.get('/submit/test_form')
            
            assert response.status_code == 404


@pytest.mark.api
class TestFormSubmission:
    """Test form submission functionality"""
    
    def test_submit_form_success(self, client):
        """Test successful form submission"""
        form = FormFactory(
            name='test_form',
            status='published',
            questions=[
                {
                    'id': 'q_1',
                    'title': 'Name',
                    'text': 'What is your name?',
                    'type': 'text',
                    'required': True
                }
            ]
        )
        
        submission_data = {
            'responses': {
                'q_1': 'John Doe'
            }
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.add_submission', return_value=True) as mock_add, \
             patch('uuid.uuid4', return_value=MagicMock(hex='test-submission-id')):
            
            response = client.post('/api/form/test_form/submit',
                                 data=json.dumps(submission_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            response_data = json.loads(response.data)
            assert response_data['message'] == 'Form submitted successfully!'
            assert 'submission_id' in response_data
            
            # Verify submission was added with correct data
            mock_add.assert_called_once()
            call_args = mock_add.call_args
            assert call_args[0][0] == 'test_form'  # form_name
            submission = call_args[0][1]  # submission_data
            assert submission['responses'] == {'q_1': 'John Doe'}
            assert 'id' in submission
    
    def test_submit_form_not_found(self, client):
        """Test submitting to non-existent form"""
        submission_data = {
            'responses': {
                'q_1': 'John Doe'
            }
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=None):
            response = client.post('/api/form/nonexistent_form/submit',
                                 data=json.dumps(submission_data),
                                 content_type='application/json')
            
            assert response.status_code == 404
            response_data = json.loads(response.data)
            assert 'Form not found or not published' in response_data['error']
    
    def test_submit_form_not_published(self, client):
        """Test submitting to unpublished form"""
        form = FormFactory(
            name='test_form',
            status='draft'
        )
        
        submission_data = {
            'responses': {
                'q_1': 'John Doe'
            }
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form):
            response = client.post('/api/form/test_form/submit',
                                 data=json.dumps(submission_data),
                                 content_type='application/json')
            
            assert response.status_code == 404
            response_data = json.loads(response.data)
            assert 'Form not found or not published' in response_data['error']
    
    def test_submit_form_empty_responses(self, client):
        """Test submitting form with empty responses"""
        form = FormFactory(
            name='test_form',
            status='published'
        )
        
        submission_data = {
            'responses': {}
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.add_submission', return_value=True):
            
            response = client.post('/api/form/test_form/submit',
                                 data=json.dumps(submission_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
    
    def test_submit_form_missing_responses(self, client):
        """Test submitting form without responses field"""
        form = FormFactory(
            name='test_form',
            status='published'
        )
        
        submission_data = {}  # No responses field
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.add_submission', return_value=True):
            
            response = client.post('/api/form/test_form/submit',
                                 data=json.dumps(submission_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            # Should handle missing responses gracefully
    
    def test_submit_form_database_failure(self, client):
        """Test form submission when database operation fails"""
        form = FormFactory(
            name='test_form',
            status='published'
        )
        
        submission_data = {
            'responses': {
                'q_1': 'John Doe'
            }
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.add_submission', return_value=False):
            
            response = client.post('/api/form/test_form/submit',
                                 data=json.dumps(submission_data),
                                 content_type='application/json')
            
            assert response.status_code == 500
            response_data = json.loads(response.data)
            assert 'Failed to submit form' in response_data['error']
    
    def test_submit_form_complex_responses(self, client):
        """Test submitting form with complex response data"""
        form = FormFactory(
            name='test_form',
            status='published',
            questions=[
                {
                    'id': 'q_1',
                    'title': 'Name',
                    'type': 'text'
                },
                {
                    'id': 'q_2',
                    'title': 'Options',
                    'type': 'checkbox'
                },
                {
                    'id': 'q_3',
                    'title': 'Rating',
                    'type': 'number'
                }
            ]
        )
        
        submission_data = {
            'responses': {
                'q_1': 'Jane Smith',
                'q_2': ['option1', 'option3'],  # Multiple selections
                'q_3': 8
            }
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.add_submission', return_value=True) as mock_add:
            
            response = client.post('/api/form/test_form/submit',
                                 data=json.dumps(submission_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            
            # Verify complex data is preserved
            call_args = mock_add.call_args
            submission = call_args[0][1]
            assert submission['responses']['q_1'] == 'Jane Smith'
            assert submission['responses']['q_2'] == ['option1', 'option3']
            assert submission['responses']['q_3'] == 8


@pytest.mark.api
class TestFormValidation:
    """Test form validation functionality"""
    
    def test_submit_form_with_required_fields(self, client):
        """Test form submission validation for required fields"""
        form = FormFactory(
            name='test_form',
            status='published',
            questions=[
                {
                    'id': 'q_1',
                    'title': 'Name',
                    'text': 'What is your name?',
                    'type': 'text',
                    'required': True
                },
                {
                    'id': 'q_2',
                    'title': 'Email',
                    'text': 'What is your email?',
                    'type': 'email',
                    'required': False
                }
            ]
        )
        
        # Submit with required field
        submission_data = {
            'responses': {
                'q_1': 'John Doe'
                # q_2 is not required, so it's okay to omit
            }
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.add_submission', return_value=True):
            
            response = client.post('/api/form/test_form/submit',
                                 data=json.dumps(submission_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
    
    def test_submit_form_different_question_types(self, client):
        """Test form submission with different question types"""
        form = FormFactory(
            name='test_form',
            status='published',
            questions=[
                {'id': 'q_text', 'type': 'text', 'title': 'Text'},
                {'id': 'q_email', 'type': 'email', 'title': 'Email'},
                {'id': 'q_number', 'type': 'number', 'title': 'Number'},
                {'id': 'q_select', 'type': 'select', 'title': 'Select'},
                {'id': 'q_radio', 'type': 'radio', 'title': 'Radio'},
                {'id': 'q_checkbox', 'type': 'checkbox', 'title': 'Checkbox'},
                {'id': 'q_textarea', 'type': 'textarea', 'title': 'Textarea'}
            ]
        )
        
        submission_data = {
            'responses': {
                'q_text': 'Sample text',
                'q_email': 'user@example.com',
                'q_number': 42,
                'q_select': 'option2',
                'q_radio': 'choice1',
                'q_checkbox': ['check1', 'check3'],
                'q_textarea': 'This is a longer text response\\nwith multiple lines.'
            }
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.add_submission', return_value=True) as mock_add:
            
            response = client.post('/api/form/test_form/submit',
                                 data=json.dumps(submission_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            
            # Verify all question types are handled
            call_args = mock_add.call_args
            submission = call_args[0][1]
            responses = submission['responses']
            
            assert responses['q_text'] == 'Sample text'
            assert responses['q_email'] == 'user@example.com'
            assert responses['q_number'] == 42
            assert responses['q_select'] == 'option2'
            assert responses['q_radio'] == 'choice1'
            assert responses['q_checkbox'] == ['check1', 'check3']
            assert 'multiple lines' in responses['q_textarea']


@pytest.mark.api
class TestSubmissionIdentifiers:
    """Test submission ID generation and handling"""
    
    def test_submission_id_generation(self, client):
        """Test that submission IDs are properly generated"""
        form = FormFactory(name='test_form', status='published')
        
        submission_data = {
            'responses': {
                'q_1': 'Test response'
            }
        }
        
        # Mock uuid.uuid4 to return predictable value
        mock_uuid = MagicMock()
        mock_uuid.hex = 'test-uuid-12345'
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.add_submission', return_value=True), \
             patch('uuid.uuid4', return_value=mock_uuid):
            
            response = client.post('/api/form/test_form/submit',
                                 data=json.dumps(submission_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            response_data = json.loads(response.data)
            assert response_data['submission_id'] == 'test-uuid-12345'
    
    def test_multiple_submissions_unique_ids(self, client):
        """Test that multiple submissions get unique IDs"""
        form = FormFactory(name='test_form', status='published')
        
        submission_data = {
            'responses': {
                'q_1': 'Test response'
            }
        }
        
        submission_ids = []
        
        # Submit form multiple times
        for i in range(3):
            with patch('models.FormModel.get_form_by_name', return_value=form), \
                 patch('models.FormModel.add_submission', return_value=True):
                
                response = client.post('/api/form/test_form/submit',
                                     data=json.dumps(submission_data),
                                     content_type='application/json')
                
                assert response.status_code == 200
                response_data = json.loads(response.data)
                submission_ids.append(response_data['submission_id'])
        
        # Verify all IDs are unique
        assert len(set(submission_ids)) == 3


@pytest.mark.api
class TestPublicFormSecurity:
    """Test security aspects of public forms"""
    
    def test_public_form_no_auth_required(self, client):
        """Test that public forms don't require authentication"""
        form = FormFactory(name='test_form', status='published')
        
        with patch('models.FormModel.get_form_by_name', return_value=form):
            # Should work without any authentication
            response = client.get('/submit/test_form')
            assert response.status_code == 200
    
    def test_submit_form_no_auth_required(self, client):
        """Test that form submission doesn't require authentication"""
        form = FormFactory(name='test_form', status='published')
        
        submission_data = {
            'responses': {
                'q_1': 'Anonymous submission'
            }
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.add_submission', return_value=True):
            
            # Should work without any authentication
            response = client.post('/api/form/test_form/submit',
                                 data=json.dumps(submission_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
    
    def test_public_form_private_data_not_exposed(self, client):
        """Test that private form data is not exposed in public view"""
        form = FormFactory(
            name='test_form',
            status='published',
            permissions={'admin': ['secret_admin'], 'editor': [], 'viewer': []},
            submissions=[
                {
                    'id': 'secret_submission',
                    'responses': {'q_1': 'Secret response'}
                }
            ]
        )
        
        with patch('models.FormModel.get_form_by_name', return_value=form):
            response = client.get('/submit/test_form')
            
            assert response.status_code == 200
            # Sensitive data should not be in public view
            assert b'secret_admin' not in response.data
            assert b'secret_submission' not in response.data
            assert b'Secret response' not in response.data
    
    def test_malicious_submission_data(self, client):
        """Test handling of potentially malicious submission data"""
        form = FormFactory(name='test_form', status='published')
        
        malicious_data = {
            'responses': {
                'q_1': '<script>alert("xss")</script>',
                'q_2': ''; DROP TABLE users; --',
                'q_3': '\\x00\\x01\\x02',  # Binary data
                '__proto__': 'malicious',  # Prototype pollution attempt
                'eval': 'dangerous_code()'
            }
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.add_submission', return_value=True) as mock_add:
            
            response = client.post('/api/form/test_form/submit',
                                 data=json.dumps(malicious_data),
                                 content_type='application/json')
            
            # Should handle malicious data gracefully
            assert response.status_code == 200
            
            # Verify data is stored as-is (filtering should happen on output)
            call_args = mock_add.call_args
            submission = call_args[0][1]
            responses = submission['responses']
            
            # Data should be preserved for analysis but handled safely
            assert '<script>' in responses['q_1']
            assert 'DROP TABLE' in responses['q_2']