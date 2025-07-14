"""
Authentication module for OAuth2 with Google
"""
import os
import json
from functools import wraps
from flask import session, redirect, url_for, request, jsonify, current_app
from authlib.integrations.flask_client import OAuth
from datetime import datetime
from database import db_manager
from models import UserModel, FormModel

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
        """Load users from MongoDB"""
        return UserModel.get_all_users()
    
    def save_users(self, users):
        """Save users to MongoDB (deprecated - use UserModel methods)"""
        # This method is kept for backward compatibility but is deprecated
        # Individual user operations should use UserModel methods
        pass
    
    def get_user_by_email(self, email):
        """Get user by email"""
        return UserModel.get_user_by_email(email)
    
    def create_or_update_user(self, user_info):
        """Create or update user from OAuth response"""
        # Check if user exists
        existing_user = self.get_user_by_email(user_info['email'])
        
        if existing_user:
            # Update existing user
            update_data = {
                'name': user_info.get('name', existing_user.get('name')),
                'picture': user_info.get('picture', existing_user.get('picture'))
            }
            user = UserModel.update_user(existing_user['id'], update_data)
        else:
            # Create new user
            user = UserModel.create_user(user_info)
        
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
    
    def has_form_permission(self, form, permission_type):
        """Check if current user has specific permission on a form"""
        user = self.get_current_user()
        if not user:
            return False
        
        # Global admins have access to everything
        if user.get('role') == 'admin':
            return True
        
        user_id = user['id']
        permissions = form.get('permissions', {})
        
        # Check form-level permissions
        if permission_type == 'admin':
            return user_id in permissions.get('admin', [])
        elif permission_type == 'edit':
            return (user_id in permissions.get('admin', []) or 
                    user_id in permissions.get('editor', []))
        elif permission_type == 'view_submissions':
            return (user_id in permissions.get('admin', []) or 
                    user_id in permissions.get('editor', []) or
                    user_id in permissions.get('viewer', []))
        
        return False
    
    def get_user_forms(self, forms=None):
        """Get forms that the current user has access to"""
        user = self.get_current_user()
        if not user:
            return []
        
        # Global admins see all forms
        if user.get('role') == 'admin':
            return FormModel.get_all_forms()
        
        # Get user's accessible forms from MongoDB
        return FormModel.get_user_forms(user['id'])

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