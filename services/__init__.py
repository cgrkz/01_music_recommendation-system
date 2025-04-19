"""
Services module for the Music Recommender application.
"""
from .auth_service import SpotifyAuthManager
from .playlist_service import PlaylistService
from .analysis_service import PlaylistAnalyzer
from .recommendation_service import RecommendationService

__all__ = [
    'SpotifyAuthManager',
    'PlaylistService',
    'PlaylistAnalyzer',
    'RecommendationService',
]