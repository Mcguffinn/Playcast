#!/usr/bin/env python
"""
Test script to check if the application will run on Vercel
"""

def test_core_imports():
    """Test just the core Flask imports that should be safe on Vercel"""
    try:
        from flask import Flask, render_template, jsonify, request
        print("✅ Flask imports successful")
        
        # Test creating a Flask app
        app = Flask(__name__)
        print("✅ Flask app created successfully")
        
        return True
    except Exception as e:
        print(f"❌ Error with core Flask imports: {str(e)}")
        return False

def test_static_paths():
    """Test if the static and template paths are accessible"""
    import os
    
    static_path = os.path.join(os.path.dirname(__file__), 'static')
    templates_path = os.path.join(os.path.dirname(__file__), 'templates')
    
    print(f"Static path: {static_path} - {'✅ exists' if os.path.exists(static_path) else '❌ missing'}")
    print(f"Templates path: {templates_path} - {'✅ exists' if os.path.exists(templates_path) else '❌ missing'}")

if __name__ == "__main__":
    print("Testing core functionality for Vercel deployment...\n")
    
    if test_core_imports():
        test_static_paths()
        print("\n✅ Basic tests passed! The app should be able to deploy on Vercel.")
    else:
        print("\n❌ Tests failed. The app may not work properly on Vercel.") 