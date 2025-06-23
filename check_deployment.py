#!/usr/bin/env python3
"""
Simple deployment status checker for the three Streamlit applications.
"""

import requests
import time
import sys

def check_app_status(port, app_name):
    """Check if an application is running on the specified port."""
    try:
        url = f"http://localhost:{port}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {app_name} is running on port {port}")
            return True
        else:
            print(f"⚠️  {app_name} responded with status {response.status_code} on port {port}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ {app_name} is not running on port {port}")
        return False
    except requests.exceptions.Timeout:
        print(f"⏰ {app_name} timed out on port {port}")
        return False
    except Exception as e:
        print(f"❌ Error checking {app_name} on port {port}: {e}")
        return False

def main():
    apps = [
        (8501, "Project Setup"),
        (8502, "Image Generator"),
        (8503, "Comic Preview")
    ]
    
    print("🔍 Checking deployment status...")
    print("=" * 50)
    
    all_running = True
    for port, app_name in apps:
        if not check_app_status(port, app_name):
            all_running = False
    
    print("=" * 50)
    if all_running:
        print("🎉 All applications are running successfully!")
        print("\n📱 Access your applications at:")
        for port, app_name in apps:
            print(f"   - {app_name}: http://localhost:{port}")
    else:
        print("❌ Some applications are not running.")
        print("💡 Try running the deployment script again.")
        sys.exit(1)

if __name__ == "__main__":
    main() 