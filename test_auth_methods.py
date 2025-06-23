#!/usr/bin/env python3
"""
Test different authentication methods for Google Cloud.
"""

import os
import sys
import traceback

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_service_account_auth():
    """Test service account authentication."""
    print("=== Testing Service Account Authentication ===")
    
    try:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "C:\\Users\\hirko\\Cursor Projects\\3AppProbelm\\service_account.json"
        
        from google.auth import default
        credentials, project = default()
        
        print(f"✅ Service account auth successful!")
        print(f"   Project: {project}")
        print(f"   Credentials type: {type(credentials)}")
        return True
    except Exception as e:
        print(f"❌ Service account auth failed: {e}")
        return False

def test_application_default_auth():
    """Test application default credentials."""
    print("\n=== Testing Application Default Credentials ===")
    
    try:
        # Remove service account from environment
        if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
            del os.environ['GOOGLE_APPLICATION_CREDENTIALS']
        
        from google.auth import default
        credentials, project = default()
        
        print(f"✅ Application default auth successful!")
        print(f"   Project: {project}")
        print(f"   Credentials type: {type(credentials)}")
        return True
    except Exception as e:
        print(f"❌ Application default auth failed: {e}")
        return False

def test_manual_credentials():
    """Test with manual credential setup."""
    print("\n=== Testing Manual Credential Setup ===")
    
    try:
        from google.oauth2 import service_account
        from google import genai
        
        # Load service account manually
        credentials = service_account.Credentials.from_service_account_file(
            "C:\\Users\\hirko\\Cursor Projects\\3AppProbelm\\service_account.json",
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        
        client = genai.Client(
            credentials=credentials,
            project=credentials.project_id,
            location="global",
            vertexai=True
        )
        
        print(f"✅ Manual credential setup successful!")
        print(f"   Project: {credentials.project_id}")
        return True
    except Exception as e:
        print(f"❌ Manual credential setup failed: {e}")
        return False

def test_simple_model_call(auth_method_name, setup_func):
    """Test a simple model call with the given authentication method."""
    print(f"\n=== Testing Model Call with {auth_method_name} ===")
    
    try:
        # Setup authentication
        if not setup_func():
            return False
        
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
        
        # Try a simple text model first
        content = types.Content(
            role="user",
            parts=[types.Part.from_text(text="Say hello")]
        )
        
        config = types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=10
        )
        
        # Try with a basic model
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[content],
            config=config
        )
        
        if response and response.candidates:
            print(f"✅ {auth_method_name} - Model call successful!")
            print(f"   Response: {response.candidates[0].content.parts[0].text}")
            return True
        else:
            print(f"❌ {auth_method_name} - No response from model")
            return False
            
    except Exception as e:
        print(f"❌ {auth_method_name} - Model call failed: {e}")
        return False

def main():
    """Main test function."""
    print("🔐 Testing Google Cloud Authentication Methods")
    print("=" * 60)
    
    # Test different authentication methods
    auth_methods = [
        ("Service Account", test_service_account_auth),
        ("Application Default", test_application_default_auth),
        ("Manual Credentials", test_manual_credentials)
    ]
    
    working_methods = []
    
    for method_name, setup_func in auth_methods:
        if test_simple_model_call(method_name, setup_func):
            working_methods.append(method_name)
    
    print(f"\n" + "=" * 60)
    print(f"SUMMARY:")
    print(f"Working authentication methods: {len(working_methods)}")
    
    if working_methods:
        print("✅ Working methods:")
        for method in working_methods:
            print(f"   - {method}")
        print("\n🎉 You can use any of these methods!")
    else:
        print("❌ No authentication methods are working")
        print("\nNext steps:")
        print("1. Run: gcloud auth application-default login")
        print("2. Check service account permissions in Google Cloud Console")
        print("3. Enable required APIs (Vertex AI, Generative AI)")

if __name__ == "__main__":
    main() 