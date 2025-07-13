#!/usr/bin/env python3
"""
Simple server runner to debug Flask startup issues
"""
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app
    print("✓ App imported successfully")
    
    print("✓ Starting Flask server...")
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
    
except Exception as e:
    print(f"✗ Error starting server: {e}")
    import traceback
    traceback.print_exc()