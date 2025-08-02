import openai
from typing import List, Optional
import base64
import io
import os
from dotenv import load_dotenv
import requests
from datetime import datetime

load_dotenv()


def generate_mood_image(emotional_tags: List[str], genres: List[str], mood_text: str = None, visual_imagery: List[str] = None, movement_quality: str = None, color_palette: List[str] = None, energy_level: str = None) -> Optional[str]:
    """
    Generate an AI image based on mood and genre using OpenAI's DALL-E API.
    
    Args:
        emotional_tags: List of emotional descriptors
        genres: List of musical genres
        mood_text: Original mood description for context
        
    Returns:
        Base64 encoded image data or None if failed
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("OpenAI API key not found")
        return None
    
    client = openai.OpenAI(api_key=api_key)
    
    try:
        # Create descriptive prompt for DALL-E
        prompt = create_image_prompt(
            emotional_tags, 
            genres, 
            mood_text, 
            visual_imagery, 
            movement_quality, 
            color_palette, 
            energy_level
        )
        
        print(f"Generating image with prompt: {prompt}")
        
        # Generate image using DALL-E 3
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        
        # Get the image URL
        image_url = response.data[0].url
        
        # Download and convert to base64
        image_response = requests.get(image_url)
        if image_response.status_code == 200:
            image_base64 = base64.b64encode(image_response.content).decode('utf-8')
            return image_base64
        else:
            print(f"Failed to download image: {image_response.status_code}")
            return None
            
    except Exception as e:
        print(f"Image generation error: {e}")
        return None


def create_image_prompt(emotional_tags: List[str], genres: List[str], mood_text: str = None, visual_imagery: List[str] = None, movement_quality: str = None, color_palette: List[str] = None, energy_level: str = None) -> str:
    """Create a rich, detailed prompt for DALL-E image generation using extracted mood data."""
    
    # Set defaults for optional parameters
    visual_imagery = visual_imagery or []
    color_palette = color_palette or []
    movement_quality = movement_quality or ""
    energy_level = energy_level or "medium"
    
    # Start building the prompt with specific imagery from user's text
    prompt_parts = []
    
    # 1. Core concept - use actual imagery from the user if available
    if visual_imagery:
        primary_imagery = ", ".join(visual_imagery[:3])
        if mood_text and len(mood_text) < 80:
            prompt_parts.append(f"Dynamic artwork showing {primary_imagery}, inspired by '{mood_text}'")
        else:
            prompt_parts.append(f"Dynamic artwork featuring {primary_imagery}")
    elif mood_text and len(mood_text) < 80:
        prompt_parts.append(f"Abstract visual representation of '{mood_text}'")
    else:
        emotion_str = ", ".join(emotional_tags[:3])
        prompt_parts.append(f"Abstract artwork expressing {emotion_str} emotions")
    
    # 2. Movement and energy
    energy_qualities = {
        "low": "gentle, flowing, peaceful movement",
        "medium": "steady, rhythmic, balanced energy", 
        "high": "dynamic, powerful, intense motion"
    }
    
    if energy_level in energy_qualities:
        prompt_parts.append(energy_qualities[energy_level])
    
    if movement_quality:
        prompt_parts.append(f"with {movement_quality}")
    
    # 3. Color palette - use actual extracted colors
    if color_palette:
        color_str = ", ".join(color_palette[:3])
        prompt_parts.append(f"featuring {color_str} color palette")
    else:
        # Fallback to emotion-based colors
        emotion_colors = {
            "graceful": "elegant gold and white tones",
            "triumphant": "victory gold and electric blue",
            "flowing": "fluid blues and silvers",
            "energetic": "vibrant oranges and electric colors",
            "calm": "soft blues and pearl whites",
            "confident": "bold golds and deep blues",
            "peaceful": "gentle greens and soft whites"
        }
        
        for tag in emotional_tags[:2]:
            if tag in emotion_colors:
                prompt_parts.append(emotion_colors[tag])
                break
    
    # 4. Enhanced visual style based on genre and emotion
    style_elements = []
    
    # Genre-influenced style
    genre_styles = {
        "electronic": "digital art, geometric patterns, futuristic elements",
        "pop": "vibrant, contemporary, bold graphics",
        "folk": "organic, natural textures, hand-crafted feel",
        "ambient": "atmospheric, ethereal, abstract flows",
        "rock": "dramatic, high contrast, powerful composition",
        "classical": "elegant, refined, timeless beauty"
    }
    
    for genre in genres[:2]:
        if genre in genre_styles:
            style_elements.append(genre_styles[genre])
    
    # Add emotional style
    emotion_styles = {
        "graceful": "fluid, elegant curves, refined composition",
        "triumphant": "upward movement, victory poses, heroic lighting",
        "flowing": "smooth gradients, continuous motion lines",
        "confident": "strong composition, clear focal points",
        "energetic": "dynamic angles, explosive patterns"
    }
    
    for tag in emotional_tags[:2]:
        if tag in emotion_styles:
            style_elements.append(emotion_styles[tag])
    
    if style_elements:
        prompt_parts.append(", ".join(style_elements[:2]))
    
    # 5. Technical style and quality
    prompt_parts.append("digital art, masterpiece quality, highly detailed, artistic composition, no text or words")
    
    # Combine all parts
    full_prompt = ". ".join(prompt_parts)
    
    # Ensure prompt is under DALL-E's limit
    if len(full_prompt) > 900:
        full_prompt = full_prompt[:900] + "..."
    
    return full_prompt


def save_image_locally(image_data: str, filename: str = None) -> str:
    """
    Save base64 image data to local file.
    
    Args:
        image_data: Base64 encoded image
        filename: Optional filename, auto-generated if not provided
        
    Returns:
        Filename of saved image
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"moodcanvas_{timestamp}.png"
    
    try:
        # Decode base64 to binary
        image_binary = base64.b64decode(image_data)
        
        # Save to file
        with open(filename, 'wb') as f:
            f.write(image_binary)
        
        print(f"Image saved as {filename}")
        return filename
        
    except Exception as e:
        print(f"Error saving image: {e}")
        return None


def validate_image_generation() -> bool:
    """Test if image generation is working."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key == 'sk-...':
        return False
    
    try:
        client = openai.OpenAI(api_key=api_key)
        # Simple test call
        response = client.images.generate(
            model="dall-e-3",
            prompt="A simple blue circle",
            size="1024x1024",
            n=1
        )
        return True
    except Exception as e:
        print(f"Image validation error: {e}")
        return False


def test_image_generation():
    """Test function for iterative development."""
    print("🔄 Testing image generation setup...")
    
    if not validate_image_generation():
        print("❌ Image generation not available - check OpenAI API key")
        return False
    
    print("✅ OpenAI image API configured")
    
    # Test cases
    test_cases = [
        {
            "emotional_tags": ["calm", "dreamy"],
            "genres": ["ambient", "folk"],
            "mood_text": "floating through morning mist"
        },
        {
            "emotional_tags": ["energetic", "confident"],
            "genres": ["electronic", "rock"],
            "mood_text": "ready to conquer the world"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔄 Test {i}: Generating image for {test_case['emotional_tags']} mood...")
        
        try:
            image_data = generate_mood_image(
                test_case["emotional_tags"],
                test_case["genres"],
                test_case["mood_text"]
            )
            
            if image_data:
                filename = save_image_locally(image_data, f"test_mood_{i}.png")
                print(f"   ✅ Image generated and saved as {filename}")
            else:
                print(f"   ❌ Failed to generate image")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    print("\n✅ All image generation tests passed!")
    return True


if __name__ == "__main__":
    test_image_generation()