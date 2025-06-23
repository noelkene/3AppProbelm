#!/usr/bin/env python3
"""
Simple test script for troubleshooting image generation.
This script will attempt to generate a single image with detailed logging.
"""

import os
import sys
import traceback
from typing import Optional
import base64
from io import BytesIO

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_google_auth():
    """Test Google Cloud authentication."""
    print("=== Testing Google Cloud Authentication ===")
    try:
        from google.auth import default
        credentials, project = default()
        print(f"✅ Authentication successful!")
        print(f"   Project: {project}")
        print(f"   Credentials type: {type(credentials)}")
        return True
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print(f"   Full error: {traceback.format_exc()}")
        return False

def test_imports():
    """Test if all required modules can be imported."""
    print("\n=== Testing Imports ===")
    
    try:
        from google import genai
        print("✅ google.genai imported successfully")
    except Exception as e:
        print(f"❌ Failed to import google.genai: {e}")
        return False
    
    try:
        from google.genai import types
        print("✅ google.genai.types imported successfully")
    except Exception as e:
        print(f"❌ Failed to import google.genai.types: {e}")
        return False
    
    try:
        from src.config.settings import MULTIMODAL_MODEL_ID, TEXT_MODEL_ID
        print(f"✅ Settings imported successfully")
        print(f"   MULTIMODAL_MODEL_ID: {MULTIMODAL_MODEL_ID}")
        print(f"   TEXT_MODEL_ID: {TEXT_MODEL_ID}")
    except Exception as e:
        print(f"❌ Failed to import settings: {e}")
        return False
    
    return True

def test_client_initialization():
    """Test if the GenAI client can be initialized."""
    print("\n=== Testing Client Initialization ===")
    
    try:
        from google import genai
        from google.genai import types
        from google.auth import default
        
        credentials, project = default()
        print(f"   Using project: {project}")
        
        client = genai.Client(
            credentials=credentials,
            project=project,
            location="global",
            vertexai=True
        )
        print("✅ GenAI client initialized successfully")
        return client
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        print(f"   Full error: {traceback.format_exc()}")
        return None

def test_model_availability(client):
    """Test if the models are available."""
    print("\n=== Testing Model Availability ===")
    
    try:
        from src.config.settings import MULTIMODAL_MODEL_ID, TEXT_MODEL_ID
        
        # Test multimodal model
        print(f"Testing multimodal model: {MULTIMODAL_MODEL_ID}")
        try:
            # Try to list models to see what's available
            models = client.models.list()
            available_models = [model.name for model in models]
            print(f"Available models: {available_models[:5]}...")  # Show first 5
            
            if MULTIMODAL_MODEL_ID in available_models:
                print(f"✅ Multimodal model available: {MULTIMODAL_MODEL_ID}")
            else:
                print(f"❌ Multimodal model not found in available models")
                return False
        except Exception as e:
            print(f"❌ Error checking multimodal model: {e}")
            return False
        
        # Test text model
        print(f"Testing text model: {TEXT_MODEL_ID}")
        try:
            if TEXT_MODEL_ID in available_models:
                print(f"✅ Text model available: {TEXT_MODEL_ID}")
            else:
                print(f"❌ Text model not found in available models")
                return False
        except Exception as e:
            print(f"❌ Error checking text model: {e}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error testing model availability: {e}")
        return False

