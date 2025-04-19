"""
Service for analyzing playlist characteristics.
"""
import logging
from collections import Counter

logger = logging.getLogger('music_recommender.analysis')

class PlaylistAnalyzer:
    """Analyzes playlist data to extract characteristics and patterns."""
    
    def __init__(self):
        """Initialize the playlist analyzer."""
        logger.info("Playlist analyzer initialized")
    
    def analyze_playlist(self, playlist_data):
        """
        Analyze a playlist to extract key characteristics.
        
        Args:
            playlist_data (dict): Playlist data containing tracks
            
        Returns:
            dict: Analysis results
        """
        if not playlist_data or not isinstance(playlist_data, dict):
            logger.error("Invalid playlist data provided for analysis")
            return {}
            
        tracks = playlist_data.get('tracks', [])
        if not tracks:
            logger.warning("No tracks found in playlist for analysis")
            return {}
            
        logger.info(f"Analyzing playlist with {len(tracks)} tracks")
        
        # Basic info
        analysis = {
            'track_count': len(tracks),
            'platform': playlist_data.get('platform', 'unknown')
        }
        
        # Extract artist data
        analysis.update(self._analyze_artists(tracks))
        
        # Extract genre data if available (Spotify only)
        if analysis['platform'] == 'spotify':
            analysis.update(self._analyze_genres(tracks))
        
        # Extract audio features if available (Spotify only)
        if analysis['platform'] == 'spotify':
            analysis.update(self._analyze_audio_features(tracks))
        
        # Extract popularity info (Spotify only)
        if analysis['platform'] == 'spotify':
            analysis.update(self._analyze_popularity(tracks))
        
        # General metrics for all platforms
        analysis.update(self._analyze_general_metrics(tracks))
        
        logger.info(f"Playlist analysis complete: {len(analysis)} metrics extracted")
        return analysis
    
    def _analyze_artists(self, tracks):
        """Extract artist-related information from tracks."""
        # Count artist occurrences
        artist_counter = Counter()
        for track in tracks:
            artist = track.get('artist', 'Unknown')
            artist_counter[artist] += 1
        
        # Get top artists by frequency
        top_artists = artist_counter.most_common(10)
        
        # Calculate artist diversity
        unique_artists = len(artist_counter)
        artist_diversity = unique_artists / len(tracks) if tracks else 0
        
        return {
            'top_artists': top_artists,
            'unique_artists': unique_artists,
            'artist_diversity': artist_diversity,
            'artist_distribution': dict(artist_counter.most_common())
        }
    
    def _analyze_genres(self, tracks):
        """Extract genre-related information from tracks."""
        # Note: This would normally require additional API calls to get artist genres
        # For simplicity, we'll just return placeholder data
        return {
            'genre_analysis': {
                'available': False,
                'message': 'Artist genre analysis requires additional data not available in basic playlist info'
            }
        }
    
    def _analyze_audio_features(self, tracks):
        """
        Audio features analysis is no longer supported by Spotify API for new applications.
        This method now returns a placeholder indicating features are not available.
        """
        logger.info("Audio Features API is no longer available for new applications - skipping analysis")
        return {
            'audio_features': {
                'available': False,
                'message': 'Audio features are no longer available through Spotify API'
            }
        }
    
    def _analyze_popularity(self, tracks):
        """Analyze track popularity."""
        popularity_values = [track.get('popularity', 0) for track in tracks if 'popularity' in track]
        
        if not popularity_values:
            return {
                'popularity': {
                    'available': False,
                    'message': 'No popularity data found'
                }
            }
        
        avg_popularity = sum(popularity_values) / len(popularity_values)
        
        # Categorize the playlist's mainstream appeal
        if avg_popularity >= 80:
            mainstream_level = "Very Mainstream"
        elif avg_popularity >= 60:
            mainstream_level = "Mainstream"
        elif avg_popularity >= 40:
            mainstream_level = "Mixed Popularity"
        elif avg_popularity >= 20:
            mainstream_level = "Niche"
        else:
            mainstream_level = "Very Niche"
        
        return {
            'popularity': {
                'available': True,
                'average': avg_popularity,
                'mainstream_level': mainstream_level
            }
        }
    
    def _analyze_general_metrics(self, tracks):
        """Extract general metrics applicable to all platforms."""
        # Calculate average track duration
        durations = [track.get('duration_ms', 0) for track in tracks if 'duration_ms' in track]
        avg_duration_ms = sum(durations) / len(durations) if durations else 0
        
        # Get album data
        album_counter = Counter()
        for track in tracks:
            album = track.get('album', 'Unknown')
            album_counter[album] += 1
        
        top_albums = album_counter.most_common(5)
        
        return {
            'general': {
                'avg_duration_ms': avg_duration_ms,
                'avg_duration_minutes': avg_duration_ms / 60000 if avg_duration_ms else 0,
                'top_albums': top_albums,
                'unique_albums': len(album_counter)
            }
        }