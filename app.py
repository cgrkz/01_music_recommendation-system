"""
Main Flask application for Music Recommender.
"""
import os
import time
import logging
from flask import Flask, render_template, request, jsonify, redirect, session, url_for

import config
from services.auth_service import SpotifyAuthManager
from services.playlist_service import PlaylistService
from services.analysis_service import PlaylistAnalyzer
from services.recommendation_service import RecommendationService

# Configure logger
logger = logging.getLogger('music_recommender.app')

# Initialize Flask
app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config['DEBUG'] = config.DEBUG

# Initialize services
auth_manager = SpotifyAuthManager()
analyzer = PlaylistAnalyzer()

@app.route('/')
def index():
    """Render the main page."""
    logger.info("Loading index page")
    return render_template('index.html')

@app.route('/login-spotify')
def login_spotify():
    """Start the Spotify OAuth flow."""
    logger.info("Starting Spotify login flow")
    auth_url = auth_manager.get_auth_url()
    
    if not auth_url:
        logger.error("Failed to generate Spotify auth URL")
        return jsonify({'error': 'Could not generate Spotify authentication URL. Please check your API credentials.'}), 500
    
    return jsonify({'auth_url': auth_url})

@app.route('/callback')
def callback():
    """Handle the callback from Spotify OAuth."""
    logger.info("Received Spotify callback")
    code = request.args.get('code')
    
    if not code:
        logger.error("No authorization code received from Spotify")
        return redirect('/?error=no_code')
    
    token_info = auth_manager.get_access_token(code)
    
    if not token_info:
        logger.error("Failed to get access token from Spotify")
        return redirect('/?error=token_failure')
    
    session['spotify_token'] = token_info
    logger.info("Successfully authenticated with Spotify")
    
    return redirect('/')

@app.route('/validate-playlist', methods=['POST'])
def validate_playlist():
    """Validate if a playlist URL is valid and has enough tracks."""
    data = request.json
    playlist_url = data.get('playlist_url')
    
    if not playlist_url:
        logger.warning("No playlist URL provided for validation")
        return jsonify({'valid': False, 'error': 'No playlist URL provided'}), 400
    
    logger.info(f"Validating playlist URL: {playlist_url}")
    
    # Get Spotify token if available
    token = _get_spotify_token()
    
    # Initialize playlist service with token if available
    playlist_service = PlaylistService(token)
    
    # Validate the playlist
    validation_result = playlist_service.validate_playlist(playlist_url)
    
    if validation_result.get('valid', False):
        logger.info(f"Playlist validated successfully: {validation_result.get('name')} ({validation_result.get('track_count')} tracks)")
    else:
        logger.warning(f"Playlist validation failed: {validation_result.get('error')}")
    
    return jsonify(validation_result)

@app.route('/analyze-playlist', methods=['POST'])
def analyze_playlist():
    """Analyze a playlist and return its characteristics."""
    data = request.json
    playlist_url = data.get('playlist_url')
    
    if not playlist_url:
        logger.warning("No playlist URL provided for analysis")
        return jsonify({'error': 'No playlist URL provided'}), 400
    
    logger.info(f"Analyzing playlist: {playlist_url}")
    
    # Get Spotify token if available
    token = _get_spotify_token()
    
    # Initialize services with token if available
    playlist_service = PlaylistService(token)
    
    try:
        # Get playlist data
        playlist_data = playlist_service.get_playlist(playlist_url)
        
        if not playlist_data:
            logger.error("Failed to fetch playlist data")
            return jsonify({'error': 'Failed to fetch playlist data. Please check the URL and try again.'}), 400
        
        # Analyze the playlist
        analysis_results = analyzer.analyze_playlist(playlist_data)
        
        # Return results
        return jsonify({
            'status': 'success',
            'playlist': {
                'name': playlist_data.get('name'),
                'owner': playlist_data.get('owner'),
                'track_count': len(playlist_data.get('tracks', [])),
                'platform': playlist_data.get('platform'),
                'image_url': playlist_data.get('image_url', '')
            },
            'analysis': analysis_results
        })
        
    except Exception as e:
        logger.error(f"Error analyzing playlist: {str(e)}")
        return jsonify({'error': f'Error analyzing playlist: {str(e)}'}), 500

