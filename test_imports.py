#!/usr/bin/env python
"""
Test script to debug import issues
"""

def test_imports():
    """Test all imports needed by the application"""
    imports = {
        "Flask": "from flask import Flask",
        "SpotifyAPI": "from spotifyApi import SpotifyAPI",
        "Weather": "from weatherApi import Weather",
        "requests": "import requests",
        "urllib3": "import urllib3",
        "six": "import six"
    }
    
    results = {}
    
    for module, import_stmt in imports.items():
        try:
            exec(import_stmt)
            results[module] = "OK"
        except Exception as e:
            results[module] = f"ERROR: {str(e)}"
    
    # Print results
    print("\n=== Import Test Results ===")
    for module, status in results.items():
        print(f"{module}: {status}")
    
    # Check specific urllib3 paths
    try:
        import urllib3.packages
        print("\nurllib3.packages exists")
        try:
            import urllib3.packages.six
            print("urllib3.packages.six exists")
            try:
                import urllib3.packages.six.moves
                print("urllib3.packages.six.moves exists")
            except ImportError:
                print("urllib3.packages.six.moves MISSING")
        except ImportError:
            print("urllib3.packages.six MISSING")
    except ImportError:
        print("\nurllib3.packages MISSING")

if __name__ == "__main__":
    test_imports() 