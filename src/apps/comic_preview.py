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
from src.services.ai_service import AIService

storage_service = StorageService()
ai_service = AIService()

st.set_page_config(layout="wide", page_title="Comic Preview")

def initialize_session_state():
    """Initialize session state variables."""
    if 'current_project' not in st.session_state:
        st.session_state.current_project = None
    if 'refinement_requests' not in st.session_state:
        st.session_state.refinement_requests = {}

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

def get_best_variant(panel):
    """Get the best variant for a panel based on evaluation scores."""
    if not panel.variants:
        return None
    
    # Find the variant with the highest evaluation score
    best_variant = None
    best_score = -1
    
    for variant in panel.variants:
        if hasattr(variant, 'evaluation_score') and variant.evaluation_score is not None:
            if variant.evaluation_score > best_score:
                best_score = variant.evaluation_score
                best_variant = variant
    
    # If no variants have scores, return the first one
    if best_variant is None and panel.variants:
        best_variant = panel.variants[0]
    
    return best_variant

def render_image_refinement_section(panel, panel_index):
    """Render the image refinement section for a panel."""
    st.markdown(f"### Panel {panel_index + 1} - Image Refinement")
    
    # Get the best variant
    best_variant = get_best_variant(panel)
    
    if not best_variant:
        st.warning("No variants available for this panel.")
        return
    
    # Display the current best image
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🎯 Automatically Selected Best Image")
        if best_variant.image_uri:
            image_bytes = storage_service.get_image(best_variant.image_uri)
            if image_bytes:
                st.image(image_bytes, caption=f"Score: {best_variant.evaluation_score:.1f}/10" if hasattr(best_variant, 'evaluation_score') and best_variant.evaluation_score else "No score", use_column_width=True)
            else:
                st.error("Could not load image")
        else:
            st.error("No image URI available")
    
    with col2:
        st.subheader("✏️ Request Changes")
        
        # Show current prompt
        current_prompt = best_variant.generation_prompt if hasattr(best_variant, 'generation_prompt') else panel.script.visual_description
        st.text_area("Current Prompt", value=current_prompt, height=100, key=f"current_prompt_{panel_index}")
        
        # User can modify the prompt
        refinement_prompt = st.text_area(
            "Describe the changes you want:",
            placeholder="e.g., Make the character more angry, change the lighting to be darker, add more detail to the background...",
            height=100,
            key=f"refinement_prompt_{panel_index}"
        )
        
        if st.button("🔄 Generate Refined Image", key=f"refine_button_{panel_index}"):
            if refinement_prompt.strip():
                with st.spinner("Generating refined image..."):
                    try:
                        # Combine original prompt with refinement request
                        combined_prompt = f"{current_prompt}. {refinement_prompt}"
                        
                        # Generate new image
                        generated_data = ai_service.generate_panel_variants(
                            panel_description=combined_prompt,
                            character_references=[],
                            background_references=[],
                            num_variants=1,
                            system_prompt="Generate a high-quality comic panel image based on the description."
                        )
                        if generated_data and len(generated_data) > 0:
                            new_image_bytes, new_text = generated_data[0]
                            
                            if new_image_bytes:
                                # Save the new image
                                project_identifier = st.session_state.current_project.name
                                new_image_uri = storage_service.save_image(
                                    image_bytes=new_image_bytes,
                                    project_id=project_identifier,
                                    panel_index=panel_index,
                                    variant_type="refined",
                                    variant_index=len(panel.variants) + 1
                                )
                                
                                if new_image_uri:
                                    # Create new variant
                                    from src.models.panel import PanelVariant
                                    new_variant = PanelVariant(
                                        image_uri=new_image_uri,
                                        generation_prompt=combined_prompt,
                                        selected=True  # This becomes the new selected variant
                                    )
                                    
                                    # Add to panel
                                    panel.variants.append(new_variant)
                                    panel.selected_variant = new_variant
                                    
                                    # Update project metadata using the save_project function
                                    from src.apps.project_setup import save_project
                                    if save_project(st.session_state.current_project):
                                        st.success("✅ Refined image generated and saved!")
                                        st.rerun()
                                    else:
                                        st.error("Image generated but failed to save project metadata")
                                else:
                                    st.error("Failed to save refined image")
                            else:
                                st.error("Failed to generate refined image")
                        else:
                            st.error("No image data received from AI service")
                    except Exception as e:
                        st.error(f"Error generating refined image: {str(e)}")
            else:
                st.warning("Please describe the changes you want to make")

def render_comic_preview():
    """Render the comic preview with full script."""
    if not st.session_state.current_project:
        st.info("Please select a project from the sidebar to begin.")
        return

    project = st.session_state.current_project
    
    st.title(f"Comic Preview: {project.name}")
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["📖 Comic Preview", "🎨 Image Refinement"])
    
    with tab1:
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
    
    with tab2:
        st.header("🎨 Image Refinement")
        st.info("Here you can see the automatically selected best images and request changes to improve them.")
        
        if not project.panels:
            st.warning("This project has no panels defined yet.")
        else:
            for panel in project.panels:
                render_image_refinement_section(panel, panel.index)
                st.markdown("---")

def main():
    initialize_session_state()
    render_sidebar()
    render_comic_preview()

if __name__ == "__main__":
    main() 