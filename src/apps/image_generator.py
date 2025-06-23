"""Image Generation and Management Application."""

import streamlit as st
from pathlib import Path
import sys
import os
import json
import traceback
import uuid
from typing import List, Dict
from dataclasses import asdict
import re # Ensure re is imported for parsing

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.models.project import Project, ProjectJSONEncoder, Character, Background
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
    if 'global_system_prompt' not in st.session_state:
        st.session_state.global_system_prompt = "Generate a comic panel image based on the visual description, adhering to character and background references if provided. Focus on clear storytelling and dynamic composition. Characters should match their descriptions and reference images accurately."

def render_sidebar():
    """Render the sidebar with project selection and navigation."""
    with st.sidebar:
        st.header("⚙️ Project Settings")
        
        try:
            project_list = storage_service.list_projects()
            if project_list:
                # Ensure unique project_id for selection if names can be non-unique
                # For now, assuming name is unique enough or first one is taken if duplicate names exist
                project_options = {f"{p['name']} (ID: {p['id']})": p['id'] for p in project_list}
                if not project_options: # Handle case where project_list might be empty after filtering or processing
                     st.info("No projects available for selection.")
                     return

                selected_project_display_name = st.selectbox(
                    "Select a project",
                    options=list(project_options.keys()),
                    key="project_selector"
                )
                
                if selected_project_display_name and st.button("Load Project"):
                    project_id = project_options[selected_project_display_name]
                    print(f"DEBUG LOAD: Attempting to load project with selected ID: '{project_id}'")
                    metadata_bytes = storage_service.get_project_file(project_id, "metadata.json")
                    if metadata_bytes:
                        try:
                            metadata_str = metadata_bytes.decode('utf-8')
                            project_data = json.loads(metadata_str)
                            print(f"DEBUG LOAD: Loaded metadata JSON for {project_id}. Project Name from JSON: {project_data.get('name')}")
                            # Ensure project_dir is consistent if it comes from JSON or is set from ID
                            if 'project_dir' not in project_data or not project_data['project_dir']:
                                project_data['project_dir'] = f"projects/{project_id}" # Or however it should be structured
                                print(f"DEBUG LOAD: Injected/Updated project_dir in project_data to: {project_data['project_dir']}")
                            
                            project = Project.from_dict(project_data)
                            if project:
                                st.session_state.current_project = project
                                st.session_state.current_panel_index = 0 
                                st.success(f"Loaded project: {project.name}")
                                st.rerun()
                            else:
                                st.error("Failed to reconstruct project from metadata.")
                        except json.JSONDecodeError:
                            st.error("Failed to parse project metadata (JSON decode error).")
                        except Exception as e_load:
                            st.error(f"Error reconstructing project: {str(e_load)}")
                    else:
                        st.error(f"Could not retrieve metadata for project ID: {project_id}")
            else:
                st.info("No projects found. Please create a project in the Project Setup app first.")
        except Exception as e:
            st.error(f"Error loading projects: {str(e)}")

        st.markdown("***")
        st.header("📝 Global System Prompt")
        st.session_state.global_system_prompt = st.text_area(
            "Default System Prompt for Image Generation",
            value=st.session_state.global_system_prompt,
            height=150,
            key="global_system_prompt_editor",
            help="This prompt is used as a base instruction for all image generations. It can be overridden per panel if needed (future feature)."
        )
            
        # Add Auto-Process All Panels button
        st.markdown("***")
        st.header("🚀 Automatic Processing")
        if st.session_state.current_project and st.session_state.current_project.panels:
            col1_auto, col2_auto = st.columns(2)
            with col1_auto:
                auto_variants = st.number_input("Variants per panel", min_value=2, max_value=5, value=3, key="auto_variants")
            with col2_auto:
                auto_temperature = st.slider("Image creativity", min_value=0.0, max_value=1.0, value=0.7, key="auto_temperature")
            
            if st.button("🎯 Auto-Process All Panels", type="primary", help="Automatically generate and select the best images for all panels"):
                with st.spinner("Processing all panels automatically... This may take several minutes."):
                    try:
                        results = ai_service.process_all_panels_automatically_sync(
                            project=st.session_state.current_project,
                            num_variants=auto_variants,
                            image_temperature=auto_temperature
                        )
                        
                        # Save the updated project
                        project_data_dict = st.session_state.current_project.to_dict()
                        project_json_str = json.dumps(project_data_dict, indent=2, cls=ProjectJSONEncoder)
                        project_json_bytes = project_json_str.encode('utf-8')
                        project_identifier = st.session_state.current_project.id if hasattr(st.session_state.current_project, 'id') and st.session_state.current_project.id else st.session_state.current_project.name
                        save_uri = storage_service.save_project_file(
                            project_id=project_identifier,
                            filename="metadata.json",
                            content=project_json_bytes,
                            content_type="application/json"
                        )
                        
                        # Display results
                        st.success(f"✅ Processed {results['processed_panels']}/{results['total_panels']} panels successfully!")
                        
                        # Show summary
                        if results['panel_results']:
                            st.subheader("📊 Processing Summary")
                            for panel_result in results['panel_results']:
                                st.write(f"**Panel {panel_result['panel_index'] + 1}**: Selected variant {panel_result['selected_variant'] + 1} (Score: {panel_result['best_score']:.1f}/10)")
                        
                        # Show errors if any
                        if results['errors']:
                            st.warning("⚠️ Some issues occurred:")
                            for error in results['errors']:
                                st.error(error)
                        
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error during automatic processing: {str(e)}")
        else:
            st.info("Load a project with panels to use automatic processing.")

        st.markdown("***")

        if st.session_state.current_project:
                project = st.session_state.current_project
                st.header("🎨 Project Assets Overview")
                if project.characters:
                    with st.expander("Characters", expanded=False):
                        for char_name, char_obj in project.characters.items():
                            st.subheader(f"{char_name}")
                            st.caption(f"Description: {char_obj.description}")
                            if char_obj.style_notes:
                                st.caption(f"Style Notes: {char_obj.style_notes}")
                            if char_obj.reference_images:
                                st.caption("Reference Images:")
                                for uri in char_obj.reference_images:
                                    st.code(uri, language=None)
                                    image_bytes = storage_service.get_image(uri)
                                    if image_bytes:
                                        st.image(image_bytes, width=150)
                                    else:
                                        st.warning(f"Could not load image: {uri}")
                            else:
                                st.caption("No reference images.")
                            st.markdown("---")
                else:
                    st.info("No characters defined in this project.")

                if project.backgrounds:
                    with st.expander("Backgrounds", expanded=False):
                        for bg_name, bg_obj in project.backgrounds.items():
                            st.subheader(f"{bg_name}")
                            st.caption(f"Description: {bg_obj.description}")
                            if bg_obj.style_notes:
                                st.caption(f"Style Notes: {bg_obj.style_notes}")
                            if bg_obj.reference_image:
                                st.caption("Reference Image:")
                                st.code(bg_obj.reference_image, language=None)
                                image_bytes = storage_service.get_image(bg_obj.reference_image)
                                if image_bytes:
                                    st.image(image_bytes, width=150)
                                else:
                                    st.warning(f"Could not load image: {bg_obj.reference_image}")
                            else:
                                st.caption("No reference image.")
                            st.markdown("---")
                else:
                    st.info("No backgrounds defined in this project.")

