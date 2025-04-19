/**
 * Music Recommender - Main JavaScript
 * Handles UI interaction, API calls, and result rendering
 */

// Global state 
let currentPlatform = 'spotify';
let playlistInfo = null;
let analysisResults = null;
let recommendations = null;

// DOM elements
const platformButtons = document.querySelectorAll('.platform-btn');
const spotifyLoginBtn = document.getElementById('spotify-login');
const spotifyForm = document.getElementById('spotify-form');
const youtubeForm = document.getElementById('youtube-form');
const loadingEl = document.getElementById('loading');
const errorContainerEl = document.getElementById('error-container');
const resultsContainerEl = document.getElementById('results-container');

// Initialize event listeners
function initializeApp() {
    // Platform selection
    platformButtons.forEach(button => {
        button.addEventListener('click', handlePlatformChange);
    });
    
    // Spotify login
    spotifyLoginBtn.addEventListener('click', handleSpotifyLogin);
    
    // Form submissions
    spotifyForm.addEventListener('submit', handleFormSubmit);
    youtubeForm.addEventListener('submit', handleFormSubmit);
    
    // Check if URL has error parameter
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('error')) {
        showError(urlParams.get('error'));
        // Clear the URL parameter
        window.history.replaceState({}, document.title, '/');
    }
}

/**
 * Handle platform tab changes
 */
function handlePlatformChange(event) {
    const platform = event.currentTarget.getAttribute('data-platform');
    
    // Update active button styles
    platformButtons.forEach(btn => btn.classList.remove('active'));
    event.currentTarget.classList.add('active');
    
    // Show selected platform content
    document.querySelectorAll('.platform-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${platform}-content`).classList.add('active');
    
    // Update current platform
    currentPlatform = platform;
}

/**
 * Handle Spotify login button click
 */
function handleSpotifyLogin() {
    fetch('/login-spotify')
        .then(response => response.json())
        .then(data => {
            if (data.auth_url) {
                window.location.href = data.auth_url;
            } else if (data.error) {
                showError(data.error);
            } else {
                showError('Failed to start Spotify authentication process');
            }
        })
        .catch(error => {
            showError(`Error: ${error.message}`);
        });
}

/**
 * Handle form submissions for both platforms
 */
function handleFormSubmit(event) {
    event.preventDefault();
    
    // Get form data
    const form = event.currentTarget;
    const isSpotify = form.id === 'spotify-form';
    const platform = isSpotify ? 'spotify' : 'youtube';
    const urlInput = document.getElementById(`${platform}-url`);
    const numRecommendationsInput = document.getElementById(`${platform}-num-recommendations`);
    
    const playlistUrl = urlInput.value.trim();
    const numRecommendations = parseInt(numRecommendationsInput.value);
    
    // Validate input
    if (!playlistUrl) {
        showError('Please enter a playlist URL');
        return;
    }
    
    if (isNaN(numRecommendations) || numRecommendations < 1 || numRecommendations > 50) {
        showError('Number of recommendations must be between 1 and 50');
        return;
    }
    
    // Reset UI state
    hideError();
    hideResults();
    showLoading();
    
    // Validate playlist URL first
    validatePlaylist(playlistUrl)
        .then(validationResult => {
            if (!validationResult.valid) {
                throw new Error(validationResult.error || 'Invalid playlist URL');
            }
            
            if (!validationResult.has_enough_tracks) {
                throw new Error(`Your playlist has only ${validationResult.track_count} tracks, but at least 10 are required for good recommendations.`);
            }
            
            // If valid, get recommendations
            return getRecommendations(playlistUrl, numRecommendations);
        })
        .then(data => {
            // Hide loading and show results
            hideLoading();
            
            // Update global state
            playlistInfo = data.playlist;
            analysisResults = data.analysis;
            recommendations = data.recommendations;
            
            // Render results
            renderResults();
        })
        .catch(error => {
            hideLoading();
            showError(error.message || 'An error occurred while processing your request');
        });
}

/**
 * Validate a playlist URL
 */
function validatePlaylist(playlistUrl) {
    return fetch('/validate-playlist', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ playlist_url: playlistUrl })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || 'Failed to validate playlist');
            });
        }
        return response.json();
    });
}

/**
 * Get recommendations for a playlist
 */
function getRecommendations(playlistUrl, numRecommendations) {
    return fetch('/get-recommendations', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            playlist_url: playlistUrl,
            num_recommendations: numRecommendations
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || 'Failed to get recommendations');
            });
        }
        return response.json();
    });
}

/**
 * Show loading indicator
 */
