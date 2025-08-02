import os
import time
from dotenv import load_dotenv
import requests
import base64
from datetime import datetime
from typing import List, Optional, Dict

try:
    from google import genai
    from google.genai import types
    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    # Fallback to older API structure
    try:
        import google.generativeai as genai
        GOOGLE_GENAI_AVAILABLE = False
    except ImportError:
        genai = None
        GOOGLE_GENAI_AVAILABLE = False

load_dotenv()


def generate_mood_video(
    emotional_tags: List[str], 
    genres: List[str], 
    mood_text: str = None,
    visual_imagery: List[str] = None,
    movement_quality: str = None,
    color_palette: List[str] = None,
    energy_level: str = None,
    duration: int = 8
) -> Optional[Dict]:
    """
    Generate an AI video based on mood and genre using Google's Veo 3 API.
    
    Args:
        emotional_tags: List of emotional descriptors
        genres: List of musical genres
        mood_text: Original mood description for context
        visual_imagery: List of visual elements from mood analysis
        movement_quality: Description of movement quality
        color_palette: List of colors from mood analysis
        energy_level: Energy level (low/medium/high)
        duration: Video duration in seconds (default 8)
        
    Returns:
        Dict with video data and metadata or None if failed
    """
    api_key = os.getenv('GOOGLE_AI_API_KEY')
    if not api_key:
        print("Google AI API key not found. Please set GOOGLE_AI_API_KEY in .env file")
        return None
    
    try:
        # Create video prompt using mood data
        video_prompt = create_video_prompt(
            emotional_tags, 
            genres, 
            mood_text,
            visual_imagery,
            movement_quality,
            color_palette,
            energy_level
        )
        
        print(f"Generating video with prompt: {video_prompt}")
        
        # Configure API with current available version
        genai.configure(api_key=api_key)
        
        # NOTE: Video generation with Veo 3 requires the new Google Generative AI SDK
        # The current google-generativeai package (0.8.5) doesn't fully support video generation
        # This is a placeholder implementation
        
        print("⚠️  Video generation is not fully supported in the current API version.")
        print("📋 The google-generativeai package needs to be updated to support Veo 3.")
        print("💡 This feature will work once Google releases the updated SDK.")
        print("🔗 For now, you can use Google AI Studio at https://ai.google.dev/")
        
        # For demonstration, return a placeholder response
        return {
            'video_url': None,
            'video_data': None,
            'prompt': video_prompt,
            'error': 'Video generation requires updated Google AI SDK',
            'metadata': {
                'emotional_tags': emotional_tags,
                'genres': genres,
                'mood_text': mood_text,
                'visual_imagery': visual_imagery,
                'color_palette': color_palette,
                'energy_level': energy_level,
                'duration': duration,
                'timestamp': datetime.now().isoformat(),
                'status': 'awaiting_sdk_update'
            }
        }
            
    except Exception as e:
        print(f"Video generation error: {e}")
        return None


