"""
Configuration settings for the Music Recommender application.
"""
import os
import logging
from logging.handlers import RotatingFileHandler
import sys
from datetime import datetime
from dotenv import load_dotenv
import os


# Application settings
APP_NAME = "Music Recommender"
APP_VERSION = "1.0.0"

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configure logging
log_filename = f"logs/music_recommender_{datetime.now().strftime('%Y-%m-%d')}.log"

# Logger setup
logger = logging.getLogger('music_recommender')
logger.setLevel(logging.DEBUG)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_format = logging.Formatter('%(levelname)s - %(message)s')
console_handler.setFormatter(console_format)

# File handler
file_handler = RotatingFileHandler(log_filename, maxBytes=10485760, backupCount=5)  # 10MB max size, 5 backup files
file_handler.setLevel(logging.DEBUG)
file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_format)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# API Credentials
load_dotenv()
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# If no env variables, check if we can load from a local file (for development)
if not (SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET):
    try:
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    if key == 'SPOTIFY_CLIENT_ID':
                        SPOTIFY_CLIENT_ID = value
                    elif key == 'SPOTIFY_CLIENT_SECRET':
                        SPOTIFY_CLIENT_SECRET = value
    except FileNotFoundError:
        pass
    
    # If still not set, use defaults
    if not SPOTIFY_CLIENT_ID:
        logger.warning("SPOTIFY_CLIENT_ID not set in environment or .env file")
        SPOTIFY_CLIENT_ID = ""  # Don't hardcode credentials in the actual code
    
    if not SPOTIFY_CLIENT_SECRET:
        logger.warning("SPOTIFY_CLIENT_SECRET not set in environment or .env file")
        SPOTIFY_CLIENT_SECRET = ""  # Don't hardcode credentials in the actual code

# Spotify API settings
SPOTIFY_REDIRECT_URI = 'http://localhost:5000/callback'
SPOTIFY_SCOPES = [
    'playlist-read-private',
    'playlist-read-collaborative',
    'user-library-read',
    'user-read-private',
    'user-top-read'
]

# Application settings
MINIMUM_TRACKS = 10
DEFAULT_RECOMMENDATIONS = 10
MAX_RECOMMENDATIONS = 50

# Flask settings
SECRET_KEY = os.environ.get('SECRET_KEY', 'music_recommendation_system_dev')
DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 't')