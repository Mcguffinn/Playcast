# Playcast

A web application that provides weather-based Spotify playlist recommendations.

## Features

- Gets weather information based on user location
- Recommends Spotify playlists that match the current weather mood
- Allows users to play the recommended playlists directly in the browser

## Deployment on Vercel

### Prerequisites

- A Vercel account
- Spotify API credentials (CLIENT_ID and CLIENT_SECRET)
- Weather API credentials

### Deploying to Vercel

1. Connect your repository to Vercel
2. Add the following environment variables in the Vercel project settings:
   - `CLIENT_ID`: Your Spotify API client ID
   - `CLIENT_SECERET`: Your Spotify API client secret
   - `SECRET_KEY`: A secret key for Flask session
   - Other API keys for weather services as needed

3. Deploy the application
   - Vercel will automatically detect the project as a Python application
   - It will use vercel.json for routing configuration

### Local Development

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file with the required environment variables:
```
CLIENT_ID=your_spotify_client_id
CLIENT_SECERET=your_spotify_client_secret
SECRET_KEY=your_flask_secret_key
FLASK_ENV=development
PORT=5000
```
6. Run the application: `python playcast.py`

## Project Structure

- `playcast.py`: Main Flask application
- `weatherApi.py`: Weather API integration
- `spotifyApi.py`: Spotify API integration
- `templates/`: HTML templates
- `static/`: Static assets (CSS, JS, icons)
- `api/index.py`: Vercel serverless function handler
- `vercel.json`: Vercel deployment configuration 