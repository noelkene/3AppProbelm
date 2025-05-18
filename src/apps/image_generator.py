"""Image Generation and Management Application."""

import streamlit as st
from pathlib import Path
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.models.project import Project
from src.models.panel import Panel, PanelVariant
from src.services.storage_service import StorageService
from src.services.ai_service import AIService

storage_service = StorageService()
ai_service = AIService()

st.set_page_config(layout="wide", page_title="Comic Image Generator")

def initialize_session_state():
    """Initialize session state variables."""
    if 'current_project' not in st.session_state:
        st.session_state.current_project = None
    if 'current_panel_index' not in st.session_state:
        st.session_state.current_panel_index = 0
    if 'generating_images' not in st.session_state:
        st.session_state.generating_images = False

def render_sidebar():
    """Render the sidebar with project selection and navigation."""
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

def render_panel_generator():
    """Render the panel image generation interface."""
    if not st.session_state.current_project:
        st.info("Please select a project from the sidebar to begin.")
        return

    project = st.session_state.current_project
    
    # Panel navigation
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("Previous Panel") and st.session_state.current_panel_index > 0:
            st.session_state.current_panel_index -= 1
            st.rerun()
    with col2:
        st.header(f"Panel {st.session_state.current_panel_index + 1} of {len(project.panels)}")
    with col3:
        if st.button("Next Panel") and st.session_state.current_panel_index < len(project.panels) - 1:
            st.session_state.current_panel_index += 1
            st.rerun()

    # Get current panel
    panel = project.panels[st.session_state.current_panel_index]
    
    # Display panel description
    st.subheader("Panel Description")
    st.write(panel.panel_description)
    
    # Image generation controls
    st.subheader("Image Generation")
    
    col1, col2 = st.columns(2)
    with col1:
        num_variants = st.number_input("Number of Variants", min_value=1, max_value=4, value=2)
    with col2:
        image_temperature = st.slider("Image Variation", min_value=0.0, max_value=1.0, value=0.7)
    
    if st.button("Generate Images"):
        st.session_state.generating_images = True
        with st.spinner("Generating images..."):
            try:
                variants = ai_service.generate_panel_images(
                    panel.panel_description,
                    num_variants,
                    image_temperature,
                    project.characters,
                    project.backgrounds
                )
                
                panel.variants.extend(variants)
                storage_service.save_project(project)
                st.success("Images generated successfully!")
            except Exception as e:
                st.error(f"Error generating images: {str(e)}")
        st.session_state.generating_images = False
        st.rerun()
    
    # Display variants
    if panel.variants:
        st.subheader("Image Variants")
        cols = st.columns(len(panel.variants))
        for i, variant in enumerate(panel.variants):
            with cols[i]:
                if variant.image_uri:
                    image_bytes = storage_service.get_image(variant.image_uri)
                    if image_bytes:
                        st.image(image_bytes)
                        if st.button(f"Select Variant {i + 1}", key=f"select_{i}"):
                            panel.selected_variant = variant
                            storage_service.save_project(project)
                            st.success(f"Selected variant {i + 1}")
                            st.rerun()
    
    # Final image generation
    if panel.selected_variant:
        st.subheader("Final Image Generation")
        if st.button("Generate Final Version"):
            with st.spinner("Generating final image..."):
                try:
                    final_variant = ai_service.generate_final_panel_image(
                        panel.panel_description,
                        panel.selected_variant.generation_prompt,
                        project.characters,
                        project.backgrounds
                    )
                    
                    panel.final_variants.append(final_variant)
                    storage_service.save_project(project)
                    st.success("Final image generated successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error generating final image: {str(e)}")

def main():
    initialize_session_state()
    render_sidebar()
    render_panel_generator()

if __name__ == "__main__":
    main() 