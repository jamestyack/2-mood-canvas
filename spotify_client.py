import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import List, Dict, Optional
import random


class SpotifyClient:
    """Handle Spotify authentication and playlist operations."""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """Initialize Spotify client with OAuth."""
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = "playlist-modify-public playlist-modify-private"
        self.sp = None
        self.user_id = None
        
        # Set up OAuth
        self.auth_manager = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope,
            cache_path=".spotify_cache"
        )
    
    def authenticate(self) -> bool:
        """Authenticate with Spotify and return success status."""
        try:
            self.sp = spotipy.Spotify(auth_manager=self.auth_manager)
            user_info = self.sp.current_user()
            self.user_id = user_info['id']
            return True
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False
    
    def search_tracks(self, genres: List[str], limit: int = 20, search_keywords: List[str] = None, energy_level: str = None, tempo_feeling: str = None) -> List[Dict]:
        """Enhanced search for tracks based on genres and mood characteristics."""
        if not self.sp:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        all_tracks = []
        search_keywords = search_keywords or []
        
        # Create diverse search queries
        search_queries = []
        
        # 1. Genre-based searches
        for genre in genres:
            search_queries.append({
                'query': f"genre:{genre}",
                'weight': 0.4  # 40% genre-based
            })
        
        # 2. Keyword-enhanced searches  
        for keyword in search_keywords[:3]:  # Limit to top 3 keywords
            # Combine keyword with primary genre
            if genres:
                search_queries.append({
                    'query': f"{keyword} genre:{genres[0]}",
                    'weight': 0.3  # 30% keyword+genre
                })
            # Pure keyword search
            search_queries.append({
                'query': keyword,
                'weight': 0.2  # 20% pure keyword
            })
        
        # 3. Energy/tempo-based searches
        energy_terms = {
            'low': ['chill', 'ambient', 'calm', 'peaceful'],
            'medium': ['groovy', 'steady', 'flowing'],
            'high': ['energetic', 'powerful', 'intense', 'upbeat']
        }
        
        tempo_terms = {
            'slow': ['slow', 'downtempo', 'ballad'],
            'moderate': ['mid-tempo', 'groove'],
            'fast': ['upbeat', 'fast', 'energetic'],
            'explosive': ['intense', 'powerful', 'explosive', 'high-energy']
        }
        
        if energy_level and energy_level in energy_terms:
            for term in energy_terms[energy_level][:2]:
                search_queries.append({
                    'query': f"{term} {genres[0] if genres else ''}",
                    'weight': 0.1  # 10% energy-based
                })
        
        # Execute searches with proper distribution
        total_weight = sum(q['weight'] for q in search_queries)
        
        for query_info in search_queries:
            try:
                tracks_needed = max(1, int((query_info['weight'] / total_weight) * limit))
                
                results = self.sp.search(
                    q=query_info['query'], 
                    type='track', 
                    limit=tracks_needed, 
                    market='US'
                )
                
                for track in results['tracks']['items']:
                    track_info = {
                        'name': track['name'],
                        'artist': track['artists'][0]['name'],
                        'uri': track['uri'],
                        'preview_url': track['preview_url'],
                        'external_url': track['external_urls']['spotify'],
                        'search_source': query_info['query']  # For debugging
                    }
                    all_tracks.append(track_info)
                    
            except Exception as e:
                print(f"Error searching for '{query_info['query']}': {e}")
                continue
        
        # Remove duplicates (same track URI)
        seen_uris = set()
        unique_tracks = []
        for track in all_tracks:
            if track['uri'] not in seen_uris:
                seen_uris.add(track['uri'])
                unique_tracks.append(track)
        
        # Shuffle and return requested number of tracks
        random.shuffle(unique_tracks)
        return unique_tracks[:limit]
    
    def create_playlist(self, name: str, tracks: List[str], mood_prompt: str = None, emotional_tags: List[str] = None, genres: List[str] = None) -> Optional[str]:
        """
        Create a playlist and add tracks.
        
        Args:
            name: Playlist name
            tracks: List of track URIs
            mood_prompt: Original mood description from user
            emotional_tags: Analyzed emotional tags
            genres: Music genres used
            
        Returns:
            Dict with playlist URL and ID for embedding, or None if failed
        """
        if not self.sp or not self.user_id:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        try:
            # Create rich playlist description
            description_parts = ["Generated by MoodCanvas 🎨"]
            
            if mood_prompt:
                description_parts.append(f"Mood: \"{mood_prompt}\"")
            
            if emotional_tags:
                description_parts.append(f"Emotions: {', '.join(emotional_tags)}")
            
            if genres:
                description_parts.append(f"Genres: {', '.join(genres)}")
            
            description = " | ".join(description_parts)
            
            # Create playlist
            playlist = self.sp.user_playlist_create(
                user=self.user_id,
                name=name,
                public=True,
                description=description
            )
            
            playlist_id = playlist['id']
            
            # Add tracks to playlist
            if tracks:
                self.sp.playlist_add_items(playlist_id, tracks)
            
            return {
                'url': playlist['external_urls']['spotify'],
                'id': playlist_id,
                'embed_url': f"https://open.spotify.com/embed/playlist/{playlist_id}"
            }
            
        except Exception as e:
            print(f"Error creating playlist: {e}")
            return None
    
    def get_auth_url(self) -> str:
        """Get the authorization URL for manual auth flow."""
        return self.auth_manager.get_authorize_url()


def test_spotify_client():
    """Test function for iterative development."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    client_id = os.getenv('SPOTIPY_CLIENT_ID')
    client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
    redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')
    
    if not all([client_id, client_secret, redirect_uri]):
        print("❌ Missing Spotify credentials in .env file")
        return False
    
    client = SpotifyClient(client_id, client_secret, redirect_uri)
    
    print("🔄 Testing authentication...")
    if not client.authenticate():
        print("❌ Authentication failed")
        return False
    
    print("✅ Authentication successful!")
    
    print("🔄 Testing track search...")
    test_genres = ["ambient", "folk"]
    tracks = client.search_tracks(test_genres, limit=10)
    
    if not tracks:
        print("❌ No tracks found")
        return False
    
    print(f"✅ Found {len(tracks)} tracks")
    for i, track in enumerate(tracks[:3]):
        print(f"  {i+1}. {track['name']} by {track['artist']}")
    
    print("🔄 Testing playlist creation...")
    track_uris = [track['uri'] for track in tracks[:5]]
    playlist_result = client.create_playlist(
        name="MoodCanvas Test",
        tracks=track_uris,
        mood_prompt="Testing the new metadata feature",
        emotional_tags=["calm", "test"],
        genres=test_genres
    )
    
    if playlist_result:
        print(f"✅ Playlist created: {playlist_result['url']}")
        print(f"   Embed URL: {playlist_result['embed_url']}")
        return True
    else:
        print("❌ Playlist creation failed")
        return False


if __name__ == "__main__":
    test_spotify_client()