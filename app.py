from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import json
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from auth import auth_manager, login_required, permission_required, role_required

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'development_secret_key_change_in_production')

# Configure OAuth
app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')

# Initialize auth manager
auth_manager.init_app(app)

def load_forms():
    if os.path.exists('forms.json'):
        with open('forms.json', 'r') as f:
            return json.load(f)
    return []

def save_forms(forms):
    with open('forms.json', 'w') as f:
        json.dump(forms, f, indent=2)

@app.route('/')
@login_required
def index():
    current_user = auth_manager.get_current_user()
    forms = load_forms()
    
    # Filter forms by user (unless admin)
    if not auth_manager.has_role('admin'):
        user_id = current_user['id']
        forms = [form for form in forms if form.get('created_by') == user_id]
    
    return render_template('my_forms_modern.html', forms=forms, current_user=current_user)

# Authentication Routes
@app.route('/login')
def auth_login():
    if auth_manager.is_authenticated():
        return redirect(url_for('index'))
    
    # Check if Google OAuth is configured
    if not auth_manager.google:
        return redirect(url_for('login_page'))
    
    redirect_uri = url_for('auth_callback', _external=True)
    return auth_manager.google.authorize_redirect(redirect_uri)

@app.route('/auth/callback')
def auth_callback():
    print("=== AUTH CALLBACK STARTED ===")
    
    try:
        # Get the authorization code from the callback
        code = request.args.get('code')
        if not code:
            raise Exception("No authorization code received")
        
        print(f"=== CODE RECEIVED: {bool(code)} ===")
        
        # Exchange code for access token using requests
        import requests
        token_data = {
            'client_id': app.config['GOOGLE_CLIENT_ID'],
            'client_secret': app.config['GOOGLE_CLIENT_SECRET'],
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': url_for('auth_callback', _external=True)
        }
        
        # Get access token
        token_response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
        token_json = token_response.json()
        
        if 'access_token' not in token_json:
            raise Exception(f"Token exchange failed: {token_json}")
        
        access_token = token_json['access_token']
        print(f"=== ACCESS TOKEN RECEIVED ===")
        
        # Get user info using access token
        userinfo_response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        user_info = userinfo_response.json()
        
        print(f"=== USER INFO: {user_info.get('email')} ===")
        
        # Validate we have required user info
        if not user_info.get('email'):
            raise Exception("No email received from Google")
        
        # Create or update user in our database
        user = auth_manager.create_or_update_user(user_info)
        session['user'] = user
        
        print(f"=== USER SET IN SESSION: {user['email']} (ID: {user['id']}) ===")
        
        return redirect(url_for('index'))
        
    except Exception as e:
        print(f"=== CALLBACK ERROR: {e} ===")
        import traceback
        traceback.print_exc()
        return f"<h1>Callback Error</h1><p>{str(e)}</p><a href='/login-page'>Back to Login</a>"

@app.route('/logout')
def auth_logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/login-page')
def login_page():
    if auth_manager.is_authenticated():
        return redirect(url_for('index'))
    
    # Check if Google OAuth is configured
    google_configured = auth_manager.google is not None
    return render_template('login.html', google_configured=google_configured)

@app.route('/dev-login')
def dev_login():
    """Development login for testing without Google OAuth"""
    if os.getenv('FLASK_ENV') == 'development':
        # Create a test user
        test_user_info = {
            'email': 'test@example.com',
            'name': 'Test User',
            'picture': ''
        }
        
        user = auth_manager.create_or_update_user(test_user_info)
        session['user'] = user
        
        return redirect(url_for('index'))
    
    return redirect(url_for('login_page'))

@app.route('/test-callback')
def test_callback():
    """Test route to verify callback URL is accessible"""
    return f"""
    <h1>Callback Test</h1>
    <p>This route works!</p>
    <p>Expected callback URL: {url_for('auth_callback', _external=True)}</p>
    <a href="/login-page">Back to Login</a>
    """

@app.route('/create-form', methods=['POST'])
@login_required
@permission_required('create_form')
def create_form():
    data = request.get_json()
    form_name = data.get('name', '').strip()
    
    if not form_name:
        return jsonify({'error': 'Form name is required'}), 400
    
    forms = load_forms()
    
    # Check if form name already exists
    if any(form['name'] == form_name for form in forms):
        return jsonify({'error': 'Form name already exists'}), 400
    
    current_user = auth_manager.get_current_user()
    
    # Create new form with initial question
    new_form = {
        'name': form_name,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'status': 'draft',
        'created_by': current_user['id'],
        'created_by_name': current_user['name'],
        'submissions': [],
        'questions': [
            {
                'id': 'q_1',
                'title': 'Question 1',
                'text': '',
                'type': 'text',
                'required': False
            }
        ]
    }
    
    forms.append(new_form)
    save_forms(forms)
    
    return jsonify({'message': 'Form created successfully!', 'redirect': f'/form/{form_name}'})

@app.route('/form/<form_name>')
@login_required
@permission_required('edit_form')
def edit_form(form_name):
    forms = load_forms()
    form = next((f for f in forms if f['name'] == form_name), None)
    
    if not form:
        return redirect(url_for('index'))
    
    # Check if user owns this form (unless admin)
    current_user = auth_manager.get_current_user()
    if not auth_manager.has_role('admin') and form.get('created_by') != current_user['id']:
        return jsonify({'error': 'Access denied'}), 403
    
    return render_template('form_builder_modern.html', form=form, current_user=current_user)

