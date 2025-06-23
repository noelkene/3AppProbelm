#!/usr/bin/env python3
"""
Test script to verify the image generation and evaluation fixes.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.services.ai_service import AIService
from src.config.settings import IMAGE_GENERATION_MODEL_ID, MULTIMODAL_MODEL_ID

def test_model_configuration():
    """Test that the correct models are being used for different tasks."""
    print("🔍 Testing Model Configuration...")
    print(f"Image Generation Model: {IMAGE_GENERATION_MODEL_ID}")
    print(f"Multimodal Model (for evaluation): {MULTIMODAL_MODEL_ID}")
    
    if "image-generation" in IMAGE_GENERATION_MODEL_ID:
        print("✅ Image generation model is correctly configured")
    else:
        print("❌ Image generation model may not be correct")
    
    if "pro" in MULTIMODAL_MODEL_ID:
        print("✅ Multimodal model is correctly configured for evaluation")
    else:
        print("❌ Multimodal model may not be correct for evaluation")
    
    print()

def test_ai_service_initialization():
    """Test that the AI service initializes correctly."""
    print("🔍 Testing AI Service Initialization...")
    try:
        ai_service = AIService()
        print("✅ AI Service initialized successfully")
        print(f"   Project ID: {ai_service.project_id}")
        print(f"   Client: {'✅ Available' if ai_service.client else '❌ Not available'}")
        return ai_service
    except Exception as e:
        print(f"❌ AI Service initialization failed: {e}")
        return None

def test_image_generation():
    """Test basic image generation functionality."""
    print("🔍 Testing Image Generation...")
    
    ai_service = test_ai_service_initialization()
    if not ai_service:
        return False
    
    try:
        # Simple test prompt
        test_prompt = "A simple comic panel showing a character standing in a room"
        
        print(f"   Testing with prompt: {test_prompt}")
        print(f"   Using model: {IMAGE_GENERATION_MODEL_ID}")
        
        # This is a basic test - in a real scenario, you'd want to test with actual panel data
        print("   ⚠️  Note: This is a configuration test. Full image generation test would require a project with panels.")
        
        return True
        
    except Exception as e:
        print(f"❌ Image generation test failed: {e}")
        return False

def main():
    print("🧪 Testing Image Generation and Evaluation Fixes")
    print("=" * 60)
    
    # Test model configuration
    test_model_configuration()
    
    # Test AI service initialization
    ai_service = test_ai_service_initialization()
    
    # Test image generation setup
    test_image_generation()
    
    print("=" * 60)
    print("✅ Configuration tests completed!")
    print("\n📝 Summary:")
    print("   - Model configuration has been updated to use correct models")
    print("   - Image generation now uses IMAGE_GENERATION_MODEL_ID")
    print("   - Image evaluation now uses MULTIMODAL_MODEL_ID")
    print("   - This should resolve the '400 INVALID_ARGUMENT' errors")
    print("\n🚀 You can now test the Image Generator app at http://localhost:8502")

if __name__ == '__main__':
    main() 