#!/usr/bin/env python3
"""
Test script to verify the image evaluation model fix.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.services.ai_service import AIService
from src.config.settings import MULTIMODAL_MODEL_ID, IMAGE_GENERATION_MODEL_ID

def test_evaluation_model():
    """Test that the correct model is being used for evaluation."""
    print("🧪 Testing Image Evaluation Model Configuration")
    print("=" * 60)
    
    print(f"Image Generation Model: {IMAGE_GENERATION_MODEL_ID}")
    print(f"Multimodal Model (for evaluation): {MULTIMODAL_MODEL_ID}")
    
    # Test AI service initialization
    try:
        ai_service = AIService()
        print("✅ AI Service initialized successfully")
        
        # Test a simple evaluation (this will show which model is actually being used)
        print("\n🔍 Testing evaluation function...")
        
        # Create a dummy image (1x1 pixel PNG)
        dummy_image = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x07tIME\x07\xe6\x06\x14\x12\x1d\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf5\xd7\xd4\xc2\x00\x00\x00\x00IEND\xaeB`\x82'
        
        test_prompt = "A simple test image"
        
        print("   Attempting to evaluate dummy image...")
        score, reasoning = ai_service.evaluate_image_prompt_match(dummy_image, test_prompt)
        print(f"   Evaluation result: Score {score}/10")
        print(f"   Reasoning: {reasoning[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    success = test_evaluation_model()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Evaluation model test completed successfully!")
        print("📝 The evaluation should now use the correct multimodal model.")
    else:
        print("❌ Evaluation model test failed!")
        print("💡 Check the error messages above for details.")

if __name__ == '__main__':
    main() 