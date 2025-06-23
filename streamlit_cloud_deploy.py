"""
Streamlit Cloud Deployment - Multi-Page Comic App
This file combines all three apps into a single Streamlit application with pages.
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import the main app modules
from src.apps.project_setup import main as project_setup_main
from src.apps.image_generator import main as image_generator_main
from src.apps.comic_preview import main as comic_preview_main

# Configure the main page
st.set_page_config(
    page_title="Comic Creation Suite",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .app-description {
        font-size: 1.2rem;
        text-align: center;
        color: #666;
        margin-bottom: 3rem;
    }
    .feature-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application entry point."""
    
    # Header
    st.markdown('<h1 class="main-header">🎨 Comic Creation Suite</h1>', unsafe_allow_html=True)
    st.markdown('<p class="app-description">Create, generate, and preview your comic projects with AI-powered tools</p>', unsafe_allow_html=True)
    
    # Navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose an app:",
        ["🏠 Home", "📝 Project Setup", "🎨 Image Generator", "📖 Comic Preview"]
    )
    
    # Page routing
    if page == "🏠 Home":
        show_home_page()
    elif page == "📝 Project Setup":
        project_setup_main()
    elif page == "🎨 Image Generator":
        image_generator_main()
    elif page == "📖 Comic Preview":
        comic_preview_main()

def show_home_page():
    """Display the home page with app overview."""
    
    st.markdown("## Welcome to Comic Creation Suite!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>📝 Project Setup</h3>
            <p>Create new comic projects, upload source material, and define characters and backgrounds.</p>
            <ul>
                <li>Upload PDFs and text files</li>
                <li>Define character descriptions</li>
                <li>Set up background scenes</li>
                <li>Organize your project structure</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <h3>🎨 Image Generator</h3>
            <p>Generate AI-powered images for your comic panels using advanced models.</p>
            <ul>
                <li>Create panel images from descriptions</li>
                <li>Multiple AI model options</li>
                <li>Custom generation prompts</li>
                <li>Save and manage generated images</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>📖 Comic Preview</h3>
            <p>View, edit, and manage your complete comic project with all panels.</p>
            <ul>
                <li>Preview all comic panels</li>
                <li>Edit panel scripts and dialogue</li>
                <li>Organize panel sequences</li>
                <li>Export your final comic</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <h3>🚀 Getting Started</h3>
            <p>Follow these steps to create your first comic:</p>
            <ol>
                <li>Start with <strong>Project Setup</strong></li>
                <li>Upload your source material</li>
                <li>Define characters and backgrounds</li>
                <li>Use <strong>Image Generator</strong> for panels</li>
                <li>Preview and edit in <strong>Comic Preview</strong></li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick start section
    st.markdown("---")
    st.markdown("## Quick Start")
    
    if st.button("🚀 Start New Project", type="primary"):
        st.switch_page("pages/1_Project_Setup.py")
    
    # Show recent projects if any
    st.markdown("## Recent Projects")
    st.info("No recent projects found. Start by creating a new project!")

if __name__ == "__main__":
    main() 