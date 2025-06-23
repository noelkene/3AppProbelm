#!/usr/bin/env python3
"""
Test the updated AI service with correct OAuth scopes.
"""

import os
import sys

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_ai_service():
    """Test the AI service initialization and basic functionality."""
    print("🧪 Testing Updated AI Service")
    print("=" * 50)
    
    try:
        from src.services.ai_service import AIService
        
        print("✅ Successfully imported AIService")
        
        # Initialize the service
        print("🔧 Initializing AI Service...")
        ai_service = AIService()
        
        print("✅ AI Service initialized successfully")
        
        # Test connection
        print("🔍 Testing connection...")
        result = ai_service.test_connection()
        
        print(f"Connection test result: {result}")
        
        if result.get('status') == 'success':
            print("🎉 AI Service is working correctly!")
            return True
        else:
            print(f"❌ Connection test failed: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing AI service: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_text_generation():
    """Test simple text generation."""
    print("\n📝 Testing Simple Text Generation")
    print("=" * 50)
    
    try:
        from src.services.ai_service import AIService
        
        ai_service = AIService()
        
        # Test with a simple prompt
        prompt = "Say hello in a friendly way"
        print(f"Testing prompt: '{prompt}'")
        
        result = ai_service.generate_text(prompt, "gemini-1.5-flash")
        
        if result and not result.startswith("Error"):
            print(f"✅ Text generation successful: {result}")
            return True
        else:
            print(f"❌ Text generation failed: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Error in text generation test: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 Testing Updated AI Service with Correct OAuth Scopes")
    print("=" * 60)
    
    # Test 1: Basic initialization
    test1_success = test_ai_service()
    
    # Test 2: Text generation
    test2_success = test_simple_text_generation()
    
    print(f"\n" + "=" * 60)
    print(f"TEST RESULTS:")
    print(f"✅ AI Service Initialization: {'PASS' if test1_success else 'FAIL'}")
    print(f"✅ Text Generation: {'PASS' if test2_success else 'FAIL'}")
    
    if test1_success and test2_success:
        print("\n🎉 All tests passed! The AI service is working correctly.")
    else:
        print("\n❌ Some tests failed. Check the error messages above.")
        print("\nNext steps:")
        print("1. Check service account permissions in Google Cloud Console")
        print("2. Enable required APIs (Vertex AI, Generative AI)")
        print("3. Verify the service account has the correct roles")

if __name__ == "__main__":
    main() 