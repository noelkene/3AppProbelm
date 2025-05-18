"""Project Setup and Script Management Application."""

import streamlit as st
from pathlib import Path
import json
from typing import Optional
import sys
import os
import fitz  # PyMuPDF
import traceback
import time

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.models.project import Project, Character, Background
from src.models.panel import Panel, PanelScript, PanelVariant
from src.services.storage_service import StorageService
from src.services.ai_service import AIService
from src.config.settings import DEFAULT_NUM_PANELS

storage_service = StorageService()
ai_service = AIService()

st.set_page_config(layout="wide", page_title="Comic Project Setup")

def initialize_session_state():
    """Initialize session state variables."""
    if 'current_project' not in st.session_state:
        st.session_state.current_project = None
    if 'editing_panel_index' not in st.session_state:
        st.session_state.editing_panel_index = None
    if 'generating_script' not in st.session_state:
        st.session_state.generating_script = False

def extract_text_from_pdf(pdf_file):
    """Extract text from a PDF file."""
    try:
        pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
        return text
    except Exception as e:
        st.error(f"Error extracting text from PDF: {str(e)}")
        return ""

def save_project(project: Project) -> bool:
    """Save project data to storage."""
    try:
        # Convert project to JSON
        project_dict = project.to_dict()
        project_json = json.dumps(project_dict, indent=2)
        
        # Try to save to Google Cloud Storage
        gcs_success = storage_service.save_project_file(
            project_id=project.project_dir.name,
            filename="metadata.json",
            content=project_json.encode('utf-8'),
            content_type="application/json"
        )
        
        # If Google Cloud Storage failed, save locally
        if not gcs_success:
            # Ensure project directory exists
            os.makedirs(f"data/projects/{project.project_dir.name}", exist_ok=True)
            
            # Save metadata locally
            with open(f"data/projects/{project.project_dir.name}/metadata.json", "w") as f:
                f.write(project_json)
                
            st.info("Saved project data to local storage")
        
        # Also save panels data
        panels_data = []
        for panel in project.panels:
            panels_data.append({
                "index": panel.index,
                "script": {
                    "visual_description": panel.script.visual_description,
                    "dialogue": panel.script.dialogue,
                    "captions": panel.script.captions,
                    "sfx": panel.script.sfx,
                    "thoughts": panel.script.thoughts,
                },
                "variants": [
                    {
                        "image_uri": variant.image_uri,
                        "generation_prompt": variant.generation_prompt,
                        "selected": variant.selected,
                        "feedback": variant.feedback
                    } for variant in panel.variants
                ] if panel.variants else []
            })
        
        panels_json = json.dumps(panels_data, indent=2)
        
        # Try to save panels to Google Cloud Storage
        gcs_panels_success = storage_service.save_project_file(
            project_id=project.project_dir.name,
            filename="panels.json",
            content=panels_json.encode('utf-8'),
            content_type="application/json"
        )
        
        # If Google Cloud Storage failed, save locally
        if not gcs_panels_success:
            with open(f"data/projects/{project.project_dir.name}/panels.json", "w") as f:
                f.write(panels_json)
        
        return True
    except Exception as e:
        st.error(f"Error saving project: {str(e)}")
        return False

