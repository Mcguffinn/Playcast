import sys
import os
import importlib.util
import traceback

# Add current directory to path to help with imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create a minimal Flask app that we can fall back to if imports fail
from flask import Flask, jsonify, render_template

try:
    # Attempt to import app from playcast
    from playcast import app
    print("Successfully imported the app from playcast.py")
except Exception as e:
    # If the import fails, create a minimal Flask app that displays the error
    error_message = str(e)
    traceback_str = traceback.format_exc()
    print(f"Failed to import app: {error_message}")
    print(f"Traceback: {traceback_str}")
    
    app = Flask(__name__, 
                static_url_path='/static', 
                static_folder='../static', 
                template_folder='../templates')
    
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def catch_all(path):
        error_info = {
            "error": "Application failed to start properly",
            "details": error_message,
            "traceback": traceback_str,
            "requested_path": path
        }
        
        # Try to render a template if it exists
        try:
            return render_template('base.html', error_message="We're experiencing technical difficulties. Please try again later.")
        except:
            # Or return JSON if templates aren't accessible
            return jsonify(error_info), 500

# This is needed for Vercel serverless functions
# The name 'app' is important as Vercel will look for it 