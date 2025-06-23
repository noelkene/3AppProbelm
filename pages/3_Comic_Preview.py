"""
Comic Preview Page for Streamlit Cloud Deployment
"""

import streamlit as st
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import the comic preview app
from src.apps.comic_preview import main

# Page configuration
st.set_page_config(
    page_title="Comic Preview - Comic Creation Suite",
    page_icon="📖",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .page-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .page-description {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Page header
st.markdown('<h1 class="page-header">📖 Comic Preview</h1>', unsafe_allow_html=True)
st.markdown('<p class="page-description">View, edit, and manage your complete comic project with all panels.</p>', unsafe_allow_html=True)

# Run the main comic preview app
main() 