#!/bin/bash
# Example script for setting environment variables for local testing
# Rename to setup-env.sh and add your actual API keys before running

# Spotify API Credentials
export CLIENT_ID="your_spotify_client_id_here"
export CLIENT_SECERET="your_spotify_client_secret_here"

# Weather API Credentials
export TOMORROW_IO_API_KEY="your_tomorrow_io_api_key_here"

# Flask App Settings
export SECRET_KEY="your_flask_secret_key_here"
export FLASK_ENV="development"
export PORT=5000

echo "Environment variables set for local development!" 