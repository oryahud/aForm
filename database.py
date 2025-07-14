"""
Database configuration and connection management for MongoDB
"""
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.client = None
        self.db = None
        self.users_collection = None
        self.forms_collection = None
    
    def init_app(self, app):
        """Initialize database connection with Flask app"""
        # Skip database initialization in testing mode
        if app.config.get('TESTING', False) or os.getenv('FLASK_ENV') == 'testing':
            logger.info("Skipping MongoDB initialization in testing mode")
            return
        
        # Get MongoDB configuration from environment
        mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        db_name = os.getenv('MONGODB_DB_NAME', 'aform')
        
        try:
            # Create MongoDB client
            self.client = MongoClient(
                mongo_uri,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=10000,         # 10 second connection timeout
                socketTimeoutMS=20000,          # 20 second socket timeout
                maxPoolSize=50,                 # Maximum number of connections
                waitQueueTimeoutMS=2000         # Wait queue timeout
            )
            
            # Test connection
            self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            
            # Get database
            self.db = self.client[db_name]
            
            # Get collections
            self.users_collection = self.db.users
            self.forms_collection = self.db.forms
            
            # Create indexes for better performance
            self._create_indexes()
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise Exception(f"Database connection failed: {e}")
    
    def _create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Users collection indexes
            self.users_collection.create_index("email", unique=True)
            self.users_collection.create_index("id", unique=True)
            
            # Forms collection indexes
            self.forms_collection.create_index("name", unique=True)
            self.forms_collection.create_index("created_by")
            self.forms_collection.create_index("status")
            self.forms_collection.create_index("permissions.admin")
            self.forms_collection.create_index("permissions.editor")
            self.forms_collection.create_index("permissions.viewer")
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")
    
    def get_client(self):
        """Get MongoDB client"""
        return self.client
    
    def get_database(self):
        """Get database instance"""
        return self.db
    
    def get_users_collection(self):
        """Get users collection"""
        return self.users_collection
    
    def get_forms_collection(self):
        """Get forms collection"""
        return self.forms_collection
    
    def close_connection(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")

# Global database manager instance
db_manager = DatabaseManager()