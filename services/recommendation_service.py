"""
Service for generating music recommendations based on playlist analysis.
"""
import logging
import random
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import config

# Try to import ytmusicapi, but make it optional
try:
    import ytmusicapi
    YTMUSIC_AVAILABLE = True
except ImportError:
    YTMUSIC_AVAILABLE = False

logger = logging.getLogger('music_recommender.recommendation')

class RecommendationService:
    """Generates music recommendations based on playlist analysis."""
    
    def __init__(self, spotify_token=None):
        """
        Initialize the recommendation service.
        
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
                logger.info("Spotify client initialized with client credentials for recommendations")
            else:
                logger.warning("Cannot initialize Spotify client for recommendations: missing credentials")
        except Exception as e:
            logger.error(f"Failed to initialize Spotify client for recommendations: {str(e)}")
        
        # If token provided, update to use that instead (for better recommendations)
        if spotify_token:
            self.update_spotify_token(spotify_token)
        
        # Initialize YouTube Music client if available
        if YTMUSIC_AVAILABLE:
            try:
                self.ytmusic = ytmusicapi.YTMusic()
                logger.info("YouTube Music API initialized for recommendations")
            except Exception as e:
                logger.error(f"Failed to initialize YouTube Music API: {str(e)}")
        else:
            logger.warning("ytmusicapi package not installed. YouTube Music recommendations will be limited.")
    
    def update_spotify_token(self, token):
        """Update the Spotify client with a new token."""
        try:
            self.spotify = spotipy.Spotify(auth=token)
            logger.info("Spotify client updated with new token for recommendations")
            return True
        except Exception as e:
            logger.error(f"Error updating Spotify token in recommendation service: {str(e)}")
            return False
    
    def get_recommendations(self, playlist_data, analysis, num_recommendations=10):
        """
        Generate recommendations based on playlist analysis.
        
        Args:
            playlist_data (dict): Playlist data with tracks
            analysis (dict): Playlist analysis results
            num_recommendations (int): Number of recommendations to generate
            
        Returns:
            list: Recommended tracks
        """
        if not playlist_data or not analysis:
            logger.error("Cannot generate recommendations without playlist data and analysis")
            return []
        
        platform = playlist_data.get('platform', 'unknown')
        logger.info(f"Generating {num_recommendations} recommendations for {platform} playlist")
        
        # Track IDs in the original playlist (to avoid recommending same tracks)
        original_track_ids = set(track.get('id', '') for track in playlist_data.get('tracks', []))
        
        if platform == 'spotify':
            return self._get_spotify_recommendations(playlist_data, analysis, original_track_ids, num_recommendations)
        elif platform in ['youtube_music', 'youtube']:
            return self._get_youtube_music_recommendations(playlist_data, analysis, original_track_ids, num_recommendations)
        else:
            logger.error(f"Unsupported platform for recommendations: {platform}")
            return []
    
    def get_youtube_music_recommendations(self, playlist_data, analysis, original_track_ids, num_recommendations=10):
        """
        Directly get YouTube Music recommendations (useful as a fallback).
        
        Args:
            playlist_data (dict): Playlist data with tracks
            analysis (dict): Playlist analysis results
            original_track_ids (set): Set of track IDs to exclude
            num_recommendations (int): Number of recommendations to generate
            
        Returns:
            list: Recommended tracks
        """
        if not self.ytmusic:
            logger.error("YouTube Music client not initialized for fallback recommendations")
            return []
        
        logger.info(f"Getting YouTube Music recommendations as fallback")
        return self._get_youtube_music_recommendations(playlist_data, analysis, original_track_ids, num_recommendations)
    
    def _get_spotify_recommendations(self, playlist_data, analysis, original_track_ids, num_recommendations):
        """
        Generate Spotify recommendations - using only top tracks approach now that
        Recommendations API is no longer supported for new applications.
        """
        if not self.spotify:
            logger.error("Cannot generate Spotify recommendations: Spotify client not initialized")
            return []
        
        # Use top artists for recommendations (this is the only method that still works)
        logger.info("Getting artist top tracks for Spotify recommendations")
        top_artist_recommendations = self._get_spotify_top_tracks_by_artists(analysis, original_track_ids, num_recommendations)
        
        logger.info(f"Generated {len(top_artist_recommendations)} Spotify recommendations")
        
        # Ensure we return exactly the number requested or all available
        return top_artist_recommendations[:num_recommendations]
    
    def _get_spotify_top_tracks_by_artists(self, analysis, original_track_ids, num_recommendations):
        """
        Get top tracks from artists in the playlist.
        
        This method replaces the other recommendation methods since the Recommendations 
        and Related Artists APIs are no longer supported for new applications.
        """
        try:
            top_artists = analysis.get('top_artists', [])
            if not top_artists:
                logger.warning("No top artists found in analysis for recommendations")
                return []
            
            all_recommendations = []
            
            # Calculate how many tracks we should fetch per artist to reach target number
            num_top_artists = min(len(top_artists), 5)  # Use at most 5 artists
            tracks_per_artist = (num_recommendations + num_top_artists - 1) // num_top_artists
            tracks_per_artist = min(10, tracks_per_artist)  # Cap at 10 tracks per artist
            
            # Get artist IDs from top artists
            artist_count = 0
            for artist_name, _ in top_artists:
                if artist_count >= 5:  # Limit to top 5 artists
                    break
                    
                try:
                    logger.debug(f"Searching for artist: {artist_name}")
                    results = self.spotify.search(q=f'artist:{artist_name}', type='artist', limit=1)
                    
                    if not results or 'artists' not in results:
                        logger.warning(f"Invalid search response format for artist: {artist_name}")
                        continue
                    
                    items = results.get('artists', {}).get('items', [])
                    if not items:
                        logger.warning(f"No artist found for name: {artist_name}")
                        continue
                    
                    artist_id = items[0]['id']
                    artist_count += 1
                    logger.info(f"Found artist ID for {artist_name}: {artist_id}")
                    
                    # Get top tracks for this artist
                    try:
                        top_tracks = self.spotify.artist_top_tracks(artist_id)
                        added_count = 0
                        
                        for track in top_tracks.get('tracks', []):
                            if track.get('id') not in original_track_ids:
                                rec = self._format_spotify_recommendation(track, 'artist_top_tracks')
                                all_recommendations.append(rec)
                                added_count += 1
                                
                                # Add only the required number per artist
                                if added_count >= tracks_per_artist:
                                    break
                        
                        logger.info(f"Added {added_count} top tracks from artist {artist_name}")
                    except Exception as e:
                        logger.warning(f"Error getting top tracks for artist {artist_id}: {str(e)}")
                        
                except Exception as e:
                    logger.warning(f"Error searching for artist {artist_name}: {str(e)}")
            
            # Remove duplicates while preserving order
            unique_recommendations = []
            seen_ids = set()
            
            for rec in all_recommendations:
                if rec.get('id') and rec['id'] not in seen_ids:
                    seen_ids.add(rec['id'])
                    unique_recommendations.append(rec)
            
            # Make sure we return the exact number requested or all available
            logger.info(f"Generated {len(unique_recommendations)} recommendations from artist top tracks")
            return unique_recommendations[:num_recommendations]
            
        except Exception as e:
            logger.error(f"Error generating recommendations from top tracks: {str(e)}")
            return []
    
    def _format_spotify_recommendation(self, track, source):
        """Format a Spotify track for recommendation response."""
        return {
            'id': track.get('id', ''),
            'name': track.get('name', 'Unknown'),
            'artist': track.get('artists', [{}])[0].get('name', 'Unknown') if track.get('artists') else 'Unknown',
            'artists': [artist.get('name', 'Unknown') for artist in track.get('artists', [])],
            'album': track.get('album', {}).get('name', 'Unknown') if track.get('album') else 'Unknown',
            'popularity': track.get('popularity', 0),
            'preview_url': track.get('preview_url', ''),
            'external_url': track.get('external_urls', {}).get('spotify', ''),
            'image_url': track.get('album', {}).get('images', [{}])[0].get('url', '') if track.get('album', {}).get('images') else '',
            'platform': 'spotify',
            'source': source
        }
    
    def _get_random_track_ids(self, analysis, count=2):
        """Get random track IDs from playlist analysis."""
        # In a real implementation, you would select tracks more intelligently
        # For simplicity, we'll assume this returns a list of track IDs
        return []  # Placeholder
    
    def _get_youtube_music_recommendations(self, playlist_data, analysis, original_track_ids, num_recommendations):
        """Generate YouTube Music recommendations."""
        if not self.ytmusic:
            logger.error("Cannot generate YouTube Music recommendations: YouTube Music client not initialized")
            return []
        
        try:
            top_artists = analysis.get('top_artists', [])
            if not top_artists:
                logger.warning("No top artists found in analysis for YouTube Music recommendations")
                return []
            
            all_recommendations = []
            
            # Calculate how many artists and tracks per artist we need to reach the target
            # Use more artists for higher requested recommendation counts
            max_artists = min(len(top_artists), 10)  # Use up to 10 artists
            artists_to_use = min(max_artists, max(3, num_recommendations // 5))  # At least 3, more for higher counts
            
            # Calculate tracks per artist to approximately reach target number
            tracks_per_artist = min(10, (num_recommendations + artists_to_use - 1) // artists_to_use)
            
            logger.info(f"Using {artists_to_use} artists with {tracks_per_artist} tracks each to get {num_recommendations} recommendations")
            
            # Get recommendations based on top artists
            for artist_name, _ in top_artists[:artists_to_use]:
                try:
                    # Search for the artist
                    logger.info(f"Searching for YouTube Music artist: {artist_name}")
                    search_results = self.ytmusic.search(artist_name, filter="artists")
                    
                    if not search_results:
                        logger.warning(f"No search results found for artist: {artist_name}")
                        continue
                    
                    artist_id = search_results[0].get('browseId')
                    if not artist_id:
                        logger.warning(f"No artist ID found for: {artist_name}")
                        continue
                    
                    # Get artist info including top songs
                    logger.info(f"Getting artist data for: {artist_name} (ID: {artist_id})")
                    artist_data = self.ytmusic.get_artist(artist_id)
                    artist_songs = artist_data.get('songs', {}).get('results', [])
                    
                    logger.info(f"Found {len(artist_songs)} songs for artist {artist_name}")
                    
                    # Add songs to recommendations
                    for song in artist_songs[:tracks_per_artist]:
                        if song.get('videoId') not in original_track_ids:
                            recommendation = {
                                'id': song.get('videoId', ''),
                                'name': song.get('title', 'Unknown'),
                                'artist': artist_name,
                                'artists': [artist.get('name', 'Unknown') for artist in song.get('artists', [])],
                                'album': song.get('album', {}).get('name', 'Unknown') if song.get('album') else 'Unknown',
                                'external_url': f"https://music.youtube.com/watch?v={song.get('videoId')}" if song.get('videoId') else '',
                                'image_url': song.get('thumbnails', [{}])[-1].get('url', '') if song.get('thumbnails') else '',
                                'platform': 'youtube_music',
                                'source': 'artist_top_tracks'
                            }
                            all_recommendations.append(recommendation)
                
                except Exception as e:
                    logger.warning(f"Error getting YouTube Music recommendations for artist {artist_name}: {str(e)}")
            
            # Remove duplicates while preserving order
            unique_recommendations = []
            seen_ids = set()
            
            for rec in all_recommendations:
                if rec.get('id') and rec['id'] not in seen_ids:
                    seen_ids.add(rec['id'])
                    unique_recommendations.append(rec)
            
            # Get more recommendations if needed by searching for similar artists
            if len(unique_recommendations) < num_recommendations and len(top_artists) > artists_to_use:
                logger.info(f"Got only {len(unique_recommendations)} recommendations, trying more artists")
                
                # Try more artists
                for artist_name, _ in top_artists[artists_to_use:artists_to_use+5]:
                    if len(unique_recommendations) >= num_recommendations:
                        break
                        
                    try:
                        # Search for the artist
                        search_results = self.ytmusic.search(artist_name, filter="artists")
                        if not search_results:
                            continue
                        
                        artist_id = search_results[0].get('browseId')
                        if not artist_id:
                            continue
                        
                        # Get artist info including top songs
                        artist_data = self.ytmusic.get_artist(artist_id)
                        artist_songs = artist_data.get('songs', {}).get('results', [])
                        
                        # Add songs to recommendations
                        for song in artist_songs[:tracks_per_artist]:
                            if song.get('videoId') not in original_track_ids and song.get('videoId') not in seen_ids:
                                recommendation = {
                                    'id': song.get('videoId', ''),
                                    'name': song.get('title', 'Unknown'),
                                    'artist': artist_name,
                                    'artists': [artist.get('name', 'Unknown') for artist in song.get('artists', [])],
                                    'album': song.get('album', {}).get('name', 'Unknown') if song.get('album') else 'Unknown',
                                    'external_url': f"https://music.youtube.com/watch?v={song.get('videoId')}" if song.get('videoId') else '',
                                    'image_url': song.get('thumbnails', [{}])[-1].get('url', '') if song.get('thumbnails') else '',
                                    'platform': 'youtube_music',
                                    'source': 'artist_top_tracks'
                                }
                                unique_recommendations.append(recommendation)
                                seen_ids.add(song.get('videoId', ''))
                    except Exception:
                        continue
            
            logger.info(f"Generated {len(unique_recommendations)} unique YouTube Music recommendations")
            return unique_recommendations[:num_recommendations]
            
        except Exception as e:
            logger.error(f"Error generating YouTube Music recommendations: {str(e)}")
            return []