@app.route('/get-recommendations', methods=['POST'])
def get_recommendations():
    """Get recommendations based on a playlist URL."""
    data = request.json
    playlist_url = data.get('playlist_url')
    num_recommendations = int(data.get('num_recommendations', config.DEFAULT_RECOMMENDATIONS))
    
    # Limit number of recommendations
    num_recommendations = min(num_recommendations, config.MAX_RECOMMENDATIONS)
    
    if not playlist_url:
        logger.warning("No playlist URL provided for recommendations")
        return jsonify({'error': 'No playlist URL provided'}), 400
    
    logger.info(f"Getting recommendations for playlist: {playlist_url}")
    
    # Get Spotify token if available
    token = _get_spotify_token()
    
    # Initialize services with token if available
    playlist_service = PlaylistService(token)
    recommendation_service = RecommendationService(token)
    
    try:
        # Get playlist data
        playlist_data = playlist_service.get_playlist(playlist_url)
        
        if not playlist_data:
            logger.error("Failed to fetch playlist data")
            return jsonify({'error': 'Failed to fetch playlist data. Please check the URL and try again.'}), 400
        
        # Check if playlist has enough tracks
        if len(playlist_data.get('tracks', [])) < config.MINIMUM_TRACKS:
            error_message = f"Playlist has only {len(playlist_data.get('tracks', []))} tracks, but at least {config.MINIMUM_TRACKS} are needed for good recommendations."
            logger.warning(error_message)
            return jsonify({'error': error_message}), 400
        
        # Analyze the playlist
        analysis_results = analyzer.analyze_playlist(playlist_data)
        
        # Get recommendations
        recommendations = recommendation_service.get_recommendations(
            playlist_data, 
            analysis_results, 
            num_recommendations
        )
        
        # If no Spotify recommendations, try YouTube Music recommendations as fallback
        if playlist_data.get('platform') == 'spotify' and not recommendations:
            logger.info("No Spotify recommendations found, trying YouTube Music as fallback")
            youtube_recommendations = RecommendationService().get_youtube_music_recommendations(
                playlist_data, analysis_results, original_track_ids=set(), num_recommendations=num_recommendations
            )
            if youtube_recommendations:
                recommendations = youtube_recommendations
                logger.info(f"Got {len(recommendations)} YouTube Music recommendations as fallback")
        
        # Return results, even if no recommendations found
        return jsonify({
            'status': 'success',
            'playlist': {
                'name': playlist_data.get('name'),
                'owner': playlist_data.get('owner'),
                'track_count': len(playlist_data.get('tracks', [])),
                'platform': playlist_data.get('platform'),
                'image_url': playlist_data.get('image_url', '')
            },
            'analysis': analysis_results,
            'recommendations': recommendations
        })
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        return jsonify({'error': f'Error getting recommendations: {str(e)}'}), 500

def _get_spotify_token():
    """Get a valid Spotify access token from session."""
    token_info = session.get('spotify_token')
    
    if not token_info:
        logger.debug("No Spotify token found in session")
        return None
    
    # Check if token is expired
    now = int(time.time())
    is_expired = token_info.get('expires_at', 0) - now < 60
    
    if is_expired:
        logger.debug("Spotify token is expired, refreshing")
        # Refresh the token
        refreshed_token_info = auth_manager.refresh_token(token_info)
        
        if refreshed_token_info:
            # Update session
            session['spotify_token'] = refreshed_token_info
            logger.info("Successfully refreshed Spotify token")
            return refreshed_token_info.get('access_token')
        else:
            # Clear invalid token
            session.pop('spotify_token', None)
            logger.warning("Failed to refresh Spotify token, removed from session")
            return None
    
    return token_info.get('access_token')

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    logger.warning(f"404 error: {request.path}")
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    logger.error(f"500 error: {str(error)}")
    return render_template('error.html', error="Internal server error"), 500

if __name__ == '__main__':
    # Make sure template and static directories exist
    for directory in ['templates', 'static', 'static/css', 'static/js', 'static/img']:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    # Create error.html template if it doesn't exist
    if not os.path.exists('templates/error.html'):
        with open('templates/error.html', 'w') as f:
            f.write('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error - Music Recommender</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <div class="container">
        <div class="error-container">
            <h1>Oops! Something went wrong</h1>
            <p>{{ error }}</p>
            <a href="/" class="btn btn-primary">Go Back Home</a>
        </div>
    </div>
</body>
</html>
            ''')
    
    logger.info(f"Starting Music Recommender App on port 5000")
    app.run(debug=config.DEBUG, port=5000)