def load_project(project_id: str) -> Optional[Project]:
    """Load project data from storage."""
    try:
        # Try to load metadata from Google Cloud
        metadata_bytes = storage_service.get_project_file(project_id, "metadata.json")
        metadata_dict = None
        
        # If Google Cloud failed, try loading from local storage
        if not metadata_bytes:
            local_path = f"data/projects/{project_id}/metadata.json"
            if os.path.exists(local_path):
                with open(local_path, "r") as f:
                    metadata_dict = json.load(f)
                st.info("Loaded project data from local storage")
        else:
            metadata_dict = json.loads(metadata_bytes)
        
        if not metadata_dict:
            st.error(f"Could not find metadata for project {project_id}")
            return None
        
        project = Project(
            name=metadata_dict.get("name", "Unnamed Project"),
            source_text=metadata_dict.get("source_text", ""),
            source_file=metadata_dict.get("source_file", ""),
            project_dir=Path(f"projects/{project_id}")
        )
        
        # Load characters
        for char_name, char_data in metadata_dict.get("characters", {}).items():
            character = Character(
                name=char_name,
                description=char_data.get("description", ""),
                reference_images=char_data.get("reference_images", [])
            )
            project.characters[char_name] = character
        
        # Load backgrounds
        for bg_name, bg_data in metadata_dict.get("backgrounds", {}).items():
            background = Background(
                name=bg_name,
                description=bg_data.get("description", ""),
                reference_image=bg_data.get("reference_image", "")
            )
            project.backgrounds[bg_name] = background
        
        # Try to load panels from Google Cloud
        panels_bytes = storage_service.get_project_file(project_id, "panels.json")
        panels_data = None
        
        # If Google Cloud failed, try loading from local storage
        if not panels_bytes:
            local_panels_path = f"data/projects/{project_id}/panels.json"
            if os.path.exists(local_panels_path):
                with open(local_panels_path, "r") as f:
                    panels_data = json.load(f)
        else:
            panels_data = json.loads(panels_bytes)
        
        if panels_data:
            for panel_data in panels_data:
                script_data = panel_data.get("script", {})
                script = PanelScript(
                    visual_description=script_data.get("visual_description", ""),
                    dialogue=script_data.get("dialogue", []),
                    captions=script_data.get("captions", []),
                    sfx=script_data.get("sfx", []),
                    thoughts=script_data.get("thoughts", [])
                )
                
                panel = Panel(
                    index=panel_data.get("index", 0),
                    script=script
                )
                
                # Load variants
                for variant_data in panel_data.get("variants", []):
                    variant = PanelVariant(
                        image_uri=variant_data.get("image_uri", ""),
                        generation_prompt=variant_data.get("generation_prompt", ""),
                        selected=variant_data.get("selected", False),
                        feedback=variant_data.get("feedback", None)
                    )
                    panel.variants.append(variant)
                
                project.panels.append(panel)
        
        return project
    except Exception as e:
        st.error(f"Error loading project: {str(e)}")
        return None