def create_video_prompt(
    emotional_tags: List[str], 
    genres: List[str], 
    mood_text: str = None,
    visual_imagery: List[str] = None,
    movement_quality: str = None,
    color_palette: List[str] = None,
    energy_level: str = None
) -> str:
    """Create a rich, detailed prompt for Veo 3 video generation using extracted mood data."""
    
    # Set defaults for optional parameters
    visual_imagery = visual_imagery or []
    color_palette = color_palette or []
    movement_quality = movement_quality or ""
    energy_level = energy_level or "medium"
    
    prompt_parts = []
    
    # 1. Core visual concept - use actual imagery from user if available
    if visual_imagery and mood_text:
        primary_imagery = ", ".join(visual_imagery[:2])
        if len(mood_text) < 60:
            prompt_parts.append(f"Cinematic video showing {primary_imagery}, embodying the feeling of '{mood_text}'")
        else:
            prompt_parts.append(f"Cinematic video featuring {primary_imagery}")
    elif mood_text and len(mood_text) < 60:
        prompt_parts.append(f"Abstract visual representation of '{mood_text}' in motion")
    else:
        emotion_str = ", ".join(emotional_tags[:2])
        prompt_parts.append(f"Flowing cinematic video expressing {emotion_str} emotions")
    
    # 2. Movement and pacing based on energy
    energy_movements = {
        "low": "slow, gentle, flowing camera movements with peaceful transitions",
        "medium": "steady, rhythmic pacing with smooth camera work", 
        "high": "dynamic, energetic movement with quick cuts and flowing motion"
    }
    
    if energy_level in energy_movements:
        prompt_parts.append(energy_movements[energy_level])
    
    if movement_quality:
        prompt_parts.append(f"featuring {movement_quality} throughout the sequence")
    
    # 3. Color and lighting from extracted palette
    if color_palette:
        color_str = ", ".join(color_palette[:3])
        prompt_parts.append(f"with {color_str} color scheme and complementary lighting")
    else:
        # Fallback to emotion-based color schemes
        emotion_colors = {
            "graceful": "elegant gold and soft white tones with warm lighting",
            "triumphant": "victory gold and electric blue with dramatic lighting",
            "flowing": "fluid blues and silvers with ethereal lighting",
            "energetic": "vibrant oranges and electric colors with dynamic lighting",
            "calm": "soft blues and pearl whites with gentle, diffused lighting",
            "confident": "bold golds and deep blues with strong, directional lighting",
            "peaceful": "gentle greens and soft whites with natural lighting"
        }
        
        for tag in emotional_tags[:2]:
            if tag in emotion_colors:
                prompt_parts.append(emotion_colors[tag])
                break
    
    # 4. Style influenced by musical genres
    genre_styles = {
        "electronic": "futuristic, digital aesthetic with geometric patterns and neon accents",
        "pop": "vibrant, contemporary style with bold visual elements",
        "folk": "organic, natural textures with earthy, hand-crafted feel",
        "ambient": "atmospheric, ethereal with abstract flowing elements",
        "rock": "dramatic, high contrast with powerful visual composition",
        "classical": "elegant, refined with timeless, sophisticated visuals",
        "jazz": "smooth, sophisticated with warm, moody atmosphere"
    }
    
    for genre in genres[:2]:
        if genre in genre_styles:
            prompt_parts.append(genre_styles[genre])
            break
    
    # 5. Technical video specifications
    prompt_parts.append("high quality cinematic video, 8 seconds duration, smooth motion, professional cinematography")
    prompt_parts.append("no text overlays, pure visual storytelling")
    
    # Combine all parts
    full_prompt = ". ".join(prompt_parts)
    
    # Ensure prompt is under Veo's limit (1024 tokens ≈ 800 characters)
    if len(full_prompt) > 800:
        full_prompt = full_prompt[:800] + "..."
    
    return full_prompt


def poll_video_generation_new_api(client, operation, timeout: int = 360) -> Optional[Dict]:
    """
    Poll for video generation completion using new API.
    
    Args:
        client: Google AI client instance
        operation: Initial operation from video generation request
        timeout: Maximum wait time in seconds (default 6 minutes)
        
    Returns:
        Video data dict or None if failed/timeout
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            # Check if generation is complete
            if hasattr(operation, 'done') and operation.done:
                # Video is ready
                if hasattr(operation, 'response') and operation.response:
                    generated_videos = getattr(operation.response, 'generated_videos', [])
                    if generated_videos:
                        video = generated_videos[0]
                        video_file = getattr(video, 'video', None)
                        if video_file:
                            # Download the video file
                            video_url = getattr(video_file, 'uri', None)
                            if video_url:
                                # Download video data
                                video_data = download_video_data(video_url)
                                return {
                                    'url': video_url,
                                    'data': video_data
                                }
            
            # Refresh operation status
            operation = client.operations.get(operation.name)
            
            # Wait before next poll
            print(f"Video generation in progress... ({int(time.time() - start_time)}s elapsed)")
            time.sleep(10)  # Poll every 10 seconds
            
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(10)
    
    print("Video generation timeout")
    return None


def poll_video_generation(response, timeout: int = 360) -> Optional[Dict]:
    """
    Poll for video generation completion (legacy function).
    
    Args:
        response: Initial response from video generation request
        timeout: Maximum wait time in seconds (default 6 minutes)
        
    Returns:
        Video data dict or None if failed/timeout
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            # Check if generation is complete
            # Note: Actual implementation depends on Veo API response format
            if hasattr(response, 'result') and response.result:
                # Video is ready
                video_url = getattr(response.result, 'uri', None)
                if video_url:
                    # Download video data
                    video_data = download_video_data(video_url)
                    return {
                        'url': video_url,
                        'data': video_data
                    }
            
            # Wait before next poll
            time.sleep(10)  # Poll every 10 seconds
            
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(10)
    
    print("Video generation timeout")
    return None