@app.route('/api/form/<form_name>/save', methods=['POST'])
def save_form_data(form_name):
    forms = load_forms()
    form_index = next((i for i, f in enumerate(forms) if f['name'] == form_name), None)
    
    if form_index is None:
        return jsonify({'error': 'Form not found'}), 404
    
    data = request.get_json()
    forms[form_index]['questions'] = data.get('questions', [])
    forms[form_index]['updated_at'] = datetime.now().isoformat()
    
    save_forms(forms)
    return jsonify({'message': 'Form saved successfully'})

@app.route('/api/form/<form_name>/question', methods=['POST'])
def add_question(form_name):
    forms = load_forms()
    form_index = next((i for i, f in enumerate(forms) if f['name'] == form_name), None)
    
    if form_index is None:
        return jsonify({'error': 'Form not found'}), 404
    
    questions = forms[form_index]['questions']
    question_num = len(questions) + 1
    new_question = {
        'id': f'q_{question_num}',
        'title': f'Question {question_num}',
        'text': '',
        'type': 'text',
        'required': False
    }
    
    questions.append(new_question)
    forms[form_index]['updated_at'] = datetime.now().isoformat()
    save_forms(forms)
    
    return jsonify({'question': new_question})

@app.route('/api/form/<form_name>/publish', methods=['POST'])
def publish_form(form_name):
    forms = load_forms()
    form_index = next((i for i, f in enumerate(forms) if f['name'] == form_name), None)
    
    if form_index is None:
        return jsonify({'error': 'Form not found'}), 404
    
    forms[form_index]['status'] = 'published'
    forms[form_index]['updated_at'] = datetime.now().isoformat()
    save_forms(forms)
    
    share_url = f"{request.url_root}submit/{form_name}"
    return jsonify({'message': 'Form published successfully!', 'share_url': share_url})

@app.route('/api/form/<form_name>/hide', methods=['POST'])
def hide_form(form_name):
    forms = load_forms()
    form_index = next((i for i, f in enumerate(forms) if f['name'] == form_name), None)
    
    if form_index is None:
        return jsonify({'error': 'Form not found'}), 404
    
    forms[form_index]['status'] = 'draft'
    forms[form_index]['updated_at'] = datetime.now().isoformat()
    save_forms(forms)
    
    return jsonify({'message': 'Form hidden successfully!'})

@app.route('/submit/<form_name>')
def public_form(form_name):
    forms = load_forms()
    form = next((f for f in forms if f['name'] == form_name), None)
    
    if not form or form.get('status') != 'published':
        return render_template('error.html', message='Form not found or not published'), 404
    
    return render_template('public_form_modern.html', form=form)

@app.route('/api/form/<form_name>/submit', methods=['POST'])
def submit_form(form_name):
    forms = load_forms()
    form_index = next((i for i, f in enumerate(forms) if f['name'] == form_name), None)
    
    if form_index is None or forms[form_index].get('status') != 'published':
        return jsonify({'error': 'Form not found or not published'}), 404
    
    data = request.get_json()
    responses = data.get('responses', {})
    
    # Create submission
    submission = {
        'id': str(uuid.uuid4()),
        'submitted_at': datetime.now().isoformat(),
        'responses': responses
    }
    
    # Add to form submissions
    if 'submissions' not in forms[form_index]:
        forms[form_index]['submissions'] = []
    
    forms[form_index]['submissions'].append(submission)
    save_forms(forms)
    
    return jsonify({'message': 'Form submitted successfully!', 'submission_id': submission['id']})

@app.route('/form/<form_name>/submissions')
def view_submissions(form_name):
    forms = load_forms()
    form = next((f for f in forms if f['name'] == form_name), None)
    
    if not form:
        return redirect(url_for('index'))
    
    return render_template('submissions.html', form=form)


@app.route('/api/form/<form_name>/delete', methods=['DELETE'])
@login_required
@permission_required('delete_form')
def delete_form(form_name):
    forms = load_forms()
    form_index = next((i for i, f in enumerate(forms) if f['name'] == form_name), None)
    
    if form_index is None:
        return jsonify({'error': 'Form not found'}), 404
    
    # Check if user owns this form (unless admin)
    current_user = auth_manager.get_current_user()
    if not auth_manager.has_role('admin') and forms[form_index].get('created_by') != current_user['id']:
        return jsonify({'error': 'Access denied'}), 403
    
    forms.pop(form_index)
    save_forms(forms)
    
    return jsonify({'message': 'Form deleted successfully'})

@app.route('/api/form/<form_name>/submission/<submission_id>/delete', methods=['DELETE'])
def delete_submission(form_name, submission_id):
    forms = load_forms()
    form_index = next((i for i, f in enumerate(forms) if f['name'] == form_name), None)
    
    if form_index is None:
        return jsonify({'error': 'Form not found'}), 404
    
    submissions = forms[form_index].get('submissions', [])
    submission_index = next((i for i, s in enumerate(submissions) if s['id'] == submission_id), None)
    
    if submission_index is None:
        return jsonify({'error': 'Submission not found'}), 404
    
    forms[form_index]['submissions'].pop(submission_index)
    forms[form_index]['updated_at'] = datetime.now().isoformat()
    save_forms(forms)
    
    return jsonify({'message': 'Submission deleted successfully'})


@app.route('/my-forms')
def my_forms():
    forms = load_forms()
    return render_template('my_forms.html', forms=forms)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)