def render_sidebar():
    """Render the sidebar with project controls and character/background management."""
    with st.sidebar:
        st.header("⚙️ Project Controls")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("New Project"):
                st.session_state.current_project = None
                st.rerun()
        
        st.subheader("📚 Projects")
        try:
            project_list = storage_service.list_projects()
            if project_list:
                project_names = {p['name']: p['id'] for p in project_list}
                selected_project = st.selectbox(
                    "Select a project to load",
                    options=list(project_names.keys()),
                    key="project_selector"
                )
                
                if selected_project and st.button("Load Selected Project"):
                    project = load_project(project_names[selected_project])
                    if project:
                        st.session_state.current_project = project
                        st.success(f"Loaded project: {project.name}")
                        st.rerun()
        except Exception as e:
            st.error(f"Error loading projects: {str(e)}")
        
        if st.session_state.current_project:
            # Character Management
            st.subheader("🎨 Character Management")
            with st.expander("Add New Character", expanded=False):
                char_name = st.text_input("Character Name", key="new_char_name")
                char_desc = st.text_area("Character Description", key="new_char_desc")
                char_image = st.file_uploader("Character Reference Image", type=["png", "jpg", "jpeg"], key="new_char_image")
                
                if st.button("Add Character") and char_name and char_image:
                    st.write(f"[ProjectSetup] Attempting to add character: {char_name}")
                    st.write(f"[ProjectSetup] Uploaded file: name='{char_image.name}', type='{char_image.type}', size='{char_image.size}'")
                    current_project_dir_name = st.session_state.current_project.project_dir.name
                    st.write(f"[ProjectSetup] Current project directory name for GCS path: {current_project_dir_name}")

                    if not current_project_dir_name:
                        st.error("[ProjectSetup] Critical Error: Project directory name is empty. Cannot save character.")
                        return # Stop processing if project_dir.name is invalid

                    try:
                        image_bytes = char_image.getvalue()
                        st.write(f"[ProjectSetup] Image bytes length: {len(image_bytes)}")
                        
                        st.write(f"[ProjectSetup] Calling storage_service.save_character_reference with:")
                        st.write(f"  project_id='{current_project_dir_name}'")
                        st.write(f"  character_name='{char_name}'")
                        st.write(f"  mime_type='{char_image.type}'")
                        
                        gcs_uri = storage_service.save_character_reference(
                            project_id=current_project_dir_name,
                            character_name=char_name,
                            image_bytes=image_bytes,
                            mime_type=char_image.type
                        )
                        st.write(f"[ProjectSetup] GCS URI from save_character_reference: {gcs_uri}")
                        
                        if gcs_uri:
                            character = Character(
                                name=char_name,
                                description=char_desc,
                                reference_images=[gcs_uri]
                            )
                            st.session_state.current_project.characters[char_name] = character
                            st.write("[ProjectSetup] Character object created and added to project state.")
                            save_project(st.session_state.current_project)
                            st.success(f"Added character: {char_name}")
                            st.rerun()
                        else:
                            st.error(f"[ProjectSetup] Failed to save character reference image for '{char_name}'. GCS URI was empty.")
                    except Exception as e:
                        st.error(f"[ProjectSetup] Error adding character '{char_name}': {str(e)}")
                        st.error(f"[ProjectSetup] Full traceback: {traceback.format_exc()}")
            
            # Display existing characters
            if st.session_state.current_project.characters:
                st.subheader("📋 Characters")
                for char_name, character in st.session_state.current_project.characters.items():
                    with st.expander(f"👤 {char_name}", expanded=False):
                        st.write(f"**Description:** {character.description}")
                        if character.reference_images:
                            image_bytes = storage_service.get_image(character.reference_images[0])
                            if image_bytes:
                                st.image(image_bytes, width=150)
            
            # Background Management
            st.subheader("🎭 Background Management")
            with st.expander("Add New Background", expanded=False):
                bg_name = st.text_input("Background Name", key="new_bg_name")
                bg_desc = st.text_area("Background Description", key="new_bg_desc")
                bg_image = st.file_uploader("Background Reference Image", type=["png", "jpg", "jpeg"], key="new_bg_image")
                
                if st.button("Add Background") and bg_name and bg_image:
                    try:
                        image_bytes = bg_image.getvalue()
                        gcs_uri = storage_service.save_background_reference(
                            st.session_state.current_project.project_dir.name,
                            bg_name,
                            image_bytes,
                            bg_image.type
                        )
                        if gcs_uri:
                            background = Background(
                                name=bg_name,
                                description=bg_desc,
                                reference_image=gcs_uri
                            )
                            st.session_state.current_project.backgrounds[bg_name] = background
                            save_project(st.session_state.current_project)
                            st.success(f"Added background: {bg_name}")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error adding background: {str(e)}")
            
            # Display existing backgrounds
            if st.session_state.current_project.backgrounds:
                st.subheader("📋 Backgrounds")
                for bg_name, background in st.session_state.current_project.backgrounds.items():
                    with st.expander(f"🏞️ {bg_name}", expanded=False):
                        st.write(f"**Description:** {background.description}")
                        if background.reference_image:
                            image_bytes = storage_service.get_image(background.reference_image)
                            if image_bytes:
                                st.image(image_bytes, width=150)

