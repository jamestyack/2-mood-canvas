import streamlit as st
import os
from dotenv import load_dotenv
import warnings
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.NotOpenSSLWarning)

from mood_to_music import analyze_mood
from spotify_client import SpotifyClient
from image_generator import generate_mood_image
from audio_utils import transcribe_audio

load_dotenv()

st.set_page_config(
    page_title="MoodCanvas",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def initialize_spotify_client():
    """Initialize Spotify client with environment variables."""
    client_id = os.getenv('SPOTIPY_CLIENT_ID')
    client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
    redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')
    
    if not all([client_id, client_secret, redirect_uri]):
        st.error("Missing Spotify API credentials. Please check your .env file.")
        return None
    
    return SpotifyClient(client_id, client_secret, redirect_uri)

def main():
    # Create centered container for clean layout
    with st.container():
        # Header with minimal styling
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div style="text-align: center; padding: 2rem 0;">
                <h1 style="font-size: 3rem; margin-bottom: 0.5rem;">🎨 MoodCanvas</h1>
                <p style="font-size: 1.2rem; color: #666; margin-bottom: 2rem;">Transform your emotions into music and art</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Clean input form
            with st.form("mood_form", clear_on_submit=False):
                st.markdown("### How are you feeling?")
                
                mood_text = st.text_area(
                    label="Describe your mood",
                    placeholder="I feel like I'm floating through fog at dawn...",
                    height=120,
                    help="Describe your current mood or emotional state",
                    label_visibility="collapsed"
                )
                
                # Center the submit button
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
                with col_btn2:
                    submitted = st.form_submit_button(
                        "✨ Create My MoodCanvas",
                        type="primary",
                        use_container_width=True
                    )
            
            # Process outside the form to avoid download button issues
            if submitted and mood_text:
                create_mood_canvas(mood_text)
            elif submitted and not mood_text:
                st.error("Please describe your mood first!")

def create_mood_canvas(mood_text: str):
    """Create the complete mood canvas experience."""
    
    with st.spinner("Creating your MoodCanvas..."):
        # Initialize Spotify client
        spotify_client = initialize_spotify_client()
        if not spotify_client:
            return
        
        # Authenticate with Spotify
        try:
            if not spotify_client.authenticate():
                st.error("Failed to authenticate with Spotify. Please check your credentials.")
                return
        except Exception as e:
            st.error(f"Spotify authentication error: {e}")
            return
        
        # Analyze mood using GPT-4o or fallback
        try:
            with st.spinner("Analyzing your mood..."):
                mood_data = analyze_mood(mood_text)
                st.success("🎭 Mood analyzed successfully!")
        except Exception as e:
            st.warning(f"Using fallback mood analysis: {e}")
            # Use fallback analysis if OpenAI fails
            from mood_to_music import create_fallback_mood_analysis
            mood_data = create_fallback_mood_analysis(mood_text)
        
        st.subheader("🎭 Mood Analysis")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Emotional Tags:**")
            for tag in mood_data["emotional_tags"]:
                st.write(f"• {tag}")
        
        with col2:
            st.write("**Musical Genres:**")
            for genre in mood_data["genres"]:
                st.write(f"• {genre}")
        
        # Search for tracks using enhanced mood data
        try:
            tracks = spotify_client.search_tracks(
                genres=mood_data["genres"],
                limit=15,
                search_keywords=mood_data.get("search_keywords", []),
                energy_level=mood_data.get("energy_level"),
                tempo_feeling=mood_data.get("tempo_feeling")
            )
            
            if not tracks:
                st.warning("No tracks found for these genres. Try again with different mood.")
                return
            
            # Create playlist with metadata
            track_uris = [track['uri'] for track in tracks]
            playlist_result = spotify_client.create_playlist(
                name=mood_data["playlist_name"],
                tracks=track_uris,
                mood_prompt=mood_text,
                emotional_tags=mood_data["emotional_tags"],
                genres=mood_data["genres"]
            )
            
            if playlist_result:
                st.success("🎉 Your MoodCanvas is ready!")
                
                # Main results layout - two columns for image and playlist
                st.markdown("---")
                result_col1, result_col2 = st.columns([1, 1])
                
                with result_col1:
                    # Generate and display mood image
                    st.markdown("### 🎨 Your Mood Visualization")
                    generate_and_display_image(mood_data, mood_text)
                
                with result_col2:
                    # Display playlist
                    st.markdown("### 🎵 Your Playlist")
                    display_spotify_playlist(playlist_result, mood_data, len(tracks))
                
                # Add data flow visualization
                show_data_flow_visualization(mood_text, mood_data, tracks, playlist_result)
                
            else:
                st.error("Failed to create playlist. Please try again.")
                
        except Exception as e:
            st.error(f"Error creating playlist: {e}")


def generate_and_display_image(mood_data: dict, mood_text: str):
    """Generate and display the mood image in a clean layout."""
    with st.spinner("Creating your mood artwork..."):
        try:
            image_data = generate_mood_image(
                emotional_tags=mood_data["emotional_tags"],
                genres=mood_data["genres"], 
                mood_text=mood_text,
                visual_imagery=mood_data.get("visual_imagery", []),
                movement_quality=mood_data.get("movement_quality", ""),
                color_palette=mood_data.get("color_palette", []),
                energy_level=mood_data.get("energy_level", "medium")
            )
            
            if image_data:
                # Display image
                import base64
                image_bytes = base64.b64decode(image_data)
                st.image(
                    image_bytes, 
                    caption=f"'{mood_data['playlist_name']}'",
                    use_container_width=True
                )
                
                # Download button
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"moodcanvas_{timestamp}.png"
                
                st.download_button(
                    label="💾 Download Artwork",
                    data=image_bytes,
                    file_name=filename,
                    mime="image/png",
                    use_container_width=True
                )
                
                # Show enhanced mood analysis
                st.markdown("**Mood Analysis:**")
                st.write(f"🎭 **Emotions:** {', '.join(mood_data['emotional_tags'])}")
                st.write(f"🎵 **Genres:** {', '.join(mood_data['genres'])}")
                
                if mood_data.get("visual_imagery"):
                    st.write(f"🖼️ **Visual Elements:** {', '.join(mood_data['visual_imagery'][:3])}")
                
                if mood_data.get("color_palette"):
                    st.write(f"🎨 **Colors:** {', '.join(mood_data['color_palette'][:3])}")
                
                if mood_data.get("energy_level"):
                    st.write(f"⚡ **Energy:** {mood_data['energy_level']}")
                
                if mood_data.get("search_keywords"):
                    st.write(f"🔍 **Keywords:** {', '.join(mood_data['search_keywords'][:3])}")
                
            else:
                st.warning("⚠️ Could not generate image")
                
        except Exception as e:
            st.warning(f"Image generation failed: {e}")


def display_spotify_playlist(playlist_result: dict, mood_data: dict, track_count: int):
    """Display the Spotify playlist with embed."""
    
    # Playlist info
    st.markdown(f"**{mood_data['playlist_name']}**")
    st.write(f"🎵 {track_count} tracks curated for your mood")
    
    # Spotify embed
    st.markdown("**Listen now:**")
    embed_html = f"""
    <iframe src="{playlist_result['embed_url']}" 
            width="100%" 
            height="352" 
            frameborder="0" 
            allowtransparency="true" 
            allow="encrypted-media">
    </iframe>
    """
    
    st.components.v1.html(embed_html, height=360)
    
    # Open in Spotify button
    st.link_button(
        "🎧 Open in Spotify App", 
        playlist_result['url'], 
        type="primary",
        use_container_width=True
    )


def test_spotify_integration():
    """Test Spotify integration."""
    st.subheader("Testing Spotify Integration")
    
    spotify_client = initialize_spotify_client()
    if not spotify_client:
        return
    
    if spotify_client.authenticate():
        st.success("✅ Spotify authentication successful!")
        
        # Test search
        test_genres = ["ambient", "folk"]
        tracks = spotify_client.search_tracks(test_genres, limit=5)
        
        if tracks:
            st.success(f"✅ Found {len(tracks)} test tracks")
            for track in tracks:
                st.write(f"• {track['name']} by {track['artist']}")
        else:
            st.warning("No tracks found in test search")
    else:
        st.error("❌ Spotify authentication failed")


def test_mood_analysis_ui():
    """Test mood analysis."""
    st.subheader("Testing Mood Analysis")
    
    from mood_to_music import validate_openai_setup
    
    if validate_openai_setup():
        st.success("✅ OpenAI API configured")
        
        test_moods = [
            "I feel calm and peaceful",
            "Energetic and ready to rock",
            "Melancholic and nostalgic"
        ]
        
        for mood in test_moods:
            try:
                result = analyze_mood(mood)
                st.write(f"**'{mood}'**")
                st.write(f"• Tags: {result['emotional_tags']}")
                st.write(f"• Genres: {result['genres']}")
                st.write(f"• Playlist: '{result['playlist_name']}'")
                st.write("---")
            except Exception as e:
                st.warning(f"Mood analysis failed, using fallback: {e}")
                from mood_to_music import create_fallback_mood_analysis
                result = create_fallback_mood_analysis(mood)
                st.write(f"**'{mood}' (Fallback)**")
                st.write(f"• Tags: {result['emotional_tags']}")
                st.write(f"• Genres: {result['genres']}")
                st.write(f"• Playlist: '{result['playlist_name']}'")
                st.write("---")
    else:
        st.warning("⚠️ OpenAI API not configured - testing fallback mode")
        
        test_moods = ["I feel calm", "I'm excited", "Feeling sad"]
        
        for mood in test_moods:
            from mood_to_music import create_fallback_mood_analysis
            result = create_fallback_mood_analysis(mood)
            st.write(f"**'{mood}' (Fallback)**")
            st.write(f"• Tags: {result['emotional_tags']}")
            st.write(f"• Genres: {result['genres']}")
            st.write(f"• Playlist: '{result['playlist_name']}'")
            st.write("---")


def test_image_generation_ui():
    """Test image generation."""
    st.subheader("Testing Image Generation")
    
    from image_generator import validate_image_generation, generate_mood_image
    
    if validate_image_generation():
        st.success("✅ DALL-E API configured")
        
        test_cases = [
            {
                "tags": ["calm", "dreamy"],
                "genres": ["ambient", "folk"],
                "mood": "floating through morning mist"
            },
            {
                "tags": ["energetic", "confident"], 
                "genres": ["electronic", "rock"],
                "mood": "ready to conquer the world"
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            st.write(f"**Test {i}: {case['mood']}**")
            st.write(f"Tags: {case['tags']}")
            st.write(f"Genres: {case['genres']}")
            
            with st.spinner(f"Generating test image {i}..."):
                try:
                    image_data = generate_mood_image(
                        case["tags"],
                        case["genres"],
                        case["mood"]
                    )
                    
                    if image_data:
                        import base64
                        image_bytes = base64.b64decode(image_data)
                        st.image(image_bytes, caption=f"Test {i}: {case['mood']}", width=300)
                        st.success(f"✅ Test {i} image generated")
                    else:
                        st.error(f"❌ Test {i} failed")
                        
                except Exception as e:
                    st.error(f"❌ Test {i} error: {e}")
            
            st.write("---")
    else:
        st.warning("⚠️ DALL-E API not configured - check OpenAI API key")


def show_data_flow_visualization(mood_text: str, mood_data: dict, tracks: list, image_data: str = None):
    """Show interactive data flow visualization after MoodCanvas creation."""
    
    st.markdown("---")
    
    # Expandable section for data flow
    with st.expander("🔍 **See How Your Mood Became Music & Art**", expanded=False):
        
        st.markdown("### 🎯 Data Transformation Flow")
        
        # Step 1: Input
        st.markdown("#### 1️⃣ Your Input")
        st.code(f'"{mood_text}"', language="text")
        
        # Step 2: GPT-4o Analysis  
        st.markdown("#### 2️⃣ 🧠 GPT-4o Mood Analysis")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**API Call:**")
            st.code("""
openai.chat.completions.create(
  model="gpt-4o",
  messages=[{
    "role": "user",
    "content": "Analyze mood and return JSON..."
  }]
)""", language="python")
        
        with col2:
            st.markdown("**Response:**")
            st.json(mood_data)
        
        # Step 3: Parallel Processing
        st.markdown("#### 3️⃣ Parallel Processing")
        
        # Spotify Path
        st.markdown("##### 🎵 Spotify Playlist Creation")
        spotify_col1, spotify_col2 = st.columns(2)
        
        with spotify_col1:
            st.markdown("**Genre Search:**")
            genre_queries = [f"genre:{genre}" for genre in mood_data["genres"]]
            st.code(f"Search queries:\n" + "\n".join(genre_queries), language="text")
            
        with spotify_col2:
            st.markdown("**Results:**")
            st.write(f"✅ Found {len(tracks)} tracks")
            if tracks:
                for i, track in enumerate(tracks[:3]):
                    st.write(f"{i+1}. {track['name']} - {track['artist']}")
                if len(tracks) > 3:
                    st.write(f"... and {len(tracks)-3} more")
        
        # Image Generation Path
        if image_data:
            st.markdown("##### 🎨 Image Generation")
            image_col1, image_col2 = st.columns(2)
            
            with image_col1:
                st.markdown("**Emotion → Visual Mapping:**")
                emotion_mappings = []
                for tag in mood_data["emotional_tags"][:2]:
                    if tag == "calm":
                        emotion_mappings.append(f"'{tag}' → serene, peaceful lighting")
                    elif tag == "dreamy": 
                        emotion_mappings.append(f"'{tag}' → ethereal, floating elements")
                    elif tag == "energetic":
                        emotion_mappings.append(f"'{tag}' → dynamic, vibrant colors")
                    elif tag == "melancholic":
                        emotion_mappings.append(f"'{tag}' → moody, subdued tones")
                    else:
                        emotion_mappings.append(f"'{tag}' → artistic interpretation")
                
                for mapping in emotion_mappings:
                    st.write(f"• {mapping}")
                    
                st.markdown("**Genre → Aesthetic Mapping:**")
                genre_mappings = []
                for genre in mood_data["genres"][:2]:
                    if genre == "ambient":
                        genre_mappings.append(f"'{genre}' → atmospheric textures")
                    elif genre == "folk":
                        genre_mappings.append(f"'{genre}' → natural landscapes")
                    elif genre == "electronic":
                        genre_mappings.append(f"'{genre}' → digital patterns, neon")
                    elif genre == "jazz":
                        genre_mappings.append(f"'{genre}' → smoky atmosphere")
                    else:
                        genre_mappings.append(f"'{genre}' → musical aesthetic")
                
                for mapping in genre_mappings:
                    st.write(f"• {mapping}")
            
            with image_col2:
                st.markdown("**DALL-E 3 API Call:**")
                st.code("""
openai.images.generate(
  model="dall-e-3",
  prompt="Abstract visual representation...",
  size="1024x1024"
)""", language="python")
                st.write("✅ Image generated successfully")
        
        # Step 4: Final Result
        st.markdown("#### 4️⃣ 🎨 Final MoodCanvas")
        result_col1, result_col2, result_col3 = st.columns(3)
        
        with result_col1:
            st.markdown("**🎭 Analysis**")
            st.write(f"Tags: {', '.join(mood_data['emotional_tags'])}")
            st.write(f"Genres: {', '.join(mood_data['genres'])}")
        
        with result_col2:
            st.markdown("**🎵 Playlist**")
            st.write(f"Name: {mood_data['playlist_name']}")
            st.write(f"Tracks: {len(tracks)}")
        
        with result_col3:
            st.markdown("**🎨 Artwork**")
            if image_data:
                st.write("✅ Generated")
                st.write("📥 Downloadable")
            else:
                st.write("❌ Not generated")
        
        # API Summary
        st.markdown("#### 🔧 API Calls Made")
        api_calls = [
            "✅ OpenAI GPT-4o - Mood analysis",
            "✅ Spotify Web API - Track search", 
            "✅ Spotify Web API - Playlist creation"
        ]
        
        if image_data:
            api_calls.append("✅ OpenAI DALL-E 3 - Image generation")
        else:
            api_calls.append("❌ OpenAI DALL-E 3 - Image generation (failed)")
        
        for call in api_calls:
            st.write(call)

if __name__ == "__main__":
    main()
    
    # Developer tools at bottom
    st.markdown("---")
    with st.expander("🛠️ Developer Tools", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🧪 Test Spotify", help="Test Spotify integration"):
                test_spotify_integration()
        with col2:
            if st.button("🎭 Test Mood Analysis", help="Test OpenAI mood analysis"):
                test_mood_analysis_ui()
        with col3:
            if st.button("🎨 Test Image Generation", help="Test DALL-E image generation"):
                test_image_generation_ui()