"""
Authentication service for Spotify API.
"""
import time
import logging
from spotipy.oauth2 import SpotifyOAuth
import config

logger = logging.getLogger('music_recommender.auth')

class SpotifyAuthManager:
    """Manages Spotify authentication and token handling."""
    
    def __init__(self):
        """Initialize the Spotify authentication manager."""
        self.client_id = config.SPOTIFY_CLIENT_ID
        self.client_secret = config.SPOTIFY_CLIENT_SECRET
        self.redirect_uri = config.SPOTIFY_REDIRECT_URI
        self.scope = " ".join(config.SPOTIFY_SCOPES)
        
        if not self.client_id or not self.client_secret:
            logger.error("Spotify API credentials not properly configured")
        else:
            logger.info("Spotify authentication manager initialized")
            
        # Initialize the OAuth manager
        self.sp_oauth = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope
        )
    
    def get_auth_url(self):
        """Get the Spotify authorization URL."""
        if not self.client_id or not self.client_secret:
            logger.error("Cannot generate auth URL: Spotify credentials not set")
            return None
            
        auth_url = self.sp_oauth.get_authorize_url()
        logger.debug(f"Generated Spotify auth URL: {auth_url[:50]}...")
        return auth_url
    
    def get_access_token(self, code):
        """Exchange code for access token."""
        try:
            token_info = self.sp_oauth.get_access_token(code)
            logger.info("Successfully obtained Spotify access token")
            return token_info
        except Exception as e:
            logger.error(f"Error getting access token: {str(e)}")
            return None
    
    def refresh_token(self, token_info):
        """Refresh the access token if expired."""
        if self._is_token_expired(token_info):
            logger.debug("Spotify token expired, refreshing...")
            try:
                refreshed_token = self.sp_oauth.refresh_access_token(token_info['refresh_token'])
                logger.info("Successfully refreshed Spotify token")
                return refreshed_token
            except Exception as e:
                logger.error(f"Error refreshing token: {str(e)}")
                return None
        return token_info
    
    def _is_token_expired(self, token_info):
        """Check if the token is expired or about to expire."""
        if not token_info:
            return True
            
        now = int(time.time())
        return token_info['expires_at'] - now < 60  # Less than 60 seconds remaining