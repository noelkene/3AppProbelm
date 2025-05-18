"""Comic Preview Application."""

import streamlit as st
from pathlib import Path
import sys
import os
import json

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
                # Using a more robust way to handle project selection if IDs are the key
                project_options = {f"{p['name']} (ID: {p['id']})": p['id'] for p in project_list}
                if not project_options:
                    st.info("No projects available for selection.")
                    return

                selected_project_display_name = st.selectbox(
                    "Select a project",
                    options=list(project_options.keys()),
                    key="project_selector_preview"
                )
                
                if selected_project_display_name and st.button("Load Project"):
                    project_id = project_options[selected_project_display_name]
                    print(f"DEBUG PREVIEW LOAD: Attempting to load project with ID: '{project_id}'")
                    metadata_bytes = storage_service.get_project_file(project_id, "metadata.json")
                    if metadata_bytes:
                        try:
                            metadata_str = metadata_bytes.decode('utf-8')
                            project_data = json.loads(metadata_str)
                            # Ensure project_dir is consistent if it comes from JSON or is set from ID
                            if 'project_dir' not in project_data or not project_data['project_dir']:
                                project_data['project_dir'] = f"projects/{project_id}"
                            
                            project = Project.from_dict(project_data) # Use Project.from_dict
                            if project:
                                st.session_state.current_project = project
                                st.success(f"Loaded project: {project.name}")
                                st.rerun()
                            else:
                                st.error("Failed to reconstruct project from metadata.")
                        except json.JSONDecodeError:
                            st.error("Failed to parse project metadata (JSON decode error).")
                        except Exception as e_load:
                            st.error(f"Error reconstructing project: {str(e_load)}")
                            # import traceback # Already imported at top level if needed for full app
                            # st.error(f"Full Traceback: {traceback.format_exc()}")
                    else:
                        st.error(f"Could not retrieve metadata for project ID: {project_id}")
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
        if not project.panels:
            st.warning("This project has no panels defined yet.")
        else:
            for panel in project.panels:
                st.markdown(f"**Panel {panel.index + 1}**")
                image_to_display_uri = None
                caption_for_image = f"Panel {panel.index + 1}"

                if panel.official_final_image_uri:
                    image_to_display_uri = panel.official_final_image_uri
                    caption_for_image = f"Panel {panel.index + 1} (Official Final)"
                elif panel.final_variants: # Fallback to most recent final_variant if no official one
                    # Display the most recent final variant if official is not set
                    # We assume final_variants are appended, so -1 is latest from last generation batch
                    final_variant_candidate = panel.final_variants[-1]
                    if final_variant_candidate.image_uri:
                        image_to_display_uri = final_variant_candidate.image_uri
                        caption_for_image = f"Panel {panel.index + 1} (Latest Final Option)"
                elif panel.selected_variant: # Fallback to selected_variant if no final options at all
                    if panel.selected_variant.image_uri:
                        image_to_display_uri = panel.selected_variant.image_uri
                        caption_for_image = f"Panel {panel.index + 1} (Selected Initial Variant)"
                
                if image_to_display_uri:
                    image_bytes = storage_service.get_image(image_to_display_uri)
                    if image_bytes:
                        st.image(image_bytes, caption=caption_for_image, use_column_width=True)
                    else:
                        st.error(f"Panel {panel.index + 1}: Could not load image from {image_to_display_uri}")
                else:
                    st.warning(f"Panel {panel.index + 1}: No image available for display (no official, final, or selected variant with URI).")
                st.markdown("---") # Separator between panels
    
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