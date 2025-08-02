import openai
from typing import Dict, List, Optional
import json
import os
from dotenv import load_dotenv

load_dotenv()


def analyze_mood(mood_text: str) -> Dict:
    """
    Analyze mood text using GPT-4o and return structured mood data.
    
    Args:
        mood_text: User's mood description
        
    Returns:
        Dict with emotional_tags, genres, and playlist_name
    """
    if not mood_text or not mood_text.strip():
        raise ValueError("Mood text cannot be empty")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OpenAI API key not found in environment variables")
    
    client = openai.OpenAI(api_key=api_key)
    
    prompt = create_mood_analysis_prompt(mood_text)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a mood-to-music assistant. Always respond with valid JSON only, no other text."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_tokens=200,
            temperature=0.7
        )
        
        response_text = response.choices[0].message.content.strip()
        return extract_mood_components(response_text)
        
    except Exception as e:
        print(f"OpenAI API error: {e}")
        # Fallback to basic analysis
        return create_fallback_mood_analysis(mood_text)


def create_mood_analysis_prompt(mood_text: str) -> str:
    """Create the enhanced GPT-4o prompt for rich mood analysis."""
    return f"""
Analyze this mood description and extract rich, colorful details to create a vivid musical and visual experience:

Mood: "{mood_text}"

Return JSON in this exact format:
{{
  "emotional_tags": ["tag1", "tag2", "tag3"],
  "genres": ["genre1", "genre2"],
  "playlist_name": "Creative playlist name",
  "energy_level": "low/medium/high",
  "tempo_feeling": "slow/moderate/fast/explosive",
  "visual_imagery": ["image1", "image2", "image3"],
  "movement_quality": "quality description",
  "color_palette": ["color1", "color2", "color3"],
  "search_keywords": ["keyword1", "keyword2", "keyword3"]
}}

Extraction Guidelines:
- emotional_tags: Nuanced emotions, not just basic ones (e.g., "triumphant", "graceful", "soaring")
- genres: Match energy and style (electronic for high energy, classical for elegance, etc.)
- energy_level: Physical/emotional intensity 
- tempo_feeling: Musical pace that matches the mood
- visual_imagery: Concrete images from the text (e.g., "running", "finish line", "wings")
- movement_quality: How the person moves/feels (e.g., "fluid motion", "explosive power")
- color_palette: Colors that match the emotional tone (e.g., "gold", "electric blue", "sunset orange")
- search_keywords: Extra music search terms beyond genres (e.g., "victory", "motivation", "flow")
- playlist_name: Poetic name incorporating key imagery (15-30 characters)

Examples:
Input: "I feel like I'm floating through fog at dawn"
Output: {{"emotional_tags": ["ethereal", "peaceful", "emerging"], "genres": ["ambient", "folk"], "playlist_name": "Dawn Mist Floating", "energy_level": "low", "tempo_feeling": "slow", "visual_imagery": ["mist", "dawn light", "floating"], "movement_quality": "weightless drifting", "color_palette": ["pearl gray", "soft gold", "misty white"], "search_keywords": ["ethereal", "atmospheric", "morning"]}}

Input: "Energized and ready to conquer the world"
Output: {{"emotional_tags": ["triumphant", "powerful", "unstoppable"], "genres": ["electronic", "rock"], "playlist_name": "World Conqueror Rising", "energy_level": "high", "tempo_feeling": "explosive", "visual_imagery": ["summit", "rising sun", "victory"], "movement_quality": "surging forward", "color_palette": ["electric blue", "gold", "crimson"], "search_keywords": ["victory", "power", "motivation"]}}

Input: "I feel gracefully running with strong momentum to the finish line light on my toes, confident and winning"
Output: {{"emotional_tags": ["graceful", "triumphant", "flowing"], "genres": ["electronic", "pop"], "playlist_name": "Graceful Victory Sprint", "energy_level": "high", "tempo_feeling": "fast", "visual_imagery": ["finish line", "running", "light steps"], "movement_quality": "graceful power", "color_palette": ["electric gold", "victory blue", "bright white"], "search_keywords": ["running", "victory", "momentum", "grace"]}}

Respond with ONLY the JSON, no other text.
"""