# Helper function to construct the initial combined prompt string
def _build_initial_combined_prompt(panel_visual_desc, global_sys_prompt, project_chars, project_bgs, ai_service_instance) -> str:
    prompt_parts = []
    prompt_parts.append("== VISUAL DESCRIPTION ==")
    prompt_parts.append(panel_visual_desc)
    prompt_parts.append("\n== SYSTEM PROMPT ==")
    prompt_parts.append(global_sys_prompt)
    
    # Auto-identify relevant characters based on the initial visual description
    if project_chars:
        prompt_parts.append("\n== AUTO-IDENTIFIED CHARACTER CONTEXT (Edit carefully below if needed) ==")
        known_char_names = list(project_chars.keys())
        # Use the passed ai_service_instance to call _extract_character_names
        mentioned_char_names = ai_service_instance._extract_character_names(panel_visual_desc, known_char_names)
        if mentioned_char_names:
            for name in mentioned_char_names:
                if name in project_chars:
                    char_obj = project_chars[name]
                    prompt_parts.append(f"Character Name: {name}")
                    prompt_parts.append(f"Description: {char_obj.description}")
                    uri = char_obj.reference_images[0] if char_obj.reference_images else "(No URI)"
                    prompt_parts.append(f"URI: {uri}")
                    prompt_parts.append("---") # Separator for multiple characters
        else:
            prompt_parts.append("(No project characters identified as relevant to the visual description above.)")
    else:
        prompt_parts.append("\n== CHARACTER CONTEXT ==")
        prompt_parts.append("(No characters defined in project. You can add context below if needed.)")

    if project_bgs:
        prompt_parts.append("\n== BACKGROUND CONTEXT (Listing all project backgrounds) ==")
        for name, bg_obj in project_bgs.items():
            prompt_parts.append(f"Background Name: {name}")
            prompt_parts.append(f"Description: {bg_obj.description}")
            uri = bg_obj.reference_image if bg_obj.reference_image else "(No URI)"
            prompt_parts.append(f"URI: {uri}")
            prompt_parts.append("---") # Separator
    else:
        prompt_parts.append("\n== BACKGROUND CONTEXT ==")
        prompt_parts.append("(No backgrounds defined in project.)")
        
    prompt_parts.append("\n== ADDITIONAL AI NOTES (Optional) ==")
    prompt_parts.append("(Add any extra instructions for the AI here)")
    
    return "\n".join(prompt_parts)

# Helper function to parse the combined prompt string
def _parse_combined_prompt(combined_prompt_str: str) -> Dict[str, any]:
    parsed = {
        'visual_description': "",
        'system_prompt': "",
        'character_references': [], # List of Dicts: {name, description, uri}
        'background_references': [], # List of Tuples: (name, uri)
        'additional_notes': ""
    }
    try:
        # Regex to find sections. Dotall allows . to match newlines.
        vis_desc_match = re.search(r"== VISUAL DESCRIPTION ==\n(.*?)(?:\n== SYSTEM PROMPT ==|\Z)", combined_prompt_str, re.DOTALL)
        if vis_desc_match: parsed['visual_description'] = vis_desc_match.group(1).strip()

        sys_prompt_match = re.search(r"== SYSTEM PROMPT ==\n(.*?)(?:\n== AUTO-IDENTIFIED CHARACTER CONTEXT|== CHARACTER CONTEXT ==|\Z)", combined_prompt_str, re.DOTALL)
        if sys_prompt_match: parsed['system_prompt'] = sys_prompt_match.group(1).strip()
        
        # Character context parsing (more complex due to multiple entries)
        # This regex attempts to find all character blocks until the next major section or end of string
        char_context_block_match = re.search(r"(?:== AUTO-IDENTIFIED CHARACTER CONTEXT.*?==|== CHARACTER CONTEXT ==)\n(.*?)(?:\n== BACKGROUND CONTEXT ==|\Z)", combined_prompt_str, re.DOTALL)
        if char_context_block_match:
            char_block_text = char_context_block_match.group(1).strip()
            # Split by "---" separator, then parse each individual character
            individual_char_entries = char_block_text.split("\n---\n")
            for entry in individual_char_entries:
                if entry.strip():
                    name_match = re.search(r"Character Name: (.*?)(?:\nDescription:|$)", entry)
                    desc_match = re.search(r"Description: (.*?)(?:\nURI:|$)", entry, re.DOTALL) # DOTALL for multi-line desc
                    uri_match = re.search(r"URI: (.*?)(?:\n|$)", entry)
                    name = name_match.group(1).strip() if name_match else f"ParsedChar{len(parsed['character_references'])+1}"
                    desc = desc_match.group(1).strip() if desc_match else ""
                    uri = uri_match.group(1).strip() if uri_match and uri_match.group(1).strip() != "(No URI)" else ""
                    if name and uri: # Only add if name and URI are present
                        parsed['character_references'].append({'name': name, 'description': desc, 'uri': uri})

        # Background context parsing (similar to characters)
        bg_context_block_match = re.search(r"== BACKGROUND CONTEXT.*?==\n(.*?)(?:\n== ADDITIONAL AI NOTES ==|\Z)", combined_prompt_str, re.DOTALL)
        if bg_context_block_match:
            bg_block_text = bg_context_block_match.group(1).strip()
            individual_bg_entries = bg_block_text.split("\n---\n")
            for entry in individual_bg_entries:
                if entry.strip():
                    name_match = re.search(r"Background Name: (.*?)(?:\nDescription:|$)", entry)
                    # desc_match for background (optional for now, but structure is there)
                    uri_match = re.search(r"URI: (.*?)(?:\n|$)", entry)
                    name = name_match.group(1).strip() if name_match else f"ParsedBg{len(parsed['background_references'])+1}"
                    uri = uri_match.group(1).strip() if uri_match and uri_match.group(1).strip() != "(No URI)" else ""
                    if name and uri:
                        parsed['background_references'].append((name, uri))
        
        notes_match = re.search(r"== ADDITIONAL AI NOTES.*?==\n(.*?)\Z", combined_prompt_str, re.DOTALL)
        if notes_match:
            notes_text = notes_match.group(1).strip()
            if notes_text != "(Add any extra instructions for the AI here)": # Avoid default placeholder
                 parsed['additional_notes'] = notes_text

    except Exception as e:
        print(f"Error parsing combined prompt: {e}")
        # Optionally, raise the error or return partially parsed data with an error flag
        st.error(f"Error parsing the combined prompt. Please check its structure. Details: {e}")
        return None # Indicate parsing failure
    return parsed