function showLoading() {
    loadingEl.style.display = 'flex';
    // Scroll to loading indicator
    loadingEl.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Hide loading indicator
 */
function hideLoading() {
    loadingEl.style.display = 'none';
}

/**
 * Show error message
 */
function showError(message) {
    errorContainerEl.textContent = message;
    errorContainerEl.style.display = 'block';
    // Scroll to error
    errorContainerEl.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Hide error message
 */
function hideError() {
    errorContainerEl.style.display = 'none';
}

/**
 * Hide results container
 */
function hideResults() {
    resultsContainerEl.style.display = 'none';
}

/**
 * Render analysis and recommendation results
 */
function renderResults() {
    if (!playlistInfo || !analysisResults) {
        showError('No data available to display');
        return;
    }
    
    // Update playlist info
    updatePlaylistInfo();
    
    // Update analysis
    renderAnalysis();
    
    // Update recommendations
    renderRecommendations();
    
    // Show results container
    resultsContainerEl.style.display = 'block';
    
    // Scroll to results
    resultsContainerEl.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Update playlist info section
 */
function updatePlaylistInfo() {
    const playlistImageEl = document.getElementById('playlist-image');
    const playlistNameEl = document.getElementById('playlist-name');
    const playlistOwnerEl = document.getElementById('playlist-owner');
    const playlistTrackCountEl = document.getElementById('playlist-track-count');
    
    // Update playlist name
    playlistNameEl.textContent = playlistInfo.name || 'Unknown Playlist';
    
    // Update playlist owner
    playlistOwnerEl.textContent = playlistInfo.owner || 'Unknown';
    
    // Update track count
    playlistTrackCountEl.textContent = playlistInfo.track_count || 0;
    
    // Update playlist image
    if (playlistInfo.image_url) {
        playlistImageEl.innerHTML = `<img src="${playlistInfo.image_url}" alt="${playlistInfo.name}" />`;
    } else {
        playlistImageEl.innerHTML = '<i class="fas fa-music"></i>';
    }
}

/**
 * Render analysis results
 */
function renderAnalysis() {
    const playlistStatsEl = document.getElementById('playlist-stats');
    
    let platformDisplay = playlistInfo.platform;
    let platformIcon = '';
    
    if (platformDisplay === 'spotify') {
        platformDisplay = 'Spotify';
        platformIcon = '<i class="fab fa-spotify" style="color: #1DB954;"></i>';
    } else if (platformDisplay === 'youtube_music') {
        platformDisplay = 'YouTube Music';
        platformIcon = '<i class="fab fa-youtube" style="color: #FF0000;"></i>';
    } else if (platformDisplay === 'youtube') {
        platformDisplay = 'YouTube';
        platformIcon = '<i class="fab fa-youtube" style="color: #FF0000;"></i>';
    }
    
    let statsHtml = `
        <p><strong>${platformIcon} Platform:</strong> ${platformDisplay}</p>
        <p><strong><i class="fas fa-music"></i> Tracks analyzed:</strong> ${playlistInfo.track_count}</p>
    `;
    
    // Add top artists
    if (analysisResults.top_artists && analysisResults.top_artists.length > 0) {
        statsHtml += '<p><strong><i class="fas fa-user-friends"></i> Top artists in your playlist:</strong></p><ul>';
        analysisResults.top_artists.slice(0, 5).forEach(artist => {
            statsHtml += `<li>${artist[0]} (${artist[1]} ${artist[1] === 1 ? 'track' : 'tracks'})</li>`;
        });
        statsHtml += '</ul>';
    }
    
    // Add artist diversity info
    if ('artist_diversity' in analysisResults) {
        const diversityPercent = (analysisResults.artist_diversity * 100).toFixed(0);
        statsHtml += `<p><strong><i class="fas fa-random"></i> Artist Diversity:</strong> ${diversityPercent}% (${analysisResults.unique_artists} unique artists)</p>`;
    }
    
    // Add audio features for Spotify
    if (analysisResults.audio_features && analysisResults.audio_features.available) {
        const features = analysisResults.audio_features.average;
        
        statsHtml += `
            <p><strong><i class="fas fa-sliders-h"></i> Playlist Mood:</strong> ${analysisResults.audio_features.mood}</p>
            <p><strong><i class="fas fa-bolt"></i> Energy Level:</strong> ${analysisResults.audio_features.energy_level}</p>
        `;
        
        statsHtml += '<div class="characteristic-bars">';
        
        // Energy bar
        if ('energy' in features) {
            statsHtml += `
                <div class="characteristic-bar">
                    <div class="characteristic-label">
                        <span class="characteristic-name">Energy</span>
                        <span class="characteristic-value">${(features.energy * 100).toFixed(0)}%</span>
                    </div>
                    <div class="bar-container">
                        <div class="bar-fill energy" style="width: ${(features.energy * 100).toFixed(0)}%"></div>
                    </div>
                </div>
            `;
        }
        
        // Danceability bar
        if ('danceability' in features) {
            statsHtml += `
                <div class="characteristic-bar">
                    <div class="characteristic-label">
                        <span class="characteristic-name">Danceability</span>
                        <span class="characteristic-value">${(features.danceability * 100).toFixed(0)}%</span>
                    </div>
                    <div class="bar-container">
                        <div class="bar-fill danceability" style="width: ${(features.danceability * 100).toFixed(0)}%"></div>
                    </div>
                </div>
            `;
        }
        
        // Acousticness bar
        if ('acousticness' in features) {
            statsHtml += `
                <div class="characteristic-bar">
                    <div class="characteristic-label">
                        <span class="characteristic-name">Acousticness</span>
                        <span class="characteristic-value">${(features.acousticness * 100).toFixed(0)}%</span>
                    </div>
                    <div class="bar-container">
                        <div class="bar-fill acousticness" style="width: ${(features.acousticness * 100).toFixed(0)}%"></div>
                    </div>
                </div>
            `;
        }
        
        // Valence (positivity) bar
        if ('valence' in features) {
            statsHtml += `
                <div class="characteristic-bar">
                    <div class="characteristic-label">
                        <span class="characteristic-name">Positivity</span>
                        <span class="characteristic-value">${(features.valence * 100).toFixed(0)}%</span>
                    </div>
                    <div class="bar-container">
                        <div class="bar-fill valence" style="width: ${(features.valence * 100).toFixed(0)}%"></div>
                    </div>
                </div>
            `;
        }
        
        statsHtml += '</div>';
    }
    
    // Add popularity info for Spotify
    if (analysisResults.popularity && analysisResults.popularity.available) {
        statsHtml += `<p><strong><i class="fas fa-fire"></i> Mainstream Appeal:</strong> ${analysisResults.popularity.mainstream_level} (${analysisResults.popularity.average.toFixed(0)}/100)</p>`;
    }
    
    // Add general metrics
    if (analysisResults.general) {
        const durationMinutes = analysisResults.general.avg_duration_minutes.toFixed(1);
        statsHtml += `<p><strong><i class="fas fa-clock"></i> Average Song Duration:</strong> ${durationMinutes} minutes</p>`;
    }
    
    playlistStatsEl.innerHTML = statsHtml;
}

/**
 * Render recommendations
 */
function renderRecommendations() {
    const recommendationsGridEl = document.getElementById('recommendations-grid');
    
    if (!recommendations || recommendations.length === 0) {
        recommendationsGridEl.innerHTML = `
            <div class="no-recommendations">
                <i class="fas fa-exclamation-circle" style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                <h3>No recommendations found</h3>
                <p>Try a different playlist with more tracks or a variety of artists.</p>
            </div>
        `;
        return;
    }
    
    let recommendationsHtml = '';
    
    recommendations.forEach((rec, index) => {
        const platformClass = playlistInfo.platform === 'spotify' ? 'spotify-link' : 'youtube-link';
        const platformIcon = playlistInfo.platform === 'spotify' ? 
            '<i class="fab fa-spotify"></i>' : 
            '<i class="fab fa-youtube"></i>';
        
        const sourceText = getSourceText(rec.source);
        
        let imageHtml = '';
        if (rec.image_url) {
            imageHtml = `<img src="${rec.image_url}" alt="${rec.name}" />`;
        } else {
            imageHtml = '<i class="fas fa-music"></i>';
        }
        
        recommendationsHtml += `
            <div class="recommendation-card">
                <div class="recommendation-image">
                    <div class="recommendation-number">${index + 1}</div>
                    <div class="recommendation-source">${sourceText}</div>
                    ${imageHtml}
                </div>
                <div class="recommendation-content">
                    <div class="recommendation-song">${rec.name}</div>
                    <div class="recommendation-artist">${rec.artist}</div>
                    <div class="recommendation-album">${rec.album || 'Unknown Album'}</div>
                    ${rec.external_url ? 
                        `<a href="${rec.external_url}" target="_blank" class="recommendation-link ${platformClass}">
                            ${platformIcon} Listen
                        </a>` : ''}
                </div>
            </div>
        `;
    });
    
    recommendationsGridEl.innerHTML = recommendationsHtml;
}

/**
 * Get human-readable text for recommendation source
 */
function getSourceText(source) {
    switch (source) {
        case 'audio_features':
            return 'Based on sound';
        case 'artist_based':
            return 'Based on artists';
        case 'artist_top_tracks':
            return 'Top track';
        case 'related_artist':
            return 'Related artist';
        case 'track_based':
            return 'Similar track';
        default:
            return 'Recommended';
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeApp);