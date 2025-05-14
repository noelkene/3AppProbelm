"""Comic Preview Page - Shows the current state of the comic with all panels."""

import streamlit as st
from pathlib import Path
import json
from models.project import Project, ProjectJSONEncoder
from services.storage_service import StorageService

# Initialize services
storage_service = StorageService()

# Page config
st.set_page_config(layout="wide", page_title="Comic Preview")

def load_project(project_id: str) -> Project:
    """Load a project from storage."""
    try:
        project_data = storage_service.get_project_file(project_id, "metadata.json")
        if project_data:
            project = Project.load(json.loads(project_data))
            project.project_dir = Path(f"projects/{project_id}")
            return project
    except Exception as e:
        st.error(f"Error loading project: {str(e)}")
    return None

def render_comic_preview():
    """Render the comic preview interface."""
    st.title("📚 Comic Preview")
    
    # Project selection
    try:
        project_list = storage_service.list_projects()
        if not project_list:
            st.info("No projects found. Please create a project first.")
            return
            
        project_names = {p['name']: p['id'] for p in project_list}
        selected_project = st.selectbox(
            "Select a project to preview",
            options=list(project_names.keys()),
            key="preview_project_selector"
        )
        
        if selected_project:
            project = load_project(project_names[selected_project])
            if not project:
                st.error("Failed to load project")
                return
                
            # Project header
            st.header(f"Project: {project.name}")
            
            # Display panels
            if not project.panels:
                st.info("No panels have been generated yet.")
                return
                
            # Create a container for the comic
            comic_container = st.container()
            
            with comic_container:
                # Display each panel
                for i, panel in enumerate(project.panels):
                    st.markdown(f"### Panel {i + 1}")
                    
                    # Create two columns: one for the image, one for the description
                    img_col, desc_col = st.columns([2, 1])
                    
                    with img_col:
                        if panel.final_variant:
                            # Get the final selected image
                            image_bytes = storage_service.get_image(panel.final_variant.image_uri)
                            if image_bytes:
                                st.image(image_bytes, use_container_width=True)
                        elif panel.selected_variant:
                            # Show the selected variant if no final variant yet
                            image_bytes = storage_service.get_image(panel.selected_variant.image_uri)
                            if image_bytes:
                                st.image(image_bytes, use_container_width=True)
                        else:
                            st.info("No image selected for this panel")
                    
                    with desc_col:
                        st.markdown("**Panel Description:**")
                        st.write(panel.description)
                        
                        if panel.final_variant:
                            st.markdown("**Generation Prompt:**")
                            st.write(panel.final_variant.generation_prompt)
                        elif panel.selected_variant:
                            st.markdown("**Generation Prompt:**")
                            st.write(panel.selected_variant.generation_prompt)
                    
                    # Add a separator between panels
                    st.markdown("---")
                    
            # Add a download button for the entire comic
            if st.button("📥 Download Comic"):
                st.info("Download functionality will be implemented in a future update.")
                
    except Exception as e:
        st.error(f"Error loading projects: {str(e)}")

def main():
    """Main entry point for the preview page."""
    render_comic_preview()

if __name__ == "__main__":
    main() 