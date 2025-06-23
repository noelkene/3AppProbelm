#!/usr/bin/env python3
"""
Debug script to test the image scoring system.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.ai_service import AIService
from src.config.settings import USE_HEURISTIC_EVALUATION, EVALUATION_FALLBACK
import io
from PIL import Image
import numpy as np

def create_test_image(width=512, height=512):
    """Create a simple test image for debugging."""
    # Create a simple gradient image
    img_array = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Create a gradient
    for y in range(height):
        for x in range(width):
            img_array[y, x] = [
                int(255 * x / width),  # Red gradient
                int(255 * y / height), # Green gradient
                128  # Fixed blue
            ]
    
    # Convert to PIL Image
    img = Image.fromarray(img_array)
    
    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    return img_bytes.getvalue()

def test_scoring():
    """Test the scoring system with a simple image."""
    print("=== Testing Image Scoring System ===")
    
    # Create AI service
    ai_service = AIService()
    
    # Create test image
    test_image = create_test_image(512, 512)
    print(f"Created test image: {len(test_image)} bytes")
    
    # Test prompt
    test_prompt = "A comic panel showing a character in action with detailed background"
    
    print(f"\nSettings:")
    print(f"USE_HEURISTIC_EVALUATION: {USE_HEURISTIC_EVALUATION}")
    print(f"EVALUATION_FALLBACK: {EVALUATION_FALLBACK}")
    
    # Test image analysis
    print(f"\n=== Testing Image Analysis ===")
    try:
        analysis = ai_service.analyze_image_composition(test_image)
        print(f"Image analysis: {analysis}")
    except Exception as e:
        print(f"Error in image analysis: {e}")
        return
    
    # Test heuristic evaluation
    print(f"\n=== Testing Heuristic Evaluation ===")
    try:
        score, reasoning = ai_service._evaluate_image_heuristic(test_image, test_prompt, 10)
        print(f"Heuristic score: {score}/10")
        print(f"Heuristic reasoning: {reasoning}")
    except Exception as e:
        print(f"Error in heuristic evaluation: {e}")
        import traceback
        traceback.print_exc()
    
    # Test main evaluation function
    print(f"\n=== Testing Main Evaluation Function ===")
    try:
        score, reasoning = ai_service.evaluate_image_prompt_match(test_image, test_prompt, 10)
        print(f"Main evaluation score: {score}/10")
        print(f"Main evaluation reasoning: {reasoning}")
    except Exception as e:
        print(f"Error in main evaluation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scoring() 