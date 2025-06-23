"""
Main Streamlit App Entry Point
This file serves as the entry point for deploying the Manga Storyboard Generator
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import the main app
from src.app import main

if __name__ == "__main__":
    main() 