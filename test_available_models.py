#!/usr/bin/env python3
"""
Test script to check available models for image evaluation.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.services.ai_service import AIService
from google.generativeai import types

def test_available_models():
    """Test different models to see which ones support image evaluation."""
    print("🔍 Testing Available Models for Image Evaluation")
    print("=" * 60)
    
    ai_service = AIService()
    
    # List of models to test
    models_to_test = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-1.5-pro-latest",
        "gemini-2.0-flash-exp",
        "gemini-2.0-flash-preview",
        "gemini-2.0-flash-preview-image-generation",
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-2.5-pro-latest"
    ]
    
    # Create a simple test image (1x1 pixel PNG)
    test_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf5\xc7\xd4\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    
    test_prompt = "A simple test image for evaluation"
    
    for model_id in models_to_test:
        print(f"\n🧪 Testing model: {model_id}")
        try:
            # Test if model can handle multimodal input
            parts = [
                types.Part.from_text(text="Rate this image from 1-10 based on quality:"),
                types.Part.from_bytes(data=test_image_data, mime_type="image/png")
            ]
            
            content = types.Content(role="user", parts=parts)
            
            response = ai_service.client.models.generate_content(
                model=model_id,
                contents=[content],
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=100
                )
            )
            
            if response and response.text:
                print(f"✅ {model_id} - SUCCESS")
                print(f"   Response: {response.text[:100]}...")
            else:
                print(f"❌ {model_id} - No response")
                
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg:
                print(f"❌ {model_id} - Model not found (404)")
            elif "400" in error_msg and "not supported" in error_msg:
                print(f"❌ {model_id} - Model doesn't support this request type")
            elif "403" in error_msg:
                print(f"❌ {model_id} - Access forbidden (403)")
            else:
                print(f"❌ {model_id} - Error: {error_msg[:100]}...")

if __name__ == "__main__":
    test_available_models() 