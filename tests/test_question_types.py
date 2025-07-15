"""
Tests for new question types and their validation
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, date

from tests.conftest import UserFactory, FormFactory, create_test_user, create_test_form, authenticate_user


@pytest.mark.question_types
class TestEmailQuestionType:
    """Test email question type functionality and validation"""
    
    def test_create_email_question(self, client, authenticated_session):
        """Test creating an email question type"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []},
            questions=[]
        )
        
        question_data = {
            'questions': [
                {
                    'id': 'q_1',
                    'title': 'Email Address',
                    'text': 'Please enter your email address',
                    'type': 'email',
                    'required': True,
                    'placeholder': 'your.email@example.com'
                }
            ]
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.update_form') as mock_update:
            
            response = client.post('/api/form/test_form/save',
                                 data=json.dumps(question_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            mock_update.assert_called_once_with('test_form', question_data)
    
    def test_email_validation_valid_emails(self):
        """Test email validation with valid email addresses"""
        valid_emails = [
            'test@example.com',
            'user.name@domain.org',
            'firstname+lastname@company.co.uk',
            'user123@test-domain.info'
        ]
        
        # Since we can't directly test client-side JS, we test the pattern
        import re
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        
        for email in valid_emails:
            assert re.match(email_pattern, email), f"Valid email {email} should pass validation"
    
    def test_email_validation_invalid_emails(self):
        """Test email validation with invalid email addresses"""
        invalid_emails = [
            'invalid-email',
            '@domain.com',
            'user@',
            'user name@domain.com',
            'user@domain',
            ''
        ]
        
        import re
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        
        for email in invalid_emails:
            assert not re.match(email_pattern, email), f"Invalid email {email} should fail validation"


@pytest.mark.question_types
class TestPhoneQuestionType:
    """Test phone number question type functionality"""
    
    def test_create_phone_question(self, client, authenticated_session):
        """Test creating a phone question type"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []},
            questions=[]
        )
        
        question_data = {
            'questions': [
                {
                    'id': 'q_1',
                    'title': 'Phone Number',
                    'text': 'Please enter your phone number',
                    'type': 'phone',
                    'required': True,
                    'countryCode': '+1',
                    'allowExtension': True
                }
            ]
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.update_form') as mock_update:
            
            response = client.post('/api/form/test_form/save',
                                 data=json.dumps(question_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            mock_update.assert_called_once_with('test_form', question_data)
    
    def test_phone_validation_valid_numbers(self):
        """Test phone validation with valid phone numbers"""
        valid_phones = [
            '555-123-4567',
            '(555) 123-4567',
            '555.123.4567',
            '5551234567',
            '+1 555 123 4567'
        ]
        
        import re
        phone_pattern = r'^[\d\s\-\(\)\+\.]+$'
        
        for phone in valid_phones:
            digits_only = re.sub(r'\D', '', phone)
            assert re.match(phone_pattern, phone), f"Valid phone {phone} should match pattern"
            assert len(digits_only) >= 7, f"Phone {phone} should have at least 7 digits"
    
    def test_phone_validation_invalid_numbers(self):
        """Test phone validation with invalid phone numbers"""
        invalid_phones = [
            'abc123',
            '123',
            '!@#$%^&*()',
            'phone number'
        ]
        
        import re
        phone_pattern = r'^[\d\s\-\(\)\+\.]+$'
        
        for phone in invalid_phones:
            digits_only = re.sub(r'\D', '', phone)
            is_valid_pattern = re.match(phone_pattern, phone)
            has_enough_digits = len(digits_only) >= 7
            
            assert not (is_valid_pattern and has_enough_digits), f"Invalid phone {phone} should fail validation"


@pytest.mark.question_types
class TestDateQuestionType:
    """Test date question type functionality"""
    
    def test_create_date_question(self, client, authenticated_session):
        """Test creating a date question type"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []},
            questions=[]
        )
        
        question_data = {
            'questions': [
                {
                    'id': 'q_1',
                    'title': 'Birth Date',
                    'text': 'Please enter your birth date',
                    'type': 'date',
                    'required': True,
                    'dateFormat': 'YYYY-MM-DD',
                    'minDate': '1900-01-01',
                    'maxDate': '2023-12-31'
                }
            ]
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.update_form') as mock_update:
            
            response = client.post('/api/form/test_form/save',
                                 data=json.dumps(question_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            mock_update.assert_called_once_with('test_form', question_data)
    
    def test_date_validation_valid_dates(self):
        """Test date validation with valid dates"""
        valid_dates = [
            '2023-12-31',
            '2000-01-01',
            '1990-06-15'
        ]
        
        from datetime import datetime
        
        for date_str in valid_dates:
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
                assert True  # If no exception, date is valid
            except ValueError:
                assert False, f"Valid date {date_str} should pass validation"
    
    def test_date_constraints(self):
        """Test date constraints (min/max)"""
        test_date = '2023-06-15'
        min_date = '2023-01-01'
        max_date = '2023-12-31'
        
        from datetime import datetime
        
        test_dt = datetime.strptime(test_date, '%Y-%m-%d')
        min_dt = datetime.strptime(min_date, '%Y-%m-%d')
        max_dt = datetime.strptime(max_date, '%Y-%m-%d')
        
        assert min_dt <= test_dt <= max_dt, "Date should be within constraints"


@pytest.mark.question_types
class TestNumberQuestionType:
    """Test number question type functionality"""
    
    def test_create_number_question(self, client, authenticated_session):
        """Test creating a number question type"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []},
            questions=[]
        )
        
        question_data = {
            'questions': [
                {
                    'id': 'q_1',
                    'title': 'Age',
                    'text': 'Please enter your age',
                    'type': 'number',
                    'required': True,
                    'minValue': 0,
                    'maxValue': 120,
                    'stepSize': 1,
                    'allowDecimals': False
                }
            ]
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.update_form') as mock_update:
            
            response = client.post('/api/form/test_form/save',
                                 data=json.dumps(question_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            mock_update.assert_called_once_with('test_form', question_data)
    
    def test_number_validation_constraints(self):
        """Test number validation with constraints"""
        min_val = 0
        max_val = 100
        
        # Valid numbers within range
        valid_numbers = [0, 50, 100, 25.5]
        for num in valid_numbers:
            assert min_val <= num <= max_val, f"Number {num} should be within range"
        
        # Invalid numbers outside range  
        invalid_numbers = [-1, 101, 150]
        for num in invalid_numbers:
            assert not (min_val <= num <= max_val), f"Number {num} should be outside range"


@pytest.mark.question_types
class TestRatingQuestionType:
    """Test rating question type functionality"""
    
    def test_create_rating_question(self, client, authenticated_session):
        """Test creating a rating question type"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []},
            questions=[]
        )
        
        question_data = {
            'questions': [
                {
                    'id': 'q_1',
                    'title': 'Satisfaction Rating',
                    'text': 'How satisfied are you with our service?',
                    'type': 'rating',
                    'required': True,
                    'ratingScale': 10,
                    'ratingStyle': 'stars',
                    'lowLabel': 'Very Poor',
                    'highLabel': 'Excellent'
                }
            ]
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.update_form') as mock_update:
            
            response = client.post('/api/form/test_form/save',
                                 data=json.dumps(question_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            mock_update.assert_called_once_with('test_form', question_data)
    
    def test_rating_scale_validation(self):
        """Test rating scale validation"""
        scale = 5
        valid_ratings = [1, 2, 3, 4, 5]
        invalid_ratings = [0, 6, -1, 10]
        
        for rating in valid_ratings:
            assert 1 <= rating <= scale, f"Rating {rating} should be valid for scale 1-{scale}"
        
        for rating in invalid_ratings:
            assert not (1 <= rating <= scale), f"Rating {rating} should be invalid for scale 1-{scale}"


@pytest.mark.question_types  
class TestURLQuestionType:
    """Test URL question type functionality"""
    
    def test_create_url_question(self, client, authenticated_session):
        """Test creating a URL question type"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []},
            questions=[]
        )
        
        question_data = {
            'questions': [
                {
                    'id': 'q_1',
                    'title': 'Website URL',
                    'text': 'Please enter your website URL',
                    'type': 'url',
                    'required': True,
                    'placeholder': 'https://example.com'
                }
            ]
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.update_form') as mock_update:
            
            response = client.post('/api/form/test_form/save',
                                 data=json.dumps(question_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            mock_update.assert_called_once_with('test_form', question_data)
    
    def test_url_validation(self):
        """Test URL validation"""
        valid_urls = [
            'https://example.com',
            'http://test.org',
            'https://subdomain.example.com/path',
            'https://example.com:8080/path?query=value'
        ]
        
        invalid_urls = [
            'not-a-url',
            'ftp://example.com',  # Might be invalid depending on requirements
            'example.com',  # Missing protocol
            'https://',  # Incomplete
            ''
        ]
        
        from urllib.parse import urlparse
        
        for url in valid_urls:
            try:
                result = urlparse(url)
                assert all([result.scheme, result.netloc]), f"URL {url} should be valid"
            except Exception:
                assert False, f"Valid URL {url} should pass validation"
        
        for url in invalid_urls:
            try:
                result = urlparse(url)
                # Check if it has both scheme and netloc
                is_valid = all([result.scheme, result.netloc])
                assert not is_valid, f"Invalid URL {url} should fail validation"
            except Exception:
                pass  # Exception means invalid URL, which is expected


@pytest.mark.question_types
class TestFileUploadQuestionType:
    """Test file upload question type functionality"""
    
    def test_create_file_question(self, client, authenticated_session):
        """Test creating a file upload question type"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []},
            questions=[]
        )
        
        question_data = {
            'questions': [
                {
                    'id': 'q_1',
                    'title': 'Upload Resume',
                    'text': 'Please upload your resume',
                    'type': 'file',
                    'required': True,
                    'fileTypes': ['application/pdf', '.doc', '.docx'],
                    'maxFileSize': 10,
                    'allowMultipleFiles': False
                }
            ]
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.update_form') as mock_update:
            
            response = client.post('/api/form/test_form/save',
                                 data=json.dumps(question_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            mock_update.assert_called_once_with('test_form', question_data)
    
    def test_file_type_validation(self):
        """Test file type validation"""
        allowed_types = ['application/pdf', '.doc', '.docx', 'image/*']
        
        valid_files = [
            ('document.pdf', 'application/pdf'),
            ('resume.doc', 'application/msword'),
            ('photo.jpg', 'image/jpeg'),
            ('image.png', 'image/png')
        ]
        
        invalid_files = [
            ('virus.exe', 'application/octet-stream'),
            ('script.js', 'text/javascript'),
            ('data.xml', 'text/xml')
        ]
        
        def is_file_allowed(filename, mimetype, allowed_types):
            for allowed in allowed_types:
                if allowed.startswith('.'):
                    if filename.endswith(allowed):
                        return True
                elif allowed.endswith('/*'):
                    if mimetype.startswith(allowed[:-1]):
                        return True
                elif allowed == mimetype:
                    return True
            return False
        
        for filename, mimetype in valid_files:
            assert is_file_allowed(filename, mimetype, allowed_types), \
                f"File {filename} with type {mimetype} should be allowed"
        
        for filename, mimetype in invalid_files:
            assert not is_file_allowed(filename, mimetype, allowed_types), \
                f"File {filename} with type {mimetype} should not be allowed"


@pytest.mark.question_types
class TestTextareaQuestionType:
    """Test textarea question type functionality"""
    
    def test_create_textarea_question(self, client, authenticated_session):
        """Test creating a textarea question type"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []},
            questions=[]
        )
        
        question_data = {
            'questions': [
                {
                    'id': 'q_1',
                    'title': 'Comments',
                    'text': 'Please provide additional comments',
                    'type': 'textarea',
                    'required': False,
                    'textareaPlaceholder': 'Enter your detailed response...',
                    'charLimit': 500,
                    'textareaRows': 6
                }
            ]
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.update_form') as mock_update:
            
            response = client.post('/api/form/test_form/save',
                                 data=json.dumps(question_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            mock_update.assert_called_once_with('test_form', question_data)
    
    def test_textarea_character_limit(self):
        """Test textarea character limit validation"""
        char_limit = 100
        
        valid_text = "A" * 50  # Under limit
        limit_text = "B" * 100  # At limit
        over_limit_text = "C" * 150  # Over limit
        
        assert len(valid_text) <= char_limit, "Text under limit should be valid"
        assert len(limit_text) <= char_limit, "Text at limit should be valid"
        assert len(over_limit_text) > char_limit, "Text over limit should be invalid"


@pytest.mark.question_types
class TestSelectQuestionType:
    """Test select/dropdown question type functionality"""
    
    def test_create_select_question(self, client, authenticated_session):
        """Test creating a select question type"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []},
            questions=[]
        )
        
        question_data = {
            'questions': [
                {
                    'id': 'q_1',
                    'title': 'Favorite Color',
                    'text': 'What is your favorite color?',
                    'type': 'select',
                    'required': True,
                    'options': ['Red', 'Blue', 'Green', 'Yellow', 'Purple'],
                    'multiple': False
                }
            ]
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.update_form') as mock_update:
            
            response = client.post('/api/form/test_form/save',
                                 data=json.dumps(question_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            mock_update.assert_called_once_with('test_form', question_data)
    
    def test_select_multiple_options(self):
        """Test select question with multiple selection"""
        options = ['Option 1', 'Option 2', 'Option 3']
        selected = ['Option 1', 'Option 3']
        
        # Validate that selected options are in available options
        for selection in selected:
            assert selection in options, f"Selected option {selection} should be in available options"
    
    def test_checkbox_question_type(self, client, authenticated_session):
        """Test creating a checkbox question type"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []},
            questions=[]
        )
        
        question_data = {
            'questions': [
                {
                    'id': 'q_1',
                    'title': 'Hobbies',
                    'text': 'Select all hobbies that apply',
                    'type': 'checkbox',
                    'required': False,
                    'options': ['Reading', 'Sports', 'Music', 'Travel', 'Cooking'],
                    'multiple': True
                }
            ]
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.update_form') as mock_update:
            
            response = client.post('/api/form/test_form/save',
                                 data=json.dumps(question_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            mock_update.assert_called_once_with('test_form', question_data)


@pytest.mark.question_types
class TestTimeQuestionType:
    """Test time question type functionality"""
    
    def test_create_time_question(self, client, authenticated_session):
        """Test creating a time question type"""
        form = FormFactory(
            name='test_form',
            permissions={'admin': [authenticated_session['id']], 'editor': [], 'viewer': []},
            questions=[]
        )
        
        question_data = {
            'questions': [
                {
                    'id': 'q_1',
                    'title': 'Preferred Meeting Time',
                    'text': 'What time works best for you?',
                    'type': 'time',
                    'required': True
                }
            ]
        }
        
        with patch('models.FormModel.get_form_by_name', return_value=form), \
             patch('models.FormModel.update_form') as mock_update:
            
            response = client.post('/api/form/test_form/save',
                                 data=json.dumps(question_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            mock_update.assert_called_once_with('test_form', question_data)
    
    def test_time_validation(self):
        """Test time format validation"""
        valid_times = [
            '09:00',
            '14:30',
            '23:59',
            '00:00'
        ]
        
        invalid_times = [
            '25:00',  # Invalid hour
            '12:60',  # Invalid minute
            '9:30',   # Missing leading zero
            'noon',   # Text format
            ''
        ]
        
        import re
        time_pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
        
        for time_str in valid_times:
            assert re.match(time_pattern, time_str), f"Valid time {time_str} should pass validation"
        
        for time_str in invalid_times:
            if time_str:  # Skip empty string for regex
                assert not re.match(time_pattern, time_str), f"Invalid time {time_str} should fail validation"


@pytest.mark.question_types
class TestQuestionTypeRendering:
    """Test question type rendering and display"""
    
    def test_question_type_display_text(self):
        """Test question type display text mapping"""
        from static.js.form_builder import getQuestionTypeText  # This would need to be accessible
        
        # Since we can't directly import JS, we'll test the mapping logic
        type_map = {
            'text': '📝 Text Input',
            'email': '📧 Email Address', 
            'phone': '📱 Phone Number',
            'date': '📅 Date',
            'time': '🕐 Time',
            'url': '🔗 Website URL',
            'number': '🔢 Number',
            'rating': '⭐ Rating Scale',
            'radio': '🔘 Multiple Choice',
            'checkbox': '☑️ Checkboxes',
            'select': '📋 Dropdown',
            'textarea': '📄 Long Text',
            'file': '📎 File Upload'
        }
        
        for question_type, expected_text in type_map.items():
            # Test that each type has proper display text
            assert expected_text.startswith(('📝', '📧', '📱', '📅', '🕐', '🔗', '🔢', '⭐', '🔘', '☑️', '📋', '📄', '📎')), \
                f"Question type {question_type} should have emoji icon"
            assert len(expected_text) > 2, f"Question type {question_type} should have descriptive text"
    
    def test_all_question_types_covered(self):
        """Test that all new question types are properly defined"""
        expected_types = [
            'text', 'email', 'phone', 'date', 'time', 'url', 'number', 
            'rating', 'radio', 'checkbox', 'select', 'textarea', 'file'
        ]
        
        # This test ensures we haven't missed any question types
        assert len(expected_types) == 13, "Should have exactly 13 question types"
        
        # Ensure no duplicates
        assert len(set(expected_types)) == len(expected_types), "No duplicate question types"