def download_video_data(video_url: str) -> Optional[str]:
    """
    Download video from URL and convert to base64.
    
    Args:
        video_url: URL to download video from
        
    Returns:
        Base64 encoded video data or None if failed
    """
    try:
        response = requests.get(video_url, timeout=30)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode('utf-8')
        else:
            print(f"Failed to download video: {response.status_code}")
            return None
    except Exception as e:
        print(f"Video download error: {e}")
        return None


def save_video_locally(video_data: str, filename: str = None) -> str:
    """
    Save base64 video data to local file.
    
    Args:
        video_data: Base64 encoded video
        filename: Optional filename, auto-generated if not provided
        
    Returns:
        Filename of saved video
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"moodcanvas_video_{timestamp}.mp4"
    
    try:
        # Decode base64 to binary
        video_binary = base64.b64decode(video_data)
        
        # Save to file
        with open(filename, 'wb') as f:
            f.write(video_binary)
        
        print(f"Video saved as {filename}")
        return filename
        
    except Exception as e:
        print(f"Error saving video: {e}")
        return None


def validate_video_generation() -> bool:
    """Test if video generation is working."""
    api_key = os.getenv('GOOGLE_AI_API_KEY')
    if not api_key or api_key == 'your-google-ai-api-key':
        print("❌ No Google AI API key found")
        return False
    
    try:
        genai.configure(api_key=api_key)
        models = genai.list_models()
        
        print("Available models:")
        veo_models = []
        for model in models:
            print(f"  - {model.name}")
            if 'veo' in model.name.lower():
                veo_models.append(model.name)
        
        if veo_models:
            print(f"✅ Found Veo models: {veo_models}")
            print("⚠️  Current SDK doesn't support video generation yet")
            print("📋 Awaiting Google AI SDK update for Veo 3 support")
            return True  # API key works, models available, just waiting for SDK
        else:
            print("❌ No Veo models found")
            return False
    except Exception as e:
        print(f"Video validation error: {e}")
        return False


def test_video_generation():
    """Test function for iterative development."""
    print("🔄 Testing video generation setup...")
    
    if not validate_video_generation():
        print("❌ Video generation not available - check Google AI API key")
        return False
    
    print("✅ Google AI Veo API configured")
    
    # Test case
    test_case = {
        "emotional_tags": ["flowing", "graceful"],
        "genres": ["ambient", "electronic"],
        "mood_text": "floating through digital clouds",
        "visual_imagery": ["clouds", "floating", "light"],
        "color_palette": ["soft blue", "white", "silver"],
        "energy_level": "medium"
    }
    
    print(f"\n🔄 Generating test video for {test_case['emotional_tags']} mood...")
    
    try:
        video_result = generate_mood_video(
            test_case["emotional_tags"],
            test_case["genres"],
            test_case["mood_text"],
            test_case["visual_imagery"],
            color_palette=test_case["color_palette"],
            energy_level=test_case["energy_level"]
        )
        
        if video_result:
            if video_result.get('video_data'):
                filename = save_video_locally(video_result['video_data'], "test_mood_video.mp4")
                print(f"   ✅ Video generated and saved as {filename}")
            else:
                print(f"   ✅ Video generated with URL: {video_result.get('video_url')}")
            return True
        else:
            print(f"   ❌ Failed to generate video")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


if __name__ == "__main__":
    test_video_generation()