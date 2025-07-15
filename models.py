"""
Database models for users and forms
"""
from datetime import datetime
from pymongo.errors import DuplicateKeyError
from database import db_manager
import hashlib

try:
    from bson import ObjectId
except ImportError:
    # Fallback for testing environments without MongoDB
    ObjectId = str

def serialize_doc(doc):
    """Convert MongoDB document to JSON-serializable format"""
    if doc is None:
        return None
    
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    
    if isinstance(doc, dict):
        serialized = {}
        for key, value in doc.items():
            if hasattr(value, '__class__') and value.__class__.__name__ == 'ObjectId':
                serialized[key] = str(value)
            elif isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, (dict, list)):
                serialized[key] = serialize_doc(value)
            else:
                serialized[key] = value
        return serialized
    
    return doc

class UserModel:
    """User model for MongoDB operations"""
    
    @staticmethod
    def create_user(user_info):
        """Create a new user"""
        try:
            # Generate user ID from email
            user_id = hashlib.md5(user_info['email'].encode()).hexdigest()[:8]
            
            user_data = {
                'id': user_id,
                'email': user_info['email'],
                'name': user_info.get('name', ''),
                'picture': user_info.get('picture', ''),
                'role': 'user',  # Default role
                'created_at': datetime.now(),
                'last_login': datetime.now(),
                'status': 'active'
            }
            
            result = db_manager.get_users_collection().insert_one(user_data)
            user_data['_id'] = str(result.inserted_id)
            return user_data
            
        except DuplicateKeyError:
            raise ValueError("User with this email already exists")
    
    @staticmethod
    def update_user(user_id, update_data):
        """Update existing user"""
        update_data['last_login'] = datetime.now()
        
        result = db_manager.get_users_collection().update_one(
            {'id': user_id},
            {'$set': update_data}
        )
        
        if result.matched_count == 0:
            raise ValueError("User not found")
        
        return UserModel.get_user_by_id(user_id)
    
    @staticmethod
    def get_user_by_email(email):
        """Get user by email"""
        doc = db_manager.get_users_collection().find_one({'email': email})
        return serialize_doc(doc)
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID"""
        doc = db_manager.get_users_collection().find_one({'id': user_id})
        return serialize_doc(doc)
    
    @staticmethod
    def get_all_users():
        """Get all users"""
        docs = list(db_manager.get_users_collection().find())
        return serialize_doc(docs)
    
    @staticmethod
    def delete_user(user_id):
        """Delete user by ID"""
        result = db_manager.get_users_collection().delete_one({'id': user_id})
        return result.deleted_count > 0

class FormModel:
    """Form model for MongoDB operations"""
    
    @staticmethod
    def create_form(form_data):
        """Create a new form"""
        try:
            form_data['created_at'] = datetime.now()
            form_data['updated_at'] = datetime.now()
            
            result = db_manager.get_forms_collection().insert_one(form_data)
            form_data['_id'] = str(result.inserted_id)
            return form_data
            
        except DuplicateKeyError:
            raise ValueError("Form with this name already exists")
    
    @staticmethod
    def update_form(form_name, update_data):
        """Update existing form"""
        update_data['updated_at'] = datetime.now()
        
        result = db_manager.get_forms_collection().update_one(
            {'name': form_name},
            {'$set': update_data}
        )
        
        if result.matched_count == 0:
            raise ValueError("Form not found")
        
        return FormModel.get_form_by_name(form_name)
    
    @staticmethod
    def get_form_by_name(form_name):
        """Get form by name"""
        doc = db_manager.get_forms_collection().find_one({'name': form_name})
        return serialize_doc(doc)
    
    @staticmethod
    def get_all_forms():
        """Get all forms"""
        docs = list(db_manager.get_forms_collection().find())
        return serialize_doc(docs)
    
    @staticmethod
    def get_user_forms(user_id):
        """Get forms that user has access to"""
        query = {
            '$or': [
                {'permissions.admin': user_id},
                {'permissions.editor': user_id},
                {'permissions.viewer': user_id}
            ]
        }
        docs = list(db_manager.get_forms_collection().find(query))
        return serialize_doc(docs)
    
    @staticmethod
    def delete_form(form_name):
        """Delete form by name"""
        result = db_manager.get_forms_collection().delete_one({'name': form_name})
        return result.deleted_count > 0
    
    @staticmethod
    def add_submission(form_name, submission_data):
        """Add submission to form"""
        submission_data['submitted_at'] = datetime.now()
        
        result = db_manager.get_forms_collection().update_one(
            {'name': form_name},
            {
                '$push': {'submissions': submission_data},
                '$set': {'updated_at': datetime.now()}
            }
        )
        
        return result.matched_count > 0
    
    @staticmethod
    def delete_submission(form_name, submission_id):
        """Delete submission from form"""
        result = db_manager.get_forms_collection().update_one(
            {'name': form_name},
            {
                '$pull': {'submissions': {'id': submission_id}},
                '$set': {'updated_at': datetime.now()}
            }
        )
        
        return result.matched_count > 0
    
    @staticmethod
    def add_collaborator(form_name, user_id, role):
        """Add collaborator to form"""
        result = db_manager.get_forms_collection().update_one(
            {'name': form_name},
            {
                '$addToSet': {f'permissions.{role}': user_id},
                '$set': {'updated_at': datetime.now()}
            }
        )
        
        return result.matched_count > 0
    
    @staticmethod
    def remove_collaborator(form_name, user_id):
        """Remove collaborator from form"""
        result = db_manager.get_forms_collection().update_one(
            {'name': form_name},
            {
                '$pull': {
                    'permissions.admin': user_id,
                    'permissions.editor': user_id,
                    'permissions.viewer': user_id
                },
                '$set': {'updated_at': datetime.now()}
            }
        )
        
        return result.matched_count > 0