def render_panel_generator():
    """Render the panel image generation interface."""
    if not st.session_state.current_project:
        st.info("Please select a project from the sidebar to begin.")
        return

    project = st.session_state.current_project
    panel_idx = st.session_state.current_panel_index
    
    if not project.panels or panel_idx >= len(project.panels):
        st.warning("Project has no panels or panel index is out of bounds.")
        # Optionally, reset panel_idx or provide a way to add panels
        if project.panels:
            st.session_state.current_panel_index = 0
            panel_idx = 0
        else:
            return # Or display a message to add panels via Comic Previewer
    
    panel = project.panels[panel_idx]
    print(f"DEBUG RENDER: Loading panel {panel_idx} for display.")
    print(f"DEBUG RENDER: Panel object official_final_image_uri: '{panel.official_final_image_uri}'")
    # For more detail, you can print the whole panel dictionary
    try:
        panel_as_dict_for_debug = asdict(panel)
        print(f"DEBUG RENDER: Full panel object (as dict) for panel {panel_idx}: {json.dumps(panel_as_dict_for_debug, indent=2, cls=ProjectJSONEncoder)}")
    except Exception as e_asdict:
        print(f"DEBUG RENDER: Could not convert panel to dict for full debug print: {e_asdict}")

    # Panel navigation
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("Previous Panel") and panel_idx > 0:
            st.session_state.current_panel_index -= 1
            st.rerun()
    with col2:
        st.header(f"Panel {panel_idx + 1} of {len(project.panels)}")
    with col3:
        if st.button("Next Panel") and panel_idx < len(project.panels) - 1:
            st.session_state.current_panel_index += 1
            st.rerun()

    st.subheader("Panel Script & Visual Description")
    # Display the panel.script.visual_description but it's not the primary edit field for the AI prompt anymore
    st.caption("Original Visual Description (from script data):")
    st.text(panel.script.visual_description)
    st.markdown("---")

    st.subheader("Initial Image Generation Settings")

    # Construct the initial value for the combined prompt text area
    # Pass the ai_service instance to _build_initial_combined_prompt
    initial_combined_prompt_text = _build_initial_combined_prompt(
        panel.script.visual_description, 
        st.session_state.global_system_prompt, 
        project.characters, 
        project.backgrounds,
        ai_service # Pass the AIService instance
    )
    
    editable_combined_prompt = st.text_area(
        "Combined Prompt for Initial Image Generation (Edit all parts below)",
        value=initial_combined_prompt_text,
        key=f"combined_prompt_initial_{panel_idx}",
        height=600 # Make it tall
    )
    
    col1_ig, col2_ig = st.columns(2)
    with col1_ig:
        num_variants = st.number_input("Number of Variants", min_value=1, max_value=4, value=2, key=f"num_var_{panel_idx}")
    with col2_ig:
        image_temperature = st.slider("Image Variation", min_value=0.0, max_value=1.0, value=0.7, key=f"temp_var_{panel_idx}")
    
    # The "View Full Prompt" expander now just shows the content of the text_area above
    with st.expander("Confirm Editable Combined Prompt Content", expanded=False):
        st.text(editable_combined_prompt) 

    if st.button("Generate Images", key=f"gen_img_btn_{panel_idx}"):
        parsed_prompt_data = _parse_combined_prompt(editable_combined_prompt)
        
        if parsed_prompt_data:
            st.session_state.generating_images = True
            with st.spinner("Generating images..."):
                try:
                    # Use parsed data for the AI call
                    # Note: _extract_character_names is implicitly handled by how _build_initial_combined_prompt 
                    # includes characters. If user edits them out, they are out.
                    # Or, we could re-filter parsed_prompt_data['character_references'] based on parsed_prompt_data['visual_description'] here.
                    # For now, trust user edits in the combined block.

                    print(f"Debug Initial Gen - Parsed Visual Desc: {parsed_prompt_data['visual_description'][:100]}...")
                    print(f"Debug Initial Gen - Parsed System Prompt: {parsed_prompt_data['system_prompt'][:100]}...")
                    print(f"Debug Initial Gen - Parsed Char Refs: {parsed_prompt_data['character_references']}")
                    print(f"Debug Initial Gen - Parsed BG Refs: {parsed_prompt_data['background_references']}")
                    print(f"Debug Initial Gen - Parsed Add. Notes: {parsed_prompt_data['additional_notes']}")

                    generated_image_data_list = ai_service.generate_panel_variants(
                        panel_description=parsed_prompt_data['visual_description'], 
                        character_references=parsed_prompt_data['character_references'], 
                        background_references=parsed_prompt_data['background_references'],    
                        num_variants=num_variants,
                        system_prompt=parsed_prompt_data['system_prompt'],
                        temperature=image_temperature,
                        additional_instructions=parsed_prompt_data['additional_notes']
                    )
                    
                    new_variants = []
                    if generated_image_data_list:
                        for i, (image_bytes, generation_text) in enumerate(generated_image_data_list):
                            if image_bytes:
                                project_identifier = project.id if hasattr(project, 'id') and project.id else project.name
                                image_uri = storage_service.save_image(
                                    image_bytes=image_bytes, project_id=project_identifier, 
                                    panel_index=panel_idx, variant_type="generated",
                                    variant_index=len(panel.variants) + i 
                                )
                                if image_uri:
                                    variant = PanelVariant(
                                        image_uri=image_uri,
                                        # Use the parsed visual description as a fallback for the variant's prompt
                                        generation_prompt=generation_text if generation_text else parsed_prompt_data['visual_description'],
                                        selected=False
                                    )
                                    new_variants.append(variant)
                    
                    if new_variants:
                        panel.variants.extend(new_variants)
                        # IMPORTANT: Save the *parsed* visual description back to the panel script object
                        # if you want the user's edits in the combined prompt to persist for this field.
                        panel.script.visual_description = parsed_prompt_data['visual_description'] 
                        # Also consider if parsed system_prompt or notes should update something on the panel/project.
                        
                        # ... (Save project logic as before) ...
                        try:
                            project_data_dict = project.to_dict()
                            project_json_str = json.dumps(project_data_dict, indent=2, cls=ProjectJSONEncoder)
                            project_json_bytes = project_json_str.encode('utf-8')
                            project_identifier = project.id if hasattr(project, 'id') and project.id else project.name
                            save_uri = storage_service.save_project_file(
                                project_id=project_identifier,filename="metadata.json",
                                content=project_json_bytes,content_type="application/json"
                            )
                            if save_uri:
                                st.success("Images generated and project metadata saved!")
                            else:
                                st.error("Images generated but failed to save project metadata.")
                        except Exception as e_save:
                            st.error(f"Error saving project metadata: {str(e_save)}")
                    # ... (other messages for no new_variants or no generated_image_data_list)

                except Exception as e:
                    st.error(f"Error generating images: {str(e)}")
                    st.error(f"Traceback: {traceback.format_exc()}")
                st.session_state.generating_images = False
                st.rerun() # Rerun to reflect changes
        else:
            st.error("Failed to parse the combined prompt. Please check its structure and ensure all == SECTION HEADERS == are present.")

    # Display variants
    if panel.variants:
        st.subheader("Image Variants")
        
        # Auto-select best variant button
        if len(panel.variants) > 1:
            if st.button("🎯 Auto-Select Best Variant", key=f"auto_select_{panel_idx}", help="Automatically evaluate and select the best matching variant"):
                with st.spinner("Evaluating variants..."):
                    try:
                        # Get image bytes for all variants
                        variant_images = []
                        for variant in panel.variants:
                            if variant.image_uri:
                                image_bytes = storage_service.get_image(variant.image_uri)
                                if image_bytes:
                                    variant_images.append((image_bytes, variant.generation_prompt))
                        
                        if variant_images:
                            best_index, best_score, reasoning = ai_service.auto_select_best_image(
                                variant_images, 
                                panel.script.visual_description
                            )
                            
                            if best_index >= 0:
                                panel.selected_variant = panel.variants[best_index]
                                st.success(f"✅ Auto-selected variant {best_index + 1} (Score: {best_score:.1f}/10)")
                                st.info(f"**Reasoning:** {reasoning}")
                                
                                # Save project
                                try:
                                    project_data_dict = project.to_dict()
                                    project_json_str = json.dumps(project_data_dict, indent=2, cls=ProjectJSONEncoder)
                                    project_json_bytes = project_json_str.encode('utf-8')
                                    project_identifier = project.id if hasattr(project, 'id') and project.id else project.name
                                    save_uri = storage_service.save_project_file(
                                        project_id=project_identifier,
                                        filename="metadata.json",
                                        content=project_json_bytes,
                                        content_type="application/json"
                                    )
                                    st.rerun()
                                except Exception as e_save:
                                    st.error(f"Error saving project: {str(e_save)}")
                            else:
                                st.error("Failed to auto-select best variant")
                        else:
                            st.error("No valid variant images found for evaluation")
                    except Exception as e:
                        st.error(f"Error during auto-selection: {str(e)}")
        
        cols = st.columns(len(panel.variants))
        for i, variant in enumerate(panel.variants):
            with cols[i]:
                if variant.image_uri:
                    image_bytes = storage_service.get_image(variant.image_uri)
                    if image_bytes:
                        st.image(image_bytes)
                        
                        # Show if this variant is selected
                        if panel.selected_variant == variant:
                            st.success("✅ Selected")
                        
                        # Show evaluation score if available
                        if hasattr(variant, 'evaluation_score') and variant.evaluation_score is not None and variant.evaluation_score > 0:
                            st.caption(f"Score: {variant.evaluation_score:.1f}/10")
                        
                        if st.button(f"Select Variant {i + 1}", key=f"select_var_{panel_idx}_{i}"):
                            panel.selected_variant = variant
                            try:
                                project_data_dict = project.to_dict()
                                project_json_str = json.dumps(project_data_dict, indent=2, cls=ProjectJSONEncoder)
                                project_json_bytes = project_json_str.encode('utf-8')
                                project_identifier = project.id if hasattr(project, 'id') and project.id else project.name
                                save_uri = storage_service.save_project_file(
                                    project_id=project_identifier,
                                    filename="metadata.json",
                                    content=project_json_bytes,
                                    content_type="application/json"
                                )
                                if save_uri:
                                    st.success(f"Selected variant {i + 1} and project metadata saved.")
                                else:
                                    st.error(f"Selected variant {i + 1} but failed to save project metadata.")
                            except Exception as e_save_select:
                                st.error(f"Error saving project metadata after selecting variant: {str(e_save_select)}")
                            st.rerun()

    # Final image generation
    if panel.selected_variant:
        st.subheader("Final Image Generation Settings")
        
        edited_base_desc_for_final = st.text_area(
            "Base Panel Visual Description for Final Image", # Clarified label
            value=panel.script.visual_description, # Default to current visual desc from above
            key=f"base_desc_final_{panel_idx}", height=150
        )
        edited_selected_variant_prompt = st.text_area(
            "Selected Variant's Prompt (Refinement Guide)", # Clarified label
            value=panel.selected_variant.generation_prompt, 
            key=f"sel_var_prompt_final_{panel_idx}", height=100
        )
        final_additional_instructions = st.text_area(
            "Additional Fine-tuning Instructions for Final Image (Optional)", 
            key=f"final_instructions_{panel_idx}", height=100
        )

        col1_final_gen, col2_final_gen = st.columns(2)
        with col1_final_gen:
            num_final_variants = st.number_input(
                "Number of Final Variants to Generate", 
                min_value=1, max_value=4, value=1, # Use default, widget updates it
                key=f"num_final_var_{panel_idx}", 
                help="How many final image options to generate."
            )
        with col2_final_gen:
            final_image_temperature = st.slider(
                "Final Image Variation (Temperature)", 
                min_value=0.0, max_value=1.0, value=0.6, # Use default, widget updates it
                key=f"temp_final_var_{panel_idx}",
                help="Controls the creativity/randomness of the final image. Lower is more conservative."
            )

        # --- Construct and Display Prompt for Final Generation ---
        known_char_names_final = list(project.characters.keys())
        mentioned_char_names_final_display = ai_service._extract_character_names(edited_base_desc_for_final, known_char_names_final)
        auto_char_refs_final_display = []
        for name in mentioned_char_names_final_display:
            if name in project.characters:
                char_obj = project.characters[name]
                uri_display = char_obj.reference_images[0] if char_obj.reference_images else "No URI"
                auto_char_refs_final_display.append(f"  - {name}: {char_obj.description[:50]}... (URI: {uri_display})")

        # For now, assume all project backgrounds are potentially relevant for display
        auto_bg_refs_final_display = [] # Re-list for final prompt based on project backgrounds
        if project.backgrounds:
            for name, bg_obj in project.backgrounds.items():
                uri_display = bg_obj.reference_image if bg_obj.reference_image else "No URI"
                auto_bg_refs_final_display.append(f"  - {name}: {bg_obj.description[:50]}... (URI: {uri_display})")

        final_prompt_display_parts = [
            f"**Base Panel Visual Description (Editable Above):**\n{edited_base_desc_for_final}",
            f"**Selected Variant's Prompt (Editable Above, for Refinement):**\n{edited_selected_variant_prompt}",
            f"(Selected Variant's Image itself will be used as a strong visual reference by the AI)",
            f"\n**Global System Prompt (Editable in Sidebar):**\n{st.session_state.global_system_prompt}",
            f"\n**Automatically Included Character References (based on final description):**\n{chr(10).join(auto_char_refs_final_display) if auto_char_refs_final_display else 'None identified or no URIs'}",
            f"\n**Project Background References (All listed, AI will use if relevant):**\n{chr(10).join(auto_bg_refs_final_display) if auto_bg_refs_final_display else 'None defined in project'}"
        ]
        final_prompt_display_parts.append(f"\n**Number of Final Variants:** {num_final_variants}")
        final_prompt_display_parts.append(f"**Final Image Temperature:** {final_image_temperature}")
        if final_additional_instructions:
            final_prompt_display_parts.append(f"\n**Your Additional Instructions:**\n{final_additional_instructions}")
        
        with st.expander("View Full Context for Final Image Generation", expanded=False):
            st.markdown("\n".join(final_prompt_display_parts))

        if st.button("Generate Final Version(s)", key=f"gen_final_btn_{panel_idx}"):
            print("\n--- Debug: Starting Final Image Generation ---")
            with st.spinner("Generating final image(s)..."):
                try:
                    selected_image_bytes = None
                    if panel.selected_variant.image_uri:
                        selected_image_bytes = storage_service.get_image(panel.selected_variant.image_uri)
                    
                    if not selected_image_bytes:
                        st.error("Could not load selected variant image for final generation.")
                        return

                    # Use the edited selected variant prompt for the tuple passed to AI
                    selected_variant_data_for_ai = (selected_image_bytes, edited_selected_variant_prompt)
                    
                    base_desc_for_final_ai = edited_base_desc_for_final

                    # Automatically determine character references for AI Service for final pass
                    known_char_names_for_final_ai = list(project.characters.keys())
                    mentioned_char_names_for_final_ai = ai_service._extract_character_names(base_desc_for_final_ai, known_char_names_for_final_ai)
                    ai_char_refs_final_structured = []
                    for name in mentioned_char_names_for_final_ai:
                        if name in project.characters:
                            char_obj = project.characters[name]
                            if char_obj.reference_images and char_obj.reference_images[0]:
                                ai_char_refs_final_structured.append({
                                    'name': name,
                                    'description': char_obj.description,
                                    'uri': char_obj.reference_images[0]
                                })
                    print(f"Debug Final Gen - Panel Desc: {base_desc_for_final_ai[:100]}...")
                    print(f"Debug Final Gen - All user char URIs: {known_char_names_for_final_ai}")
                    print(f"Debug Final Gen - Potential char refs for extraction: {mentioned_char_names_for_final_ai}")
                    print(f"Debug Final Gen - Final char refs for AI: {ai_char_refs_final_structured}")

                    # Prepare background references for final AI (pass all from project with valid URIs)
                    ai_bg_refs_final_tuples = []
                    if project.backgrounds:
                        for name, bg_obj in project.backgrounds.items():
                            if bg_obj.reference_image and bg_obj.reference_image.strip():
                                ai_bg_refs_final_tuples.append((name, bg_obj.reference_image))

                    final_image_data_list = ai_service.generate_final_variants(
                        panel_description=base_desc_for_final_ai,
                        selected_variant=selected_variant_data_for_ai, # ensure this uses edited_selected_variant_prompt
                        character_references=ai_char_refs_final_structured, 
                        background_references=ai_bg_refs_final_tuples,     
                        num_variants=num_final_variants,
                        temperature=final_image_temperature,
                        additional_instructions=final_additional_instructions,
                        system_prompt=st.session_state.global_system_prompt # Use global system prompt
                    )
                    print(f"Debug: final_image_data_list from AI: {final_image_data_list}")
                    
                    # Clear previous final_variants before adding new ones for this generation pass
                    panel.final_variants = [] 

                    newly_generated_final_variants = []
                    if final_image_data_list:
                        for i_final, (final_image_bytes, final_generation_text) in enumerate(final_image_data_list):
                            if final_image_bytes:
                                project_identifier = project.id if hasattr(project, 'id') and project.id else project.name
                                final_image_uri = storage_service.save_image(
                                    image_bytes=final_image_bytes,
                                    project_id=project_identifier,
                                    panel_index=panel_idx,
                                    variant_type="final",
                                    variant_index=i_final # Use actual index from this generation batch
                                )
                                if final_image_uri:
                                    final_variant_obj = PanelVariant(
                                        image_uri=final_image_uri,
                                        generation_prompt=base_desc_for_final_ai,
                                        selected=False
                                    )
                                    newly_generated_final_variants.append(final_variant_obj)
                                else:
                                    st.warning(f"Failed to save final image variant {i_final + 1}")
                            else:
                                st.warning(f"AI service returned no image bytes for final variant {i_final + 1}")
                        
                        panel.final_variants.extend(newly_generated_final_variants)
                        # Update panel script description if it was edited and used for final image
                        panel.script.visual_description = base_desc_for_final_ai 
                        try:
                            project_data_dict = project.to_dict()
                            project_json_str = json.dumps(project_data_dict, indent=2, cls=ProjectJSONEncoder)
                            project_json_bytes = project_json_str.encode('utf-8')
                            project_identifier = project.id if hasattr(project, 'id') and project.id else project.name
                            save_uri = storage_service.save_project_file(
                                project_id=project_identifier,
                                filename="metadata.json",
                                content=project_json_bytes,
                                content_type="application/json"
                            )
                            if save_uri:
                                st.success(f"{len(newly_generated_final_variants)} final image(s) generated and project metadata updated!")
                            else:
                                st.error("Final image(s) generated but failed to update project metadata.")
                        except Exception as e_save_final:
                            st.error(f"Error saving project metadata after final image generation: {str(e_save_final)}")
                        st.rerun()
                    else:
                        st.error("AI service did not return any data for the final image(s).")
                        print("Debug: AI service returned no final_image_data_list.")
                        
                except Exception as e:
                    st.error(f"Error generating final image(s): {str(e)}")
                    st.error(f"Traceback: {traceback.format_exc()}")
            print("--- Debug: Finished Final Image Generation Attempt ---")
    
    if panel.official_final_image_uri:
        print(f"DEBUG RENDER: Displaying official final image for panel {panel_idx}: {panel.official_final_image_uri}")
        st.success(f"Official Final Image Selected:")
        official_image_bytes = storage_service.get_image(panel.official_final_image_uri)
        if official_image_bytes:
            print(f"DEBUG RENDER: Successfully fetched official_image_bytes, length: {len(official_image_bytes)}")
            try: # Temporary local save for debugging
                with open("temp_official_image.png", "wb") as f:
                    f.write(official_image_bytes)
                print("DEBUG RENDER: temp_official_image.png saved locally for inspection.")
            except Exception as e_save_temp:
                print(f"DEBUG RENDER: Failed to save temp_official_image.png: {e_save_temp}")
            st.image(official_image_bytes, width=300) 
            st.caption(panel.official_final_image_uri)
        else:
            print(f"DEBUG RENDER: storage_service.get_image returned None for {panel.official_final_image_uri}")
            st.warning(f"Could not load official final image from {panel.official_final_image_uri}")
    else:
        print(f"DEBUG RENDER: No official_final_image_uri to display for panel {panel_idx}.")

    if panel.final_variants:
        st.subheader("Generated Final Image(s) - Choose One")
        num_final_cols = len(panel.final_variants)
        if num_final_cols > 0:
            cols = st.columns(num_final_cols)
            for i, final_variant_item in enumerate(panel.final_variants):
                with cols[i % num_final_cols]:
                    if final_variant_item.image_uri:
                        final_image_bytes = storage_service.get_image(final_variant_item.image_uri)
                        if final_image_bytes:
                            st.image(final_image_bytes, caption=f"Final Option {i+1}")
                            with st.expander("View Prompt"):
                                st.caption(final_variant_item.generation_prompt)
                            if st.button(f"Select as Official Final Image", key=f"select_official_{panel_idx}_{i}"):
                                panel.official_final_image_uri = final_variant_item.image_uri
                                panel.approved = True
                                
                                try:
                                    project_data_dict = project.to_dict()
                                    project_json_str = json.dumps(project_data_dict, indent=2, cls=ProjectJSONEncoder)
                                    project_json_bytes = project_json_str.encode('utf-8')
                                    project_identifier = project.id if hasattr(project, 'id') and project.id else project.name
                                    save_uri = storage_service.save_project_file(
                                        project_id=project_identifier,
                                        filename="metadata.json",
                                        content=project_json_bytes,
                                        content_type="application/json"
                                    )
                                    if save_uri:
                                        st.success(f"Official final image set to Option {i+1} and project saved.")
                                    else:
                                        st.error("Failed to save project after selecting official final image.")
                                except Exception as e_save_official:
                                    st.error(f"Error saving project: {str(e_save_official)}")
                                st.rerun()
                        else:
                            st.warning(f"Could not load final image option {i+1} from {final_variant_item.image_uri}")
                    else:
                        st.info(f"Final variant option {i+1} has no image URI.")

def main():
    """Main application entry point."""
    initialize_session_state()
    render_sidebar()
    
    if st.session_state.current_project:
        # Auto-process panels if they haven't been processed yet
        unprocessed_panels = [panel for panel in st.session_state.current_project.panels 
                            if not panel.selected_variant]
        
        if unprocessed_panels:
            st.info("🔄 Automatically processing panels...")
            try:
                results = ai_service.process_all_panels_automatically_sync(
                    project=st.session_state.current_project,
                    num_variants=3,  # Default to 3 variants
                    image_temperature=0.7  # Default temperature
                )
                
                # Save the updated project
                project_data_dict = st.session_state.current_project.to_dict()
                project_json_str = json.dumps(project_data_dict, indent=2, cls=ProjectJSONEncoder)
                project_json_bytes = project_json_str.encode('utf-8')
                project_identifier = st.session_state.current_project.id if hasattr(st.session_state.current_project, 'id') and st.session_state.current_project.id else st.session_state.current_project.name
                save_uri = storage_service.save_project_file(
                    project_id=project_identifier,
                    filename="metadata.json",
                    content=project_json_bytes,
                    content_type="application/json"
                )
                
                st.success(f"✅ Processed {results['processed_panels']}/{results['total_panels']} panels successfully!")
                
                # Show summary
                if results['panel_results']:
                    st.subheader("📊 Processing Summary")
                    for panel_result in results['panel_results']:
                        st.write(f"**Panel {panel_result['panel_index'] + 1}**: Selected variant {panel_result['selected_variant'] + 1} (Score: {panel_result['best_score']:.1f}/10)")
                
                # Show errors if any
                if results['errors']:
                    st.warning("⚠️ Some issues occurred:")
                    for error in results['errors']:
                        st.error(error)
                
                st.rerun()
                
            except Exception as e:
                st.error(f"Error during automatic processing: {str(e)}")
        
        render_panel_generator()
    else:
        st.info("👈 Please select a project from the sidebar to begin.")

if __name__ == "__main__":
    main() 