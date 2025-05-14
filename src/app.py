"""Main Streamlit application for the Manga Storyboard Generator."""

import streamlit as st
import datetime
from pathlib import Path
import json
import uuid
from typing import Optional
import fitz  # PyMuPDF
import traceback
import asyncio

from config.settings import (
    DEFAULT_NUM_PANELS, MAX_PANELS, MIN_PANELS,
    VARIANT_COUNT, FINAL_VARIANT_COUNT,
    DEFAULT_IMAGE_TEMPERATURE, MAX_IMAGE_TEMPERATURE, MIN_IMAGE_TEMPERATURE,
    ADDITIONAL_INSTRUCTION_TEXT
)
from models.project import Project, Character, Background, Panel, PanelVariant, ProjectJSONEncoder
from services.ai_service import AIService
from services.storage_service import StorageService

# Initialize services
ai_service = AIService()
storage_service = StorageService()

# Page config
st.set_page_config(layout="wide", page_title="AI Manga Storyboard Generator")

def initialize_session_state():
    """Initialize session state variables."""
    if 'current_project' not in st.session_state:
        st.session_state.current_project = None
    if 'current_panel_idx' not in st.session_state:
        st.session_state.current_panel_idx = 0
    if 'editing_panel' not in st.session_state:
        st.session_state.editing_panel = False
    if 'viewing_variants' not in st.session_state:
        st.session_state.viewing_variants = False

def load_project(project_id: str) -> Optional[Project]:
    """Load a project from GCS."""
    try:
        project_data = storage_service.get_project_file(project_id, "metadata.json")
        if project_data:
            project = Project.load(json.loads(project_data))
            project.project_dir = Path(f"projects/{project_id}")
            return project
    except Exception as e:
        st.error(f"Error loading project: {str(e)}")
    return None

def save_project(project: Project):
    """Save a project to GCS."""
    try:
        metadata = project.save()
        storage_service.save_project_file(
            project.project_dir.name,
            "metadata.json",
            json.dumps(metadata, cls=ProjectJSONEncoder).encode(),
            "application/json"
        )
    except Exception as e:
        st.error(f"Error saving project: {str(e)}")

def render_sidebar():
    """Render the sidebar with project controls and settings."""
    with st.sidebar:
        st.header("⚙️ Project Controls")
        
        # Project selection/creation
        if st.button("New Project"):
            st.session_state.current_project = None
            st.rerun()
            
        # Character management
        st.subheader("🎨 Characters")
        char_name = st.text_input("Character Name")
        char_desc = st.text_area("Character Description")
        char_image = st.file_uploader("Character Reference Image", type=["png", "jpg", "jpeg"])
        
        if st.button("Add Character") and char_name and char_image:
            try:
                print(f"\n=== Adding Character: {char_name} ===")
                if not st.session_state.current_project:
                    print("Error: No active project")
                    st.error("Please create a project first")
                    return
                
                print("Reading image file...")
                image_bytes = char_image.getvalue()
                print(f"Image size: {len(image_bytes)} bytes")
                print(f"Image type: {char_image.type}")
                
                print("Saving character reference to storage...")
                gcs_uri = storage_service.save_character_reference(
                    st.session_state.current_project.project_dir.name,
                    char_name,
                    image_bytes,
                    char_image.type
                )
                
                if gcs_uri:
                    print(f"Successfully saved image to: {gcs_uri}")
                    character = Character(
                        name=char_name,
                        description=char_desc,
                        reference_images=[gcs_uri]
                    )
                    st.session_state.current_project.characters[char_name] = character
                    print("Saving project state...")
                    save_project(st.session_state.current_project)
                    st.success(f"Added character: {char_name}")
                    st.rerun()
                else:
                    print("Error: Failed to save image to storage")
                    st.error("Failed to save character image. Please try again.")
            except Exception as e:
                print(f"Error adding character: {str(e)}")
                print(f"Full traceback: {traceback.format_exc()}")
                st.error(f"Error adding character: {str(e)}")
        
        # Display saved characters
        if st.session_state.current_project and st.session_state.current_project.characters:
            st.subheader("📋 Saved Characters")
            for char_name, character in st.session_state.current_project.characters.items():
                with st.expander(f"👤 {char_name}"):
                    st.write(f"**Description:** {character.description}")
                    if character.reference_images:
                        image_bytes = storage_service.get_image(character.reference_images[0])
                        if image_bytes:
                            st.image(image_bytes, width=150)
        
        # Background management
        st.subheader("🎭 Backgrounds")
        bg_name = st.text_input("Background Name")
        bg_desc = st.text_area("Background Description")
        bg_image = st.file_uploader("Background Reference Image", type=["png", "jpg", "jpeg"])
        
        if st.button("Add Background") and bg_name and bg_image:
            if not st.session_state.current_project:
                st.error("Please create a project first")
                return
                
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
        
        # Project settings
        st.subheader("⚙️ Settings")
        num_panels = st.slider(
            "Number of Panels",
            MIN_PANELS,
            MAX_PANELS,
            DEFAULT_NUM_PANELS,
            key="num_panels"
        )
        st.session_state.num_panels = num_panels
        
        st.info(f"Current Date (Server): {datetime.datetime.now().date()}")

def render_panel_editor(panel: Panel):
    """Render the panel editor interface."""
    st.subheader(f"Editing Panel {panel.index + 1}")

    # Always define these at the start
    character_refs = [
        (char.name, ref)
        for char in st.session_state.current_project.characters.values()
        for ref in char.reference_images
    ]
    background_refs = [
        (bg.name, bg.reference_image)
        for bg in st.session_state.current_project.backgrounds.values()
    ]

    # Panel description editor
    new_desc = st.text_area(
        "Panel Description",
        value=panel.description,
        height=200
    )
    
    if new_desc != panel.description:
        panel.description = new_desc
        save_project(st.session_state.current_project)
    
    # Image generation section
    st.subheader("🎨 Image Generation")
    
    # Add temperature control
    temperature = st.slider(
        "Generation Temperature",
        MIN_IMAGE_TEMPERATURE,
        MAX_IMAGE_TEMPERATURE,
        DEFAULT_IMAGE_TEMPERATURE,
        help="Higher values create more varied results, lower values are more consistent"
    )
    
    if not panel.variants:
        if st.button("✨ Generate Panel Image", key=f"generate_image_{panel.index}"):
            with st.spinner("Generating panel image..."):
                variants = ai_service.generate_panel_variants(
                    panel.description,
                    character_refs,
                    background_refs,
                    VARIANT_COUNT,
                    "Generate manga panel variants",
                    temperature=temperature
                )
                
                panel.variants = []
                for i, (image_bytes, prompt) in enumerate(variants):
                    gcs_uri = storage_service.save_image(
                        image_bytes,
                        st.session_state.current_project.project_dir.name,
                        panel.index,
                        "initial",
                        i
                    )
                    if gcs_uri:
                        panel.variants.append(PanelVariant(
                            image_uri=gcs_uri,
                            generation_prompt=prompt
                        ))
                
                save_project(st.session_state.current_project)
                st.rerun()
    else:
        st.success("Panel variants generated! Please select your preferred version.")
        
        # Add regenerate button
        if st.button("🔄 Regenerate Panel", key=f"regenerate_{panel.index}"):
            with st.spinner("Regenerating panel image..."):
                variants = ai_service.generate_panel_variants(
                    panel.description,
                    character_refs,
                    background_refs,
                    VARIANT_COUNT,
                    "Generate manga panel variants",
                    temperature=temperature
                )
                
                panel.variants = []
                for i, (image_bytes, prompt) in enumerate(variants):
                    gcs_uri = storage_service.save_image(
                        image_bytes,
                        st.session_state.current_project.project_dir.name,
                        panel.index,
                        "initial",
                        i
                    )
                    if gcs_uri:
                        panel.variants.append(PanelVariant(
                            image_uri=gcs_uri,
                            generation_prompt=prompt
                        ))
                
                save_project(st.session_state.current_project)
                st.rerun()
        
        # Display all variants in a grid
        cols = st.columns(3)
        for i, variant in enumerate(panel.variants):
            with cols[i % 3]:
                # Fetch image data from storage
                image_bytes = storage_service.get_image(variant.image_uri)
                if image_bytes:
                    st.image(image_bytes, caption=f"Variant {i + 1}")
                    if st.button(f"Select Variant {i + 1}", key=f"select_variant_{panel.index}_{i}"):
                        panel.selected_variant = variant
                        save_project(st.session_state.current_project)
                        st.rerun()
        
        # If a variant is selected, show final variant generation
        if panel.selected_variant:
            st.success(f"Selected Variant {panel.variants.index(panel.selected_variant) + 1}")
            
            # Add additional instruction text for final variants
            additional_instructions = st.text_area(
                "Additional Instructions for Final Variants",
                value=ADDITIONAL_INSTRUCTION_TEXT,
                help="Add any specific instructions or modifications for the final variant generation"
            )
            
            if not panel.final_variants:
                if st.button("✨ Generate Final Variants", key=f"generate_final_{panel.index}"):
                    with st.spinner("Generating final variants..."):
                        # Get image bytes for selected variant
                        selected_image_bytes = storage_service.get_image(panel.selected_variant.image_uri)
                        if selected_image_bytes:
                            final_variants = ai_service.generate_final_variants(
                                panel.description,
                                (selected_image_bytes, panel.selected_variant.generation_prompt),
                                character_refs,
                                background_refs,
                                FINAL_VARIANT_COUNT,
                                temperature=temperature,
                                additional_instructions=additional_instructions
                            )
                            
                            panel.final_variants = []
                            for i, (image_bytes, prompt) in enumerate(final_variants):
                                gcs_uri = storage_service.save_image(
                                    image_bytes,
                                    st.session_state.current_project.project_dir.name,
                                    panel.index,
                                    "final",
                                    i
                                )
                                if gcs_uri:
                                    panel.final_variants.append(PanelVariant(
                                        image_uri=gcs_uri,
                                        generation_prompt=prompt
                                    ))
                            
                            save_project(st.session_state.current_project)
                            st.rerun()
            else:
                st.success("Final variants generated! Please select your preferred version.")
                
                # Display all final variants in a grid
                cols = st.columns(3)
                for i, variant in enumerate(panel.final_variants):
                    with cols[i % 3]:
                        # Fetch image data from storage
                        image_bytes = storage_service.get_image(variant.image_uri)
                        if image_bytes:
                            st.image(image_bytes, caption=f"Final Variant {i + 1}")
                            if st.button(f"Select Final Variant {i + 1}", key=f"select_final_{panel.index}_{i}"):
                                panel.final_variant = variant
                                save_project(st.session_state.current_project)
                                st.rerun()

