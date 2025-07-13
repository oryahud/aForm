"""
Authentication module for OAuth2 with Google
"""
import os
import json
from functools import wraps
from flask import session, redirect, url_for, request, jsonify, current_app
from authlib.integrations.flask_client import OAuth
from datetime import datetime

class AuthManager:
    def __init__(self, app=None):
        self.oauth = OAuth()
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        self.oauth.init_app(app)
        
        # Only configure Google OAuth if credentials are provided
        client_id = app.config.get('GOOGLE_CLIENT_ID')
        client_secret = app.config.get('GOOGLE_CLIENT_SECRET')
        
        if client_id and client_secret and client_id != 'placeholder_client_id':
            # Configure Google OAuth without OpenID Connect to avoid JWT issues
            self.google = self.oauth.register(
                name='google',
                client_id=client_id,
                client_secret=client_secret,
                authorize_url='https://accounts.google.com/o/oauth2/auth',
                access_token_url='https://oauth2.googleapis.com/token',
                client_kwargs={
                    'scope': 'email profile'  # Remove 'openid' to avoid JWT validation
                },
            )
        else:
            # Set google to None if credentials not configured
            self.google = None
    
    def load_users(self):
        """Load users from JSON file"""
        if os.path.exists('users.json'):
            with open('users.json', 'r') as f:
                return json.load(f)
        return []
    
    def save_users(self, users):
        """Save users to JSON file"""
        with open('users.json', 'w') as f:
            json.dump(users, f, indent=2)
    
    def get_user_by_email(self, email):
        """Get user by email"""
        users = self.load_users()
        return next((user for user in users if user['email'] == email), None)
    
    def create_or_update_user(self, user_info):
        """Create or update user from OAuth response"""
        users = self.load_users()
        
        # Check if user exists
        existing_user = self.get_user_by_email(user_info['email'])
        
        if existing_user:
            # Update existing user
            existing_user['name'] = user_info.get('name', existing_user.get('name'))
            existing_user['picture'] = user_info.get('picture', existing_user.get('picture'))
            existing_user['last_login'] = datetime.now().isoformat()
            user = existing_user
        else:
            # Create new user with default role
            import hashlib
            user_id = hashlib.md5(user_info['email'].encode()).hexdigest()[:8]
            user = {
                'id': user_id,
                'email': user_info['email'],
                'name': user_info.get('name', ''),
                'picture': user_info.get('picture', ''),
                'role': 'user',  # Default role
                'created_at': datetime.now().isoformat(),
                'last_login': datetime.now().isoformat(),
                'status': 'active'
            }
            users.append(user)
        
        self.save_users(users)
        return user
    
    def get_current_user(self):
        """Get current logged-in user"""
        if 'user' in session:
            return session['user']
        return None
    
    def is_authenticated(self):
        """Check if user is authenticated"""
        return 'user' in session
    
    def has_role(self, role):
        """Check if current user has specific role"""
        user = self.get_current_user()
        if not user:
            return False
        return user.get('role') == role
    
    def has_permission(self, permission):
        """Check if current user has specific permission"""
        user = self.get_current_user()
        if not user:
            return False
        
        role = user.get('role', 'user')
        permissions = self.get_role_permissions(role)
        return permission in permissions
    
    def get_role_permissions(self, role):
        """Get permissions for a role"""
        role_permissions = {
            'admin': [
                'create_form', 'edit_form', 'delete_form', 'view_form',
                'view_submissions', 'delete_submissions', 'manage_users',
                'view_analytics', 'export_data'
            ],
            'editor': [
                'create_form', 'edit_form', 'delete_form', 'view_form',
                'view_submissions', 'delete_submissions'
            ],
            'user': [
                'create_form', 'edit_form', 'delete_form', 'view_form',
                'view_submissions'
            ],
            'viewer': [
                'view_form', 'view_submissions'
            ]
        }
        return role_permissions.get(role, [])

# Initialize auth manager
auth_manager = AuthManager()

def login_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not auth_manager.is_authenticated():
            return redirect(url_for('auth_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not auth_manager.is_authenticated():
                return redirect(url_for('auth_login', next=request.url))
            
            if not auth_manager.has_role(role):
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def permission_required(permission):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not auth_manager.is_authenticated():
                return redirect(url_for('auth_login', next=request.url))
            
            if not auth_manager.has_permission(permission):
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator