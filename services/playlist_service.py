"""
Service for fetching playlist data from Spotify and YouTube Music.
"""
import logging
from urllib.parse import urlparse, parse_qs
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import config

# Try to import ytmusicapi, but make it optional
try:
    import ytmusicapi
    YTMUSIC_AVAILABLE = True
except ImportError:
    YTMUSIC_AVAILABLE = False

logger = logging.getLogger('music_recommender.playlist')

class PlaylistService:
    """Handles fetching playlist data from different music platforms."""
    
    def __init__(self, spotify_token=None):
        """
        Initialize the playlist service.
        
        Args:
            spotify_token (str, optional): Spotify access token
        """
        self.spotify = None
        self.ytmusic = None
        
        # Initialize Spotify client with client credentials for public access
        try:
            if config.SPOTIFY_CLIENT_ID and config.SPOTIFY_CLIENT_SECRET:
                client_credentials_manager = SpotifyClientCredentials(
                    client_id=config.SPOTIFY_CLIENT_ID,
                    client_secret=config.SPOTIFY_CLIENT_SECRET
                )
                self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
                logger.info("Spotify client initialized with client credentials (for public playlists)")
            else:
                logger.warning("Cannot initialize Spotify client: missing credentials")
        except Exception as e:
            logger.error(f"Failed to initialize Spotify client: {str(e)}")
        
        # If token provided, update to use that instead (for private playlists)
        if spotify_token:
            self.update_spotify_token(spotify_token)
        
        # Initialize YouTube Music client if available
        if YTMUSIC_AVAILABLE:
            try:
                self.ytmusic = ytmusicapi.YTMusic()
                logger.info("YouTube Music API initialized")
            except Exception as e:
                logger.error(f"Failed to initialize YouTube Music API: {str(e)}")
        else:
            logger.warning("ytmusicapi package not installed. YouTube Music features will be limited.")
    
    def update_spotify_token(self, token):
        """Update the Spotify client with a new token."""
        try:
            self.spotify = spotipy.Spotify(auth=token)
            logger.info("Spotify client updated with new token")
            return True
        except Exception as e:
            logger.error(f"Error updating Spotify token: {str(e)}")
            return False
    
    def extract_playlist_info(self, url):
        """
        Extract platform and playlist ID from a URL.
        
        Args:
            url (str): Playlist URL from Spotify or YouTube Music
            
        Returns:
            tuple: (platform, playlist_id) or (None, None) if not recognized
        """
        logger.debug(f"Extracting playlist info from URL: {url}")
        
        try:
            parsed_url = urlparse(url)
            
            # Check for Spotify URLs
            if 'spotify.com' in parsed_url.netloc:
                path_parts = parsed_url.path.strip('/').split('/')
                if len(path_parts) >= 2 and path_parts[0] == 'playlist':
                    playlist_id = path_parts[1]
                    logger.info(f"Detected Spotify playlist with ID: {playlist_id}")
                    return 'spotify', playlist_id
            
            # Check for YouTube Music URLs
            elif 'music.youtube.com' in parsed_url.netloc:
                query = parse_qs(parsed_url.query)
                if 'list' in query:
                    playlist_id = query['list'][0]
                    logger.info(f"Detected YouTube Music playlist with ID: {playlist_id}")
                    return 'youtube_music', playlist_id
            
            # Check for regular YouTube URLs that may contain playlists
            elif 'youtube.com' in parsed_url.netloc:
                query = parse_qs(parsed_url.query)
                if 'list' in query:
                    playlist_id = query['list'][0]
                    logger.info(f"Detected YouTube playlist with ID: {playlist_id}")
                    return 'youtube', playlist_id
            
            logger.warning(f"Unrecognized playlist URL format: {url}")
            return None, None
            
        except Exception as e:
            logger.error(f"Error extracting playlist info: {str(e)}")
            return None, None
    
    def get_spotify_playlist(self, playlist_id):
        """
        Fetch a playlist from Spotify.
        
        Args:
            playlist_id (str): Spotify playlist ID
            
        Returns:
            dict: Playlist data with tracks or None if failed
        """
        if not self.spotify:
            logger.error("Spotify client not initialized")
            return None
        
        try:
            logger.debug(f"Fetching Spotify playlist: {playlist_id}")
            
            # Get playlist metadata
            playlist_data = self.spotify.playlist(playlist_id)
            logger.info(f"Retrieved Spotify playlist: {playlist_data.get('name', 'Unknown')}")
            
            # Get all tracks
            tracks = []
            results = self.spotify.playlist_tracks(playlist_id)
            
            # Process first batch of tracks
            tracks.extend(self._process_spotify_tracks(results.get('items', [])))
            
            # Handle pagination
            while results.get('next'):
                logger.debug("Fetching next page of Spotify tracks")
                results = self.spotify.next(results)
                tracks.extend(self._process_spotify_tracks(results.get('items', [])))
            
            # Add audio features to tracks
            self._add_audio_features_to_tracks(tracks)
            
            return {
                'id': playlist_data.get('id'),
                'name': playlist_data.get('name', 'Unknown Playlist'),
                'description': playlist_data.get('description', ''),
                'owner': playlist_data.get('owner', {}).get('display_name', 'Unknown'),
                'tracks': tracks,
                'platform': 'spotify',
                'image_url': next(iter(playlist_data.get('images', [])), {}).get('url', '') if playlist_data.get('images') else ''
            }
            
        except Exception as e:
            logger.error(f"Error fetching Spotify playlist: {str(e)}")
            return None
    
    def _process_spotify_tracks(self, items):
        """Process Spotify track items and extract relevant information."""
        processed_tracks = []
        
        for item in items:
            track_data = item.get('track')
            if not track_data:
                continue
                
            try:
                track = {
                    'id': track_data.get('id', ''),
                    'name': track_data.get('name', 'Unknown'),
                    'artist': track_data.get('artists', [{}])[0].get('name', 'Unknown') if track_data.get('artists') else 'Unknown',
                    'artists': [artist.get('name', 'Unknown') for artist in track_data.get('artists', [])],
                    'album': track_data.get('album', {}).get('name', 'Unknown') if track_data.get('album') else 'Unknown',
                    'popularity': track_data.get('popularity', 0),
                    'preview_url': track_data.get('preview_url', ''),
                    'external_url': track_data.get('external_urls', {}).get('spotify', ''),
                    'duration_ms': track_data.get('duration_ms', 0),
                    'platform': 'spotify'
                }
                processed_tracks.append(track)
            except Exception as e:
                logger.warning(f"Error processing Spotify track: {str(e)}")
        
        return processed_tracks
    
    def _add_audio_features_to_tracks(self, tracks):
        """
        Audio features are no longer supported by Spotify API for new applications.
        This method is kept as a placeholder but doesn't fetch features.
        """
        logger.info("Audio Features API is no longer available for new applications - skipping")
        # Don't attempt to fetch audio features
    
    def get_youtube_music_playlist(self, playlist_id):
        """
        Fetch a playlist from YouTube Music.
        
        Args:
            playlist_id (str): YouTube Music playlist ID
            
        Returns:
            dict: Playlist data with tracks or None if failed
        """
        if not self.ytmusic:
            logger.error("YouTube Music client not initialized")
            return None
        
        try:
            logger.debug(f"Fetching YouTube Music playlist: {playlist_id}")
            
            playlist_data = self.ytmusic.get_playlist(playlist_id)
            logger.info(f"Retrieved YouTube Music playlist: {playlist_data.get('title', 'Unknown')}")
            
            tracks = []
            for item in playlist_data.get('tracks', []):
                try:
                    track = {
                        'id': item.get('videoId', ''),
                        'name': item.get('title', 'Unknown'),
                        'artist': item.get('artists', [{}])[0].get('name', 'Unknown') if item.get('artists') else 'Unknown',
                        'artists': [artist.get('name', 'Unknown') for artist in item.get('artists', [])],
                        'album': item.get('album', {}).get('name', 'Unknown') if item.get('album') else 'Unknown',
                        'platform': 'youtube_music',
                        'duration_ms': item.get('duration_seconds', 0) * 1000 if item.get('duration_seconds') else 0,
                        'external_url': f"https://music.youtube.com/watch?v={item.get('videoId')}" if item.get('videoId') else ''
                    }
                    tracks.append(track)
                except Exception as e:
                    logger.warning(f"Error processing YouTube Music track: {str(e)}")
            
            return {
                'id': playlist_id,
                'name': playlist_data.get('title', 'Unknown Playlist'),
                'description': playlist_data.get('description', ''),
                'owner': playlist_data.get('author', {}).get('name', 'Unknown'),
                'tracks': tracks,
                'platform': 'youtube_music',
                'image_url': playlist_data.get('thumbnails', [{}])[-1].get('url', '') if playlist_data.get('thumbnails') else ''
            }
            
        except Exception as e:
            logger.error(f"Error fetching YouTube Music playlist: {str(e)}")
            return None
    
    def get_playlist(self, url):
        """
        Get playlist data from a URL.
        
        Args:
            url (str): Playlist URL
            
        Returns:
            dict: Playlist data with tracks or None if failed
        """
        platform, playlist_id = self.extract_playlist_info(url)
        
        if not platform or not playlist_id:
            logger.error(f"Could not extract platform and playlist ID from URL: {url}")
            return None
        
        if platform == 'spotify':
            if not self.spotify:
                logger.error("Cannot fetch Spotify playlist: Spotify client not initialized")
                return None
            return self.get_spotify_playlist(playlist_id)
            
        elif platform in ['youtube_music', 'youtube']:
            if not self.ytmusic:
                logger.error("Cannot fetch YouTube Music playlist: YouTube Music client not initialized")
                return None
            return self.get_youtube_music_playlist(playlist_id)
        
        logger.error(f"Unsupported platform: {platform}")
        return None
    
    def validate_playlist(self, url, min_tracks=config.MINIMUM_TRACKS):
        """
        Validate if a playlist URL is valid and has enough tracks.
        
        Args:
            url (str): Playlist URL
            min_tracks (int): Minimum number of tracks required
            
        Returns:
            dict: Validation result
        """
        platform, playlist_id = self.extract_playlist_info(url)
        
        if not platform or not playlist_id:
            return {
                'valid': False,
                'error': 'Invalid playlist URL format. Please check the URL and try again.'
            }
        
        try:
            if platform == 'spotify' and self.spotify:
                # Just get basic playlist info without full track details
                playlist = self.spotify.playlist(playlist_id, fields='name,tracks.total')
                track_count = playlist.get('tracks', {}).get('total', 0)
                
                return {
                    'valid': True,
                    'platform': 'spotify',
                    'name': playlist.get('name', 'Unknown Playlist'),
                    'track_count': track_count,
                    'has_enough_tracks': track_count >= min_tracks
                }
                
            elif (platform == 'youtube_music' or platform == 'youtube') and self.ytmusic:
                playlist = self.ytmusic.get_playlist(playlist_id)
                track_count = len(playlist.get('tracks', []))
                
                return {
                    'valid': True,
                    'platform': 'youtube_music',
                    'name': playlist.get('title', 'Unknown Playlist'),
                    'track_count': track_count,
                    'has_enough_tracks': track_count >= min_tracks
                }
            
            else:
                return {
                    'valid': False,
                    'error': f"Platform {platform} client not initialized"
                }
                
        except Exception as e:
            logger.error(f"Error validating playlist: {str(e)}")
            return {
                'valid': False,
                'error': f"Error validating playlist: {str(e)}"
            }