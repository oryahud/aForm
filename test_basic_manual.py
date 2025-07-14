#!/usr/bin/env python3
"""
Manual basic tests that don't require pytest
Run directly with: python test_basic_manual.py
"""

import sys
import os
import traceback

def test_basic_imports():
    """Test basic Python imports work"""
    try:
        import json
        import datetime
        import pathlib
        print("✅ Basic Python imports successful")
        return True
    except Exception as e:
        print(f"❌ Basic Python imports failed: {e}")
        return False

def test_project_structure():
    """Test project files exist"""
    required_files = [
        'app.py',
        'auth.py', 
        'database.py',
        'models.py',
        'requirements.txt'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    else:
        print("✅ All required project files present")
        return True

def test_app_imports():
    """Test that app modules can be imported"""
    try:
        # Add project root to path
        project_root = os.path.dirname(os.path.abspath(__file__))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        print(f"Project root: {project_root}")
        print(f"Python path: {sys.path[:3]}...")  # Show first 3 entries
        
        # Test individual imports
        try:
            import app
            print("✅ app.py imports successfully")
        except Exception as e:
            print(f"❌ app.py import failed: {e}")
            return False
        
        try:
            import auth
            print("✅ auth.py imports successfully")
        except Exception as e:
            print(f"❌ auth.py import failed: {e}")
            return False
        
        try:
            import database
            print("✅ database.py imports successfully")
        except Exception as e:
            print(f"❌ database.py import failed: {e}")
            return False
        
        try:
            import models
            print("✅ models.py imports successfully")
        except Exception as e:
            print(f"❌ models.py import failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ App imports failed: {e}")
        traceback.print_exc()
        return False

def test_dependencies():
    """Test that required dependencies are available"""
    required_deps = [
        'flask',
        'pymongo', 
        'pytest',
        'mongomock',
        'factory_boy'
    ]
    
    failed_deps = []
    for dep in required_deps:
        try:
            __import__(dep)
            print(f"✅ {dep} available")
        except ImportError:
            failed_deps.append(dep)
            print(f"❌ {dep} not available")
    
    return len(failed_deps) == 0

def test_flask_app():
    """Test Flask app can be created"""
    try:
        project_root = os.path.dirname(os.path.abspath(__file__))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        from app import app
        
        # Basic Flask app tests
        if hasattr(app, 'config'):
            print("✅ Flask app has config")
        else:
            print("❌ Flask app missing config")
            return False
            
        if hasattr(app, 'route'):
            print("✅ Flask app has routing")
        else:
            print("❌ Flask app missing routing")
            return False
        
        print("✅ Flask app creation successful")
        return True
        
    except Exception as e:
        print(f"❌ Flask app creation failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all basic tests"""
    print("🧪 Running Basic Manual Tests")
    print("=" * 40)
    
    tests = [
        test_basic_imports,
        test_project_structure,
        test_dependencies,
        test_app_imports,
        test_flask_app
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print(f"\n📋 Running {test.__name__}...")
        try:
            if test():
                passed += 1
            else:
                print(f"   Test {test.__name__} failed")
        except Exception as e:
            print(f"   Test {test.__name__} crashed: {e}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)