"""Comic Preview Application."""

import streamlit as st
from pathlib import Path
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.models.project import Project
from src.services.storage_service import StorageService

storage_service = StorageService()

st.set_page_config(layout="wide", page_title="Comic Preview")

def initialize_session_state():
    """Initialize session state variables."""
    if 'current_project' not in st.session_state:
        st.session_state.current_project = None

def render_sidebar():
    """Render the sidebar with project selection."""
    with st.sidebar:
        st.header("⚙️ Project Selection")
        
        try:
            project_list = storage_service.list_projects()
            if project_list:
                project_names = {p['name']: p['id'] for p in project_list}
                selected_project = st.selectbox(
                    "Select a project",
                    options=list(project_names.keys()),
                    key="project_selector"
                )
                
                if selected_project and st.button("Load Project"):
                    project = storage_service.load_project(project_names[selected_project])
                    if project:
                        st.session_state.current_project = project
                        st.success(f"Loaded project: {project.name}")
                        st.rerun()
            else:
                st.info("No projects found. Please create a project in the Project Setup app first.")
        except Exception as e:
            st.error(f"Error loading projects: {str(e)}")

def render_comic_preview():
    """Render the comic preview with full script."""
    if not st.session_state.current_project:
        st.info("Please select a project from the sidebar to begin.")
        return

    project = st.session_state.current_project
    
    st.title(f"Comic Preview: {project.name}")
    
    # Layout: Image column (2/3) and Script column (1/3)
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Comic Panels")
        for panel in project.panels:
            if panel.final_variants:
                # Display the most recent final variant
                final_variant = panel.final_variants[-1]
                if final_variant.image_uri:
                    image_bytes = storage_service.get_image(final_variant.image_uri)
                    if image_bytes:
                        st.image(image_bytes, use_column_width=True)
            elif panel.selected_variant:
                # Fall back to selected variant if no final variant exists
                if panel.selected_variant.image_uri:
                    image_bytes = storage_service.get_image(panel.selected_variant.image_uri)
                    if image_bytes:
                        st.image(image_bytes, use_column_width=True)
                        st.warning("Using selected variant - final version not yet generated")
            else:
                st.error(f"Panel {panel.index + 1}: No image generated yet")
    
    with col2:
        st.header("Full Script")
        for panel in project.panels:
            with st.expander(f"Panel {panel.index + 1}", expanded=True):
                st.markdown(panel.full_script)

def main():
    initialize_session_state()
    render_sidebar()
    render_comic_preview()

if __name__ == "__main__":
    main() 