def render_final_view(project: Project):
    """Render the final view with all panels in a column layout."""
    st.title("Final Storyboard")
    
    # Create two columns: one for images, one for prompts
    img_col, prompt_col = st.columns([2, 1])
    
    with img_col:
        st.subheader("Panels")
        for panel in project.panels:
            if panel.approved and panel.final_variants:
                selected_variant = next((v for v in panel.final_variants if v.selected), None)
                if selected_variant:
                    print(f"Getting image from URI: {selected_variant.image_uri}")
                    image_bytes = storage_service.get_image(selected_variant.image_uri)
                    if image_bytes:
                        st.image(image_bytes, use_container_width=True)
                        st.markdown("---")
    
    with prompt_col:
        st.subheader("Prompts")
        for panel in project.panels:
            if panel.approved and panel.final_variants:
                selected_variant = next((v for v in panel.final_variants if v.selected), None)
                if selected_variant:
                    st.markdown(f"**Panel {panel.index + 1}**")
                    st.text_area(
                        "Description",
                        value=panel.description,
                        height=100,
                        key=f"desc_{panel.index}"
                    )
                    st.text_area(
                        "Generation Prompt",
                        value=selected_variant.generation_prompt,
                        height=100,
                        key=f"prompt_{panel.index}"
                    )
                    st.markdown("---")

    print(f"Project directory name: {project.project_dir.name if hasattr(project, 'project_dir') else 'N/A'}")

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes."""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        st.error(f"Error extracting text from PDF: {str(e)}")
        return ""

def render_main_content():
    """Render the main content area."""
    st.title("📚➡️🖼️ AI Manga Storyboard Generator")
    
    # Project creation/loading
    if not st.session_state.current_project:
        st.header("Create New Project")
        project_name = st.text_input("Project Name")
        source_file = st.file_uploader("Upload Source Text", type=["txt", "pdf"])
        
        if st.button("Create Project") and project_name and source_file:
            try:
                print(f"\n=== Creating New Project: {project_name} ===")
                project_id = str(uuid.uuid4())
                print(f"Generated project ID: {project_id}")
                
                # Extract text based on file type
                print(f"Processing source file: {source_file.name} ({source_file.type})")
                if source_file.type == "text/plain":
                    print("Extracting text from plain text file...")
                    source_text = source_file.getvalue().decode()
                elif source_file.type == "application/pdf":
                    print("Extracting text from PDF file...")
                    source_text = extract_text_from_pdf(source_file.getvalue())
                else:
                    print(f"Error: Unsupported file type: {source_file.type}")
                    st.error(f"Unsupported file type: {source_file.type}")
                    return
                
                print(f"Extracted text length: {len(source_text)} characters")
                if not source_text.strip():
                    print("Error: No text could be extracted from file")
                    st.error("No text could be extracted from the file. Please check the file and try again.")
                    return
                
                print("Creating project instance...")
                project = Project(
                    name=project_name,
                    source_text=source_text,
                    source_file=source_file.name,
                    project_dir=Path(f"projects/{project_id}")
                )
                
                # Save source file
                print("Saving source file to storage...")
                storage_service.save_project_file(
                    project_id,
                    source_file.name,
                    source_file.getvalue(),
                    source_file.type
                )
                
                print("Setting current project and saving state...")
                st.session_state.current_project = project
                save_project(project)
                print("Project created successfully")
                st.rerun()
                
            except Exception as e:
                print(f"Error creating project: {str(e)}")
                print(f"Full traceback: {traceback.format_exc()}")
                st.error(f"Error creating project: {str(e)}")
    
    # Project workflow
    if st.session_state.current_project:
        project = st.session_state.current_project
        
        # Project header
        st.header(f"Project: {project.name}")
        
        # Only show final view if there are panels and all are approved
        if project.panels and all(panel.approved for panel in project.panels):
            render_final_view(project)
        else:
            # Panel generation
            if not project.panels:
                st.info("No panels have been generated yet. Click below to generate panel descriptions.")
                if st.button("Generate Panel Descriptions"):
                    try:
                        print(f"\n=== Generating Panel Descriptions for Project: {project.name} ===")
                        with st.spinner("Generating panel descriptions..."):
                            print("Preparing character context...")
                            character_context = "\n".join(
                                f"Character: {char.name}\nDescription: {char.description}"
                                for char in project.characters.values()
                            )
                            print(f"Character context length: {len(character_context)} characters")
                            
                            print("Preparing background context...")
                            background_context = "\n".join(
                                f"Background: {bg.name}\nDescription: {bg.description}"
                                for bg in project.backgrounds.values()
                            )
                            print(f"Background context length: {len(background_context)} characters")
                            
                            # Get the number of panels from the slider in the sidebar
                            num_panels = st.session_state.get('num_panels', DEFAULT_NUM_PANELS)
                            print(f"Generating {num_panels} panel descriptions...")
                            
                            descriptions = ai_service.generate_panel_descriptions(
                                project.source_text,
                                "Generate manga panel descriptions",
                                num_panels,
                                character_context,
                                background_context
                            )
                            
                            print(f"Generated {len(descriptions)} panel descriptions")
                            for i, desc in enumerate(descriptions):
                                print(f"Creating panel {i + 1}...")
                                project.panels.append(Panel(
                                    description=desc,
                                    index=i
                                ))
                            
                            print("Saving project state...")
                            save_project(project)
                            print("Panel generation complete")
                            st.rerun()
                            
                    except Exception as e:
                        print(f"Error generating panel descriptions: {str(e)}")
                        print(f"Full traceback: {traceback.format_exc()}")
                        st.error(f"Error generating panel descriptions: {str(e)}")
            # Panel navigation
            if project.panels:
                current_idx = st.session_state.current_panel_idx
                current_panel = project.panels[current_idx]
                
                # Panel navigation controls
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    if st.button("⬅️ Previous") and current_idx > 0:
                        st.session_state.current_panel_idx -= 1
                        st.rerun()
                with col2:
                    st.markdown(f"### Panel {current_idx + 1} of {len(project.panels)}")
                with col3:
                    if st.button("Next ➡️") and current_idx < len(project.panels) - 1:
                        st.session_state.current_panel_idx += 1
                        st.rerun()
                
                # Panel editor
                render_panel_editor(current_panel)

def main():
    """Main application entry point."""
    initialize_session_state()
    render_sidebar()
    render_main_content()

if __name__ == "__main__":
    main() 