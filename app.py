from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_mail import Mail, Message
import json
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from auth import auth_manager, login_required, permission_required, role_required
from database import db_manager
from models import UserModel, FormModel

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'development_secret_key_change_in_production')

# Configure OAuth
app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')

# Configure Mail
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# Initialize services
mail = Mail(app)
auth_manager.init_app(app)

# Only initialize database if not in testing mode
if not app.config.get('TESTING', False) and not os.getenv('FLASK_ENV') == 'testing':
    try:
        db_manager.init_app(app)
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")
        print("Running without database connection (likely in testing mode)")

def load_forms():
    """Load forms from MongoDB (deprecated - use FormModel methods directly)"""
    # This method is kept for backward compatibility but is deprecated
    # Use FormModel.get_all_forms() directly instead
    return FormModel.get_all_forms()

def save_forms(forms):
    """Save forms to MongoDB (deprecated - use FormModel methods)"""
    # This method is kept for backward compatibility but is deprecated
    # Individual form operations should use FormModel methods
    pass

def send_invitation_email(to_email, inviter_name, form_name, role, form_url):
    """Send invitation email to collaborator"""
    try:
        if not app.config.get('MAIL_USERNAME') or app.config.get('MAIL_USERNAME') == 'your-email@gmail.com':
            print(f"📧 Email not configured - invitation would be sent to: {to_email}")
            print(f"   Form: {form_name} | Role: {role} | Inviter: {inviter_name}")
            print(f"   Form URL: {form_url}")
            return True
        
        subject = f"You've been invited to collaborate on '{form_name}'"
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2563eb;">Form Collaboration Invitation</h2>
            
            <p>Hi there!</p>
            
            <p><strong>{inviter_name}</strong> has invited you to collaborate on the form "<strong>{form_name}</strong>" as a <strong>{role.title()}</strong>.</p>
            
            <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin-top: 0;">What you can do as a {role.title()}:</h3>
                <ul>
                    {'<li>Edit form questions and settings</li><li>View form submissions</li>' if role == 'editor' else '<li>View form submissions</li>'}
                </ul>
            </div>
            
            <p>
                <a href="{form_url}" style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                    Access Form
                </a>
            </p>
            
            <p>If you don't have an account yet, you'll need to sign up first at <a href="{request.url_root}">aForm</a>.</p>
            
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
            <p style="color: #6b7280; font-size: 14px;">
                This invitation was sent by {inviter_name} through aForm. 
                If you weren't expecting this invitation, you can safely ignore this email.
            </p>
        </div>
        """
        
        msg = Message(
            subject=subject,
            recipients=[to_email],
            html=html_body
        )
        
        mail.send(msg)
        return True
        
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

@app.route('/')
@login_required
def index():
    current_user = auth_manager.get_current_user()
    
    # Get forms that user has access to (including form-level permissions)
    accessible_forms = auth_manager.get_user_forms()
    
    return render_template('my_forms_modern.html', forms=accessible_forms, current_user=current_user)

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
    
    # Check if form name already exists
    if FormModel.get_form_by_name(form_name):
        return jsonify({'error': 'Form name already exists'}), 400
    
    current_user = auth_manager.get_current_user()
    
    # Create new form with initial question and form-level permissions
    new_form = {
        'name': form_name,
        'status': 'draft',
        'created_by': current_user['id'],
        'created_by_name': current_user['name'],
        'permissions': {
            'admin': [current_user['id']],  # Form admin (creator)
            'editor': [],  # Users who can edit the form
            'viewer': []   # Users who can view submissions (beyond public link)
        },
        'invites': [],  # Pending invitations
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
    
    FormModel.create_form(new_form)
    
    return jsonify({'message': 'Form created successfully!', 'redirect': f'/form/{form_name}'})

@app.route('/form/<form_name>')
@login_required
@permission_required('edit_form')
def edit_form(form_name):
    form = FormModel.get_form_by_name(form_name)
    
    if not form:
        return redirect(url_for('index'))
    
    # Check form-level permissions
    current_user = auth_manager.get_current_user()
    if not auth_manager.has_form_permission(form, 'edit'):
        return jsonify({'error': 'Access denied'}), 403
    
    return render_template('form_builder_modern.html', form=form, current_user=current_user)

@app.route('/api/form/<form_name>/invite', methods=['POST'])
@login_required
def invite_user_to_form(form_name):
    """Invite a user to collaborate on a form"""
    form = FormModel.get_form_by_name(form_name)
    
    if not form:
        return jsonify({'error': 'Form not found'}), 404
    
    # Check if user is form admin
    if not auth_manager.has_form_permission(form, 'admin'):
        return jsonify({'error': 'Only form admins can invite users'}), 403
    
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    role = data.get('role', 'viewer')  # editor, viewer
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    if role not in ['editor', 'viewer']:
        return jsonify({'error': 'Invalid role'}), 400
    
    # Check if user exists
    invited_user = UserModel.get_user_by_email(email)
    
    if not invited_user:
        return jsonify({'error': 'User not found. They must sign up first.'}), 404
    
    invited_user_id = invited_user['id']
    current_user = auth_manager.get_current_user()
    
    # Check if user already has permission
    permissions = form.get('permissions', {})
    if (invited_user_id in permissions.get('admin', []) or
        invited_user_id in permissions.get('editor', []) or
        invited_user_id in permissions.get('viewer', [])):
        return jsonify({'error': 'User already has access to this form'}), 400
    
    # Add user to form permissions using FormModel
    FormModel.add_collaborator(form_name, invited_user_id, role)
    
    # Send invitation email
    form_url = f"{request.url_root}form/{form_name}"
    email_sent = send_invitation_email(
        to_email=email,
        inviter_name=current_user['name'],
        form_name=form_name,
        role=role,
        form_url=form_url
    )
    
    email_status = " (email sent)" if email_sent else " (email failed)"
    
    return jsonify({
        'message': f'User {email} invited as {role}{email_status}',
        'user': {
            'id': invited_user_id,
            'name': invited_user['name'],
            'email': invited_user['email'],
            'role': role
        }
    })

@app.route('/api/form/<form_name>/collaborators', methods=['GET'])
@login_required
def get_form_collaborators(form_name):
    """Get list of form collaborators"""
    form = FormModel.get_form_by_name(form_name)
    
    if not form:
        return jsonify({'error': 'Form not found'}), 404
    
    # Check if user has access to view collaborators
    if not auth_manager.has_form_permission(form, 'edit'):
        return jsonify({'error': 'Access denied'}), 403
    
    users = UserModel.get_all_users()
    users_by_id = {u['id']: u for u in users}
    
    permissions = form.get('permissions', {})
    collaborators = []
    
    # Add all collaborators with their roles
    for role in ['admin', 'editor', 'viewer']:
        for user_id in permissions.get(role, []):
            if user_id in users_by_id:
                user = users_by_id[user_id]
                collaborators.append({
                    'id': user['id'],
                    'name': user['name'],
                    'email': user['email'],
                    'role': role,
                    'is_creator': user_id == form.get('created_by')
                })
    
    return jsonify({'collaborators': collaborators})

@app.route('/api/form/<form_name>/collaborators/<user_id>', methods=['DELETE'])
@login_required
def remove_form_collaborator(form_name, user_id):
    """Remove a collaborator from a form"""
    form = FormModel.get_form_by_name(form_name)
    
    if not form:
        return jsonify({'error': 'Form not found'}), 404
    
    # Check if user is form admin
    if not auth_manager.has_form_permission(form, 'admin'):
        return jsonify({'error': 'Only form admins can remove collaborators'}), 403
    
    # Don't allow removing the creator
    if user_id == form.get('created_by'):
        return jsonify({'error': 'Cannot remove form creator'}), 400
    
    # Check if user exists in collaborators
    permissions = form.get('permissions', {})
    user_exists = False
    
    for role in ['admin', 'editor', 'viewer']:
        if user_id in permissions.get(role, []):
            user_exists = True
            break
    
    if not user_exists:
        return jsonify({'error': 'User not found in collaborators'}), 404
    
    # Remove user from all permission levels using FormModel
    success = FormModel.remove_collaborator(form_name, user_id)
    
    if not success:
        return jsonify({'error': 'Failed to remove collaborator'}), 500
    
    return jsonify({'message': 'Collaborator removed successfully'})

@app.route('/api/form/<form_name>/save', methods=['POST'])
@login_required
def save_form_data(form_name):
    form = FormModel.get_form_by_name(form_name)
    
    if not form:
        return jsonify({'error': 'Form not found'}), 404
    
    # Check form-level edit permission
    if not auth_manager.has_form_permission(form, 'edit'):
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    update_data = {
        'questions': data.get('questions', [])
    }
    
    try:
        FormModel.update_form(form_name, update_data)
        return jsonify({'message': 'Form saved successfully'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/form/<form_name>/question', methods=['POST'])
@login_required
def add_question(form_name):
    form = FormModel.get_form_by_name(form_name)
    
    if not form:
        return jsonify({'error': 'Form not found'}), 404
    
    # Check form-level edit permission
    if not auth_manager.has_form_permission(form, 'edit'):
        return jsonify({'error': 'Access denied'}), 403
    
    questions = form.get('questions', [])
    question_num = len(questions) + 1
    new_question = {
        'id': f'q_{question_num}',
        'title': f'Question {question_num}',
        'text': '',
        'type': 'text',
        'required': False
    }
    
    questions.append(new_question)
    update_data = {'questions': questions}
    
    try:
        FormModel.update_form(form_name, update_data)
        return jsonify({'question': new_question})
    except ValueError as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/form/<form_name>/publish', methods=['POST'])
@login_required
def publish_form(form_name):
    form = FormModel.get_form_by_name(form_name)
    
    if not form:
        return jsonify({'error': 'Form not found'}), 404
    
    # Check form-level admin permission (only admins can publish)
    if not auth_manager.has_form_permission(form, 'admin'):
        return jsonify({'error': 'Only form admins can publish forms'}), 403
    
    update_data = {'status': 'published'}
    
    try:
        FormModel.update_form(form_name, update_data)
        share_url = f"{request.url_root}submit/{form_name}"
        return jsonify({'message': 'Form published successfully!', 'share_url': share_url})
    except ValueError as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/form/<form_name>/hide', methods=['POST'])
@login_required
def hide_form(form_name):
    form = FormModel.get_form_by_name(form_name)
    
    if not form:
        return jsonify({'error': 'Form not found'}), 404
    
    # Check form-level admin permission (only admins can hide)
    if not auth_manager.has_form_permission(form, 'admin'):
        return jsonify({'error': 'Only form admins can hide forms'}), 403
    
    update_data = {'status': 'draft'}
    
    try:
        FormModel.update_form(form_name, update_data)
        return jsonify({'message': 'Form hidden successfully!'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 500

@app.route('/submit/<form_name>')
def public_form(form_name):
    form = FormModel.get_form_by_name(form_name)
    
    if not form or form.get('status') != 'published':
        return render_template('error.html', message='Form not found or not published'), 404
    
    return render_template('public_form_modern.html', form=form)

@app.route('/api/form/<form_name>/submit', methods=['POST'])
def submit_form(form_name):
    form = FormModel.get_form_by_name(form_name)
    
    if not form or form.get('status') != 'published':
        return jsonify({'error': 'Form not found or not published'}), 404
    
    data = request.get_json()
    responses = data.get('responses', {})
    
    # Create submission
    submission = {
        'id': str(uuid.uuid4()),
        'responses': responses
    }
    
    # Add submission to form using FormModel
    success = FormModel.add_submission(form_name, submission)
    
    if not success:
        return jsonify({'error': 'Failed to submit form'}), 500
    
    return jsonify({'message': 'Form submitted successfully!', 'submission_id': submission['id']})

@app.route('/form/<form_name>/submissions')
@login_required
def view_submissions(form_name):
    form = FormModel.get_form_by_name(form_name)
    
    if not form:
        return redirect(url_for('index'))
    
    # Check form-level view submissions permission
    if not auth_manager.has_form_permission(form, 'view_submissions'):
        return jsonify({'error': 'Access denied'}), 403
    
    return render_template('submissions.html', form=form)


@app.route('/api/form/<form_name>/delete', methods=['DELETE'])
@login_required
@permission_required('delete_form')
def delete_form(form_name):
    form = FormModel.get_form_by_name(form_name)
    
    if not form:
        return jsonify({'error': 'Form not found'}), 404
    
    # Check form-level admin permission (only form admins can delete)
    if not auth_manager.has_form_permission(form, 'admin'):
        return jsonify({'error': 'Only form admins can delete forms'}), 403
    
    success = FormModel.delete_form(form_name)
    
    if not success:
        return jsonify({'error': 'Failed to delete form'}), 500
    
    return jsonify({'message': 'Form deleted successfully'})

@app.route('/api/form/<form_name>/submission/<submission_id>/delete', methods=['DELETE'])
def delete_submission(form_name, submission_id):
    form = FormModel.get_form_by_name(form_name)
    
    if not form:
        return jsonify({'error': 'Form not found'}), 404
    
    # Check if submission exists
    submissions = form.get('submissions', [])
    submission_exists = any(s['id'] == submission_id for s in submissions)
    
    if not submission_exists:
        return jsonify({'error': 'Submission not found'}), 404
    
    success = FormModel.delete_submission(form_name, submission_id)
    
    if not success:
        return jsonify({'error': 'Failed to delete submission'}), 500
    
    return jsonify({'message': 'Submission deleted successfully'})


@app.route('/my-forms')
@login_required
def my_forms():
    current_user = auth_manager.get_current_user()
    
    # Get forms that user has access to (including form-level permissions)
    accessible_forms = auth_manager.get_user_forms()
    
    return render_template('my_forms_modern.html', forms=accessible_forms, current_user=current_user)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)