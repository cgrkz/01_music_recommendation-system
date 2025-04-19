# Rhythm Radar 🎵

A modern web application that analyzes your Spotify or YouTube Music playlists and generates personalized song recommendations.



## ✨ Features

- **Multi-platform Support**: Compatible with both Spotify and YouTube Music playlists
- **Intelligent Analysis**: Analyzes playlist characteristics including top artists and musical patterns
- **Personalized Recommendations**: Suggests new tracks based on your musical preferences
- **Responsive UI**: Modern interface optimized for all devices
- **Detailed Insights**: Visual representation of your musical taste

## 📋 Requirements

- Python 3.8+
- Spotify Developer API credentials (for Spotify playlist support)
- Internet connection

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/rhythm-radar.git
   cd rhythm-radar
   ```

2. **Install required packages**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your Spotify API credentials**

   Create a `.env` file in the root directory with:
   ```
   SPOTIFY_CLIENT_ID=your_spotify_client_id
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
   SECRET_KEY=any_random_string_for_flask
   ```

   To obtain Spotify API credentials:
   - Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
   - Create a new application
   - Add `http://localhost:5000/callback` as a Redirect URI in your app settings

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the web interface**
   
   Open your browser and go to: `http://localhost:5000`

## 🎮 How to Use

1. **Choose your platform**
   - Select either Spotify or YouTube Music

2. **For Spotify playlists:**
   - For public playlists, simply paste the URL
   - For private playlists, log in with your Spotify account first

3. **For YouTube Music playlists:**
   - Paste the YouTube Music playlist URL

4. **Set the number of recommendations**
   - Choose how many song recommendations you want (1-50)

5. **Analyze and Discover**
   - View the analysis of your playlist
   - Explore your personalized recommendations
   - Click on any recommendation to listen to it on the original platform

## 🧠 How It Works

Rhythm Radar uses different strategies for each platform:

### Spotify
- Extracts playlist metadata and tracks
- Identifies top artists in your playlist
- Fetches top tracks from these artists for recommendations
- Uses artist popularity and track diversity to ensure quality suggestions

### YouTube Music
- Analyzes playlist track data
- Identifies prominent artists in your collection
- Retrieves top tracks and similar content from these artists
- Dynamically adjusts the number of sources based on your requested recommendation count

## 📁 Project Structure

```
music_recommender/
├── app.py                # Main Flask application
├── config.py             # Configuration settings
├── services/
│   ├── __init__.py
│   ├── auth_service.py   # Authentication handling
│   ├── playlist_service.py  # Playlist data fetching
│   ├── analysis_service.py  # Playlist analysis
│   ├── recommendation_service.py  # Recommendation generation
├── static/
│   ├── css/
│   ├── js/
│   └── img/
├── templates/
│   ├── index.html        # Homepage
│   └── error.html        # Error page
└── logs/                 # Log files directory
```

## ⚠️ Important Note About Spotify API

As of April 2025, Spotify has restricted access to certain API endpoints for new applications. Rhythm Radar has been updated to work within these restrictions by:

- Using artist top tracks for recommendations instead of the Recommendations API
- Skipping audio features analysis
- Focusing on direct content rather than algorithmic recommendations

These changes ensure the application continues to provide quality recommendations despite API limitations.

## 🔍 Troubleshooting

### Common Issues

1. **"Spotify API credentials not properly configured"**
   - Ensure you've created a `.env` file with valid Spotify credentials
   - Verify your Spotify Developer account is active

2. **"Cannot get recommendations from Spotify"**
   - This can happen with very niche playlists where artists have limited catalogues
   - Try a playlist with more mainstream artists

3. **"YouTube Music features disabled"**
   - Ensure you have the `ytmusicapi` package installed
   - Some YouTube Music features may be affected by regional restrictions

4. **Unable to see Playlist Image**
   - This is normal for client credentials authorization
   - For full playlist media, try logging in with your Spotify account

5. **Getting fewer recommendations than requested**
   - This can happen if there aren't enough unique tracks available
   - The application will return all unique tracks it can find

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.