def render_script_editor():
    """Render the script editing interface."""
    st.header("📝 Script Editor")
    
    # Add a prominent Script Generation section at the top
    st.write("---")
    st.subheader("🤖 Generate Panel Descriptions with AI")
    
    if st.session_state.current_project.source_text:
        with st.expander("AI Generation Settings", expanded=True):
            system_prompt = st.text_area(
                "Instructions for AI (Overall System Prompt)",
                value="""You are an expert comic scriptwriter. Your task is to break down a story into a series of comic book panels.
For each panel, you need to provide a sequential panel number, a brief technical description (shot type, key action, critical SFX/captions), 
a detailed visual description for the artist, and the segment of the source story text that the panel represents.""",
                height=150
            )
            
            batch_size = st.slider("Panels Per Batch Request", min_value=1, max_value=10, value=5, # Reduced max batch for stability with complex JSON
                                  help="Number of panels to request from the AI in a single API call. Smaller values are more reliable but slower.")
            
            debug_mode = st.checkbox("Show Debug Information", value=False, 
                                   help="Displays detailed information about the AI generation process")
            
        if st.button("🚀 Generate All Panel Details (Batch)", type="primary", help="Use AI to create brief descriptions, visual descriptions, and identify source text for all panels"):
            with st.spinner("🤖 AI is working on your panel details..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                debug_info = st.empty() if debug_mode else None
                
                try:
                    status_text.write("Preparing context...")
                    progress_bar.progress(10)
                    
                    character_context = ""
                    for name, char in st.session_state.current_project.characters.items():
                        character_context += f"{name}: {char.description}\n"
                    
                    background_context = ""
                    for name, bg in st.session_state.current_project.backgrounds.items():
                        background_context += f"{name}: {bg.description}\n"
                    
                    source_text = st.session_state.current_project.source_text
                    total_panels_in_project = len(st.session_state.current_project.panels)
                    
                    status_text.write(f"Generating panel details in batches...")
                    if debug_mode and debug_info:
                        debug_info.text(f"Sending batch request for {total_panels_in_project} panels with batch size {batch_size}")
                    
                    # Call the revamped AI service method
                    generated_panel_data_list = ai_service.generate_panel_descriptions(
                        chapter_text=source_text,
                        system_prompt=system_prompt,
                        num_panels=total_panels_in_project,
                        character_context=character_context,
                        background_context=background_context,
                        batch_size=batch_size
                    )
                    
                    if debug_mode and debug_info:
                        debug_info.text(f"Received {len(generated_panel_data_list)} panel data objects from AI.")
                        st.write("Raw AI Data:", generated_panel_data_list) # For debugging

                    successful_updates = 0
                    status_text.write("Updating project panels with generated data...")
                    for i, panel_data in enumerate(generated_panel_data_list):
                        if i < total_panels_in_project:
                            project_panel = st.session_state.current_project.panels[i]
                            project_panel.script.brief_description = panel_data.get("brief_description", "Error: Brief description not found")
                            project_panel.script.visual_description = panel_data.get("visual_description", "Error: Visual description not found")
                            project_panel.script.source_text = panel_data.get("source_text_segment", "Error: Source text segment not found")
                            project_panel.script.skip_enhancement = True # Mark as processed by the new batch method
                            successful_updates +=1
                        progress_bar.progress(30 + int(( (i+1) / total_panels_in_project ) * 60) )
                    
                    status_text.write("Saving project...")
                    progress_bar.progress(95)
                    save_project(st.session_state.current_project)
                    progress_bar.progress(100)

                    if successful_updates == total_panels_in_project:
                        status_text.success(f"✅ All {successful_updates} panel details generated and updated successfully!")
                    else:
                        status_text.warning(f"⚠️ Processed {successful_updates}/{total_panels_in_project} panels. Some may have errors or were not returned by AI. Please review.")
                    
                except Exception as e:
                    progress_bar.progress(100)
                    status_text.error(f"❌ Error generating panel details: {str(e)}")
                    if debug_mode:
                        st.write("Error details:", traceback.format_exc())
    else:
        st.warning("⚠️ Please add source text in the project settings before generating panel descriptions.")
    
    st.write("---")
    
    # Display panels for editing - single view, no more view_mode
    for i, panel_to_display in enumerate(st.session_state.current_project.panels):
        # Ensure panel_to_display.index matches its current position i, crucial for stable UI & keying
        if panel_to_display.index != i:
            st.warning(f"Correcting panel index mismatch for panel that was {panel_to_display.index} to {i}")
            panel_to_display.index = i # Correct in-memory index before rendering this panel
            # Consider saving project here if this correction should be persisted immediately,
            # but frequent saves can slow down UI. Best to save after all manipulations.

        with st.expander(f"Panel {panel_to_display.index + 1}", expanded=i == st.session_state.editing_panel_index):
            # Panel manipulation buttons
            col1, col2, col3, col4, col5 = st.columns([2,2,2,2,1]) # Adjusted column ratios for 5 buttons
            current_panel_true_index = panel_to_display.index

            with col1:
                if st.button(f"⬆️ Insert Before", key=f"insert_before_{current_panel_true_index}"):
                    st.session_state.current_project.panels.insert(current_panel_true_index, Panel.create_empty(current_panel_true_index))
                    for new_idx, p_to_reindex in enumerate(st.session_state.current_project.panels):
                        p_to_reindex.index = new_idx
                    save_project(st.session_state.current_project)
                    st.session_state.editing_panel_index = current_panel_true_index
                    st.rerun()
            
            with col2:
                if st.button(f"⬇️ Insert After", key=f"insert_after_{current_panel_true_index}"):
                    insert_at_index = current_panel_true_index + 1
                    st.session_state.current_project.panels.insert(insert_at_index, Panel.create_empty(insert_at_index))
                    for new_idx, p_to_reindex in enumerate(st.session_state.current_project.panels):
                        p_to_reindex.index = new_idx
                    save_project(st.session_state.current_project)
                    st.session_state.editing_panel_index = insert_at_index
                    st.rerun()
            
            with col3:
                if st.button(f"🔀 Split to 2", key=f"split_2_{current_panel_true_index}"):
                    with st.spinner("Splitting panel and generating descriptions for 2 new panels..."):
                        split_descriptions = ai_service.split_panel_descriptions(
                            original_description=panel_to_display.script.visual_description,
                            brief_description=panel_to_display.script.brief_description,
                            source_text=panel_to_display.script.source_text,
                            num_panels=2
                        )
                        new_panels_list = []
                        for idx, desc_data in enumerate(split_descriptions):
                            new_panels_list.append(Panel(
                                index=0, 
                                script=PanelScript(
                                    visual_description=desc_data.get("visual_description", f"Split part {idx + 1}/2"),
                                    brief_description=desc_data.get("brief_description", f"Split part {idx + 1}/2 brief"),
                                    source_text=desc_data.get("source_text_segment", panel_to_display.script.source_text),
                                    dialogue=panel_to_display.script.dialogue if idx == 0 else [],
                                    captions=panel_to_display.script.captions if idx == 0 else [],
                                    sfx=panel_to_display.script.sfx if idx == 0 else [],
                                    thoughts=panel_to_display.script.thoughts if idx == 0 else []
                                ),
                                notes=f"Split from original panel {panel_to_display.index + 1}"
                            ))
                        st.session_state.current_project.panels.pop(current_panel_true_index)
                        for insert_idx_offset, new_p in enumerate(new_panels_list):
                            st.session_state.current_project.panels.insert(current_panel_true_index + insert_idx_offset, new_p)
                        for new_idx, p_to_reindex in enumerate(st.session_state.current_project.panels):
                            p_to_reindex.index = new_idx
                        save_project(st.session_state.current_project)
                        st.session_state.editing_panel_index = current_panel_true_index 
                        st.rerun()

            with col4:
                if st.button(f"🔀 Split to 3", key=f"split_3_{current_panel_true_index}"):
                    with st.spinner("Splitting panel and generating descriptions for 3 new panels..."):
                        split_descriptions = ai_service.split_panel_descriptions(
                            original_description=panel_to_display.script.visual_description,
                            brief_description=panel_to_display.script.brief_description,
                            source_text=panel_to_display.script.source_text,
                            num_panels=3
                        )
                        new_panels_list = []
                        for idx, desc_data in enumerate(split_descriptions):
                            new_panels_list.append(Panel(
                                index=0, 
                                script=PanelScript(
                                    visual_description=desc_data.get("visual_description", f"Split part {idx + 1}/3"),
                                    brief_description=desc_data.get("brief_description", f"Split part {idx + 1}/3 brief"),
                                    source_text=desc_data.get("source_text_segment", panel_to_display.script.source_text),
                                    dialogue=panel_to_display.script.dialogue if idx == 0 else [],
                                    captions=panel_to_display.script.captions if idx == 0 else [],
                                    sfx=panel_to_display.script.sfx if idx == 0 else [],
                                    thoughts=panel_to_display.script.thoughts if idx == 0 else []
                                ),
                                notes=f"Split from original panel {panel_to_display.index + 1}"
                            ))
                        st.session_state.current_project.panels.pop(current_panel_true_index)
                        for insert_idx_offset, new_p in enumerate(new_panels_list):
                            st.session_state.current_project.panels.insert(current_panel_true_index + insert_idx_offset, new_p)
                        for new_idx, p_to_reindex in enumerate(st.session_state.current_project.panels):
                            p_to_reindex.index = new_idx
                        save_project(st.session_state.current_project)
                        st.session_state.editing_panel_index = current_panel_true_index 
                        st.rerun()
            
            with col5:
                if st.button(f"🗑️", key=f"delete_{current_panel_true_index}", help="Delete this panel"):
                    if len(st.session_state.current_project.panels) > 1:
                        st.session_state.current_project.panels.pop(current_panel_true_index)
                        for new_idx, p_to_reindex in enumerate(st.session_state.current_project.panels):
                            p_to_reindex.index = new_idx
                        save_project(st.session_state.current_project)
                        st.session_state.editing_panel_index = max(0, current_panel_true_index - 1)
                        st.rerun()
                    else:
                        st.error("Cannot delete the only panel.")
            
            st.write("---")
            
            # Unified Panel Content Editing
            panel_to_display.script.source_text = st.text_area(
                "Source Text Segment (from chapter)",
                panel_to_display.script.source_text,
                key=f"source_text_{current_panel_true_index}", # Use true index for key
                height=100
            )
            
            panel_to_display.script.brief_description = st.text_area(
                "Brief Description (shot type, key action, critical SFX/Captions)",
                panel_to_display.script.brief_description,
                key=f"brief_desc_{current_panel_true_index}", # Use true index for key
                help="E.g., 'WIDE SHOT - Character runs through forest. SFX: THUMP THUMP'", 
                height=100
            )
            
            panel_to_display.script.visual_description = st.text_area(
                "Detailed Visual Description (for artist)",
                panel_to_display.script.visual_description,
                key=f"visual_desc_{current_panel_true_index}", # Use true index for key
                height=200
            )
            
            if st.button(f"Save Panel {panel_to_display.index + 1} Details", key=f"save_panel_details_{current_panel_true_index}"):
                save_project(st.session_state.current_project)
                st.success(f"Panel {panel_to_display.index + 1} details saved!")

def render_project_setup():
    """Render the project setup interface."""
    st.header("🎬 New Project Setup")
    
    project_name = st.text_input("Project Name")
    
    # Add tabs for different input methods
    input_tab1, input_tab2 = st.tabs(["Enter Text", "Upload File"])
    
    with input_tab1:
        source_text = st.text_area("Source Text/Story", height=300)
    
    with input_tab2:
        uploaded_file = st.file_uploader("Upload Text or PDF File", type=["txt", "pdf"])
        file_text = ""
        if uploaded_file is not None:
            if uploaded_file.type == "text/plain":
                file_text = uploaded_file.getvalue().decode("utf-8")
                st.success("Text file uploaded successfully!")
            elif uploaded_file.type == "application/pdf":
                file_text = extract_text_from_pdf(uploaded_file)
                st.success("PDF file uploaded successfully!")
            
            if file_text:
                st.text_area("Extracted Text Preview", file_text[:1000] + ("..." if len(file_text) > 1000 else ""), height=200)
    
    # Combine text from both sources
    final_text = file_text if uploaded_file else source_text
    
    num_panels = st.number_input("Number of Panels", min_value=1, value=DEFAULT_NUM_PANELS)
    
    if st.button("Create Project") and project_name:
        try:
            project = Project(
                name=project_name,
                source_text=final_text,
                source_file=uploaded_file.name if uploaded_file else "",
                project_dir=Path(f"projects/{project_name.lower().replace(' ', '_')}")
            )
            
            # Initialize empty panels
            for i in range(num_panels):
                panel = Panel(
                    index=i,
                    script=PanelScript(
                        visual_description=f"Panel {i + 1} description",
                        brief_description="",
                        source_text=""
                    )
                )
                project.panels.append(panel)
            
            st.session_state.current_project = project
            save_project(project)
            st.success("Project created successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error creating project: {str(e)}")

def main():
    initialize_session_state()
    render_sidebar()
    
    if st.session_state.current_project is None:
        render_project_setup()
    else:
        render_script_editor()

if __name__ == "__main__":
    main() 