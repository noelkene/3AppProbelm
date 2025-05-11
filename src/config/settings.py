"""Configuration settings for the Manga Storyboard Generator."""

import os
from pathlib import Path
from google.auth import default

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CHARACTERS_DIR = DATA_DIR / "characters"
BACKGROUNDS_DIR = DATA_DIR / "backgrounds"
PROJECTS_DIR = DATA_DIR / "projects"

# Get Google Cloud project from default credentials
try:
    _, GOOGLE_CLOUD_PROJECT = default()
except Exception:
    # Fallback to hardcoded project ID if credentials not available
    GOOGLE_CLOUD_PROJECT = "platinum-banner-303105"

# Google Cloud settings
GOOGLE_CLOUD_LOCATION = "us-central1"
GCS_BUCKET_NAME = "comic_book_heros_and_villans"

# AI Model settings
MULTIMODAL_MODEL_ID = "gemini-2.0-flash-preview-image-generation"
TEXT_MODEL_ID = "gemini-2.5-pro-preview-05-06"

# Application settings
DEFAULT_NUM_PANELS = 10
MAX_PANELS = 40
MIN_PANELS = 5
VARIANT_COUNT = 4  # Number of variants to generate per panel
FINAL_VARIANT_COUNT = 4  # Number of final variants to generate from best variant

# Create directories if they don't exist
for directory in [DATA_DIR, CHARACTERS_DIR, BACKGROUNDS_DIR, PROJECTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True) 