def test_simple_image_generation(client):
    """Test simple image generation with a basic prompt."""
    print("\n=== Testing Simple Image Generation ===")
    
    try:
        from google.genai import types
        from src.config.settings import MULTIMODAL_MODEL_ID
        
        # Simple test prompt
        test_prompt = "A simple red circle on a white background"
        print(f"Test prompt: {test_prompt}")
        
        # Create content
        content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=test_prompt)]
        )
        
        # Configure generation
        config = types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.95,
            max_output_tokens=8192,
            response_modalities=["TEXT", "IMAGE"],
            safety_settings=[
                types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
            ]
        )
        
        print("Sending request to model...")
        response = client.models.generate_content(
            model=MULTIMODAL_MODEL_ID,
            contents=[content],
            config=config
        )
        
        print("Response received!")
        print(f"Response type: {type(response)}")
        print(f"Has candidates: {hasattr(response, 'candidates')}")
        
        if hasattr(response, 'candidates') and response.candidates:
            print(f"Number of candidates: {len(response.candidates)}")
            candidate = response.candidates[0]
            print(f"Candidate type: {type(candidate)}")
            print(f"Has content: {hasattr(candidate, 'content')}")
            
            if hasattr(candidate, 'content') and candidate.content:
                print(f"Has parts: {hasattr(candidate.content, 'parts')}")
                if hasattr(candidate.content, 'parts'):
                    print(f"Number of parts: {len(candidate.content.parts)}")
                    
                    for i, part in enumerate(candidate.content.parts):
                        print(f"Part {i+1}:")
                        print(f"  Type: {type(part)}")
                        print(f"  Has inline_data: {hasattr(part, 'inline_data')}")
                        print(f"  Has text: {hasattr(part, 'text')}")
                        
                        if hasattr(part, 'inline_data') and part.inline_data:
                            image_data = part.inline_data.data
                            if image_data is not None:
                                print(f"  ✅ Found image data: {len(image_data)} bytes")
                                # Save the image
                                with open("test_generated_image.png", "wb") as f:
                                    f.write(image_data)
                                print(f"  ✅ Image saved as test_generated_image.png")
                                return True
                        
                        if hasattr(part, 'text') and part.text:
                            print(f"  Text content: {part.text[:100]}...")
        
        print("❌ No image data found in response")
        return False
        
    except Exception as e:
        print(f"❌ Error during image generation: {e}")
        print(f"   Full error: {traceback.format_exc()}")
        return False

def test_alternative_model():
    """Test with an alternative model if the first one fails."""
    print("\n=== Testing Alternative Model ===")
    
    try:
        from google import genai
        from google.genai import types
        from google.auth import default
        
        credentials, project = default()
        client = genai.Client(
            credentials=credentials,
            project=project,
            location="global",
            vertexai=True
        )
        
        # Try a different model
        alternative_model = "gemini-1.5-pro"
        print(f"Testing alternative model: {alternative_model}")
        
        test_prompt = "A simple blue square"
        content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=test_prompt)]
        )
        
        config = types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.95,
            max_output_tokens=8192,
            response_modalities=["TEXT", "IMAGE"]
        )
        
        response = client.models.generate_content(
            model=alternative_model,
            contents=[content],
            config=config
        )
        
        if response and response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        print(f"✅ Alternative model worked! Image size: {len(part.inline_data.data)} bytes")
                        with open("test_alternative_image.png", "wb") as f:
                            f.write(part.inline_data.data)
                        print("✅ Alternative image saved as test_alternative_image.png")
                        return True
        
        print("❌ Alternative model also failed")
        return False
        
    except Exception as e:
        print(f"❌ Alternative model test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 Starting Image Generation Troubleshooting Test")
    print("=" * 60)
    
    # Test 1: Authentication
    if not test_google_auth():
        print("\n❌ Authentication failed. Please check your Google Cloud credentials.")
        return
    
    # Test 2: Imports
    if not test_imports():
        print("\n❌ Import test failed. Please check your dependencies.")
        return
    
    # Test 3: Client initialization
    client = test_client_initialization()
    if not client:
        print("\n❌ Client initialization failed.")
        return
    
    # Skip model availability test due to OAuth scope issues
    print("\n⚠️ Skipping model availability test due to OAuth scope issues")
    print("   Proceeding directly to image generation test...")
    
    # Test 4: Simple image generation
    if test_simple_image_generation(client):
        print("\n✅ SUCCESS! Image generation worked!")
        print("   Check test_generated_image.png for the result.")
    else:
        print("\n❌ Simple image generation failed.")
        
        # Test 5: Alternative model
        if test_alternative_model():
            print("\n✅ SUCCESS! Alternative model worked!")
            print("   Check test_alternative_image.png for the result.")
        else:
            print("\n❌ All image generation tests failed.")
            print("\nPossible issues:")
            print("1. Model not available in your region")
            print("2. API not enabled for your project")
            print("3. Quota exceeded")
            print("4. Authentication issues")
            print("5. Model doesn't support image generation")

if __name__ == "__main__":
    main() 