def extract_mood_components(mood_response: str) -> Dict:
    """Extract and validate mood components from GPT response."""
    try:
        # Clean the response - remove any markdown formatting
        cleaned_response = mood_response.strip()
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()
        
        # Parse JSON
        mood_data = json.loads(cleaned_response)
        
        # Validate required fields
        required_fields = ['emotional_tags', 'genres', 'playlist_name']
        for field in required_fields:
            if field not in mood_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate data types and content
        if not isinstance(mood_data['emotional_tags'], list) or len(mood_data['emotional_tags']) == 0:
            raise ValueError("emotional_tags must be a non-empty list")
        
        if not isinstance(mood_data['genres'], list) or len(mood_data['genres']) == 0:
            raise ValueError("genres must be a non-empty list")
        
        if not isinstance(mood_data['playlist_name'], str) or not mood_data['playlist_name'].strip():
            raise ValueError("playlist_name must be a non-empty string")
        
        # Clean and limit core data
        mood_data['emotional_tags'] = [tag.strip().lower() for tag in mood_data['emotional_tags'][:3]]
        mood_data['genres'] = [genre.strip().lower() for genre in mood_data['genres'][:3]]
        mood_data['playlist_name'] = mood_data['playlist_name'].strip()[:50]
        
        # Handle optional enhanced fields with defaults
        mood_data['energy_level'] = mood_data.get('energy_level', 'medium').lower()
        mood_data['tempo_feeling'] = mood_data.get('tempo_feeling', 'moderate').lower()
        mood_data['visual_imagery'] = mood_data.get('visual_imagery', [])[:5]
        mood_data['movement_quality'] = mood_data.get('movement_quality', '').strip()[:100]
        mood_data['color_palette'] = mood_data.get('color_palette', [])[:3]
        mood_data['search_keywords'] = mood_data.get('search_keywords', [])[:5]
        
        return mood_data
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Response was: {mood_response}")
        raise ValueError("Invalid JSON response from OpenAI")
    except Exception as e:
        print(f"Mood extraction error: {e}")
        raise


def create_fallback_mood_analysis(mood_text: str) -> Dict:
    """Create a basic mood analysis when OpenAI fails."""
    mood_lower = mood_text.lower()
    
    # Simple keyword-based fallback
    if any(word in mood_lower for word in ['calm', 'peaceful', 'relaxed', 'serene']):
        return {
            "emotional_tags": ["calm", "peaceful"],
            "genres": ["ambient", "folk"],
            "playlist_name": "Peaceful Moments"
        }
    elif any(word in mood_lower for word in ['happy', 'excited', 'energetic', 'pumped']):
        return {
            "emotional_tags": ["happy", "energetic"],
            "genres": ["pop", "electronic"],
            "playlist_name": "Energy Boost"
        }
    elif any(word in mood_lower for word in ['sad', 'melancholy', 'down', 'blue']):
        return {
            "emotional_tags": ["melancholic", "reflective"],
            "genres": ["folk", "indie"],
            "playlist_name": "Reflection Time"
        }
    else:
        return {
            "emotional_tags": ["contemplative", "mixed"],
            "genres": ["indie", "alternative"],
            "playlist_name": "Mixed Feelings"
        }


def validate_openai_setup() -> bool:
    """Check if OpenAI is properly configured."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key == 'sk-...':
        return False
    
    try:
        client = openai.OpenAI(api_key=api_key)
        # Test with a simple call
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        return True
    except Exception as e:
        print(f"OpenAI validation error: {e}")
        return False


def test_mood_analysis():
    """Test function for iterative development."""
    test_cases = [
        "I feel like I'm floating through fog at dawn",
        "Energized and ready to conquer the world", 
        "Feeling melancholic and nostalgic",
        "Chill and relaxed after a long day",
        "Anxious but hopeful about the future"
    ]
    
    print("🔄 Testing OpenAI setup...")
    if not validate_openai_setup():
        print("❌ OpenAI API key not configured or invalid")
        return False
    
    print("✅ OpenAI API configured")
    
    print("\n🔄 Testing mood analysis...")
    for i, test_mood in enumerate(test_cases, 1):
        try:
            print(f"\n{i}. Testing: '{test_mood}'")
            result = analyze_mood(test_mood)
            print(f"   ✅ Tags: {result['emotional_tags']}")
            print(f"   ✅ Genres: {result['genres']}")
            print(f"   ✅ Playlist: '{result['playlist_name']}'")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    print("\n✅ All mood analysis tests passed!")
    return True


if __name__ == "__main__":
    test_mood_analysis()