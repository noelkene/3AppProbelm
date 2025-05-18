"""Configuration settings for the Comic Generator application."""

import os
from pathlib import Path
from google.auth import default
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CHARACTERS_DIR = DATA_DIR / "characters"
BACKGROUNDS_DIR = DATA_DIR / "backgrounds"
PROJECTS_DIR = DATA_DIR / "projects"

# Get Google Cloud project from default credentials
# There are multiple ways to authenticate with Google Cloud:
# 1. Using GOOGLE_APPLICATION_CREDENTIALS environment variable pointing to a service account key file
# 2. Using gcloud auth application-default login (for development)
# 3. Using instance metadata (for running on GCP)
try:
    # Try to get credentials and project ID from default credentials
    print("Attempting to get GCP credentials from application default credentials...")
    credentials, project_id = default()
    GOOGLE_CLOUD_PROJECT = project_id
    print(f"Using GCP project ID from default credentials: {GOOGLE_CLOUD_PROJECT}")
except Exception as e:
    # Fallback to environment variable if not available
    print(f"Could not get default credentials: {e}")
    print("Falling back to environment variables...")
    GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT')
    if GOOGLE_CLOUD_PROJECT:
        print(f"Using GCP project ID from environment: {GOOGLE_CLOUD_PROJECT}")
    else:
        print("WARNING: No GCP project ID found. Please set GOOGLE_CLOUD_PROJECT in .env file")
        GOOGLE_CLOUD_PROJECT = 'your-project-id'

# Google Cloud settings
GOOGLE_CLOUD_LOCATION = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME')
if not GCS_BUCKET_NAME:
    print("WARNING: No GCS bucket name found. Please set GCS_BUCKET_NAME in .env file")
    GCS_BUCKET_NAME = 'your-bucket-name'

# Check for authentication
if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
    print(f"Using service account credentials from: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")
else:
    print("No GOOGLE_APPLICATION_CREDENTIALS environment variable found.")
    print("Using application default credentials if available.")

# AI Model settings
# Using models specified by the user
MULTIMODAL_MODEL_ID = "gemini-2.5-pro-preview-05-06"  # For image generation
TEXT_MODEL_ID = "gemini-2.5-pro-preview-05-06"  # For text generation

# Image Generation settings
DEFAULT_IMAGE_TEMPERATURE = 0.7
MIN_IMAGE_TEMPERATURE = 0.0
MAX_IMAGE_TEMPERATURE = 1.0
ADDITIONAL_INSTRUCTION_TEXT = """
Please provide detailed visual descriptions for each panel, including:
- Character positions and expressions
- Background elements and atmosphere
- Action and movement
- Lighting and mood
- Camera angle and framing
"""

# Application settings
DEFAULT_NUM_PANELS = 10
MAX_PANELS = 50
MIN_PANELS = 1
VARIANT_COUNT = 2
FINAL_VARIANT_COUNT = 1

# Create directories if they don't exist
for directory in [DATA_DIR, CHARACTERS_DIR, BACKGROUNDS_DIR, PROJECTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True) 