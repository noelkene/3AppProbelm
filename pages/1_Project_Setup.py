"""
Project Setup Page for Streamlit Cloud Deployment
"""

import streamlit as st
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import the project setup app
from src.apps.project_setup import main

# Page configuration
st.set_page_config(
    page_title="Project Setup - Comic Creation Suite",
    page_icon="📝",
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
st.markdown('<h1 class="page-header">📝 Project Setup</h1>', unsafe_allow_html=True)
st.markdown('<p class="page-description">Create new comic projects, upload source material, and define characters and backgrounds.</p>', unsafe_allow_html=True)

# Run the main project setup app
main() 