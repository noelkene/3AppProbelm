import re
import json
import streamlit as st
from google.cloud import storage as gcs_storage
from google import genai
from google.genai import types
import fitz  # PyMuPDF
# import io # Not explicitly used in the latest flow, but good for general IO if needed later
import uuid
import traceback # For detailed error logging
import datetime # Added for displaying current date/time

# --- Page Config (MUST BE THE FIRST STREAMLIT COMMAND) ---
# THIS LINE SHOULD BE EXECUTED BEFORE ANY OTHER st.* CALLS
st.set_page_config(layout="wide", page_title="AI Manga Storyboard Generator")

# --- Configuration (Non-Streamlit constants) ---
# Ensure these are correctly set for your environment
GOOGLE_CLOUD_PROJECT = "platinum-banner-303105" # CHANGE THIS TO YOUR PROJECT ID
GOOGLE_CLOUD_LOCATION = "us-central1"  # e.g., "us-central1"
GCS_BUCKET_NAME = "comic_book_heros_and_villans" # CHANGE THIS TO YOUR BUCKET
MULTIMODAL_MODEL_ID = "gemini-2.0-flash-preview-image-generation"
TEXT_MODEL_ID_FOR_INITIAL_PROMPTS = "gemini-2.5-pro-preview-05-06"

# --- Global Initializations (Variables for GCS status, no st.* calls here) ---
gcs_client_initialized = False
gcs_bucket_initialized = False # Indicates if the default bucket object was successfully created
gcs_connection_message = ""

try:
    storage_client = gcs_storage.Client(project=GOOGLE_CLOUD_PROJECT)
    # Try to get the default bucket; this doesn't mean other buckets can't be accessed if the client is fine.
    try:
        gcs_bucket = storage_client.bucket(GCS_BUCKET_NAME)
        if gcs_bucket.exists(): # Check if bucket actually exists
             gcs_bucket_initialized = True
             gcs_connection_message = f"GCS Client initialized. Default bucket '{GCS_BUCKET_NAME}' is accessible."
        else:
            gcs_connection_message = f"GCS Client initialized, but default bucket '{GCS_BUCKET_NAME}' not found or no access. Check bucket name and permissions."
            gcs_bucket = None # Explicitly set to None if not accessible
    except Exception as bucket_e:
        gcs_connection_message = f"GCS Client initialized, but error accessing default bucket '{GCS_BUCKET_NAME}': {bucket_e}. GCS features might be limited."
        gcs_bucket = None

    gcs_client_initialized = True # Client itself is initialized
except Exception as e:
    gcs_connection_message = f"GCS client initialization failed: {e}. GCS features will be unavailable."
    storage_client = None
    gcs_bucket = None

def get_genai_client():
    """Initializes and returns the GenAI client."""
    try:
        client = genai.Client(
            project=GOOGLE_CLOUD_PROJECT,
            location=GOOGLE_CLOUD_LOCATION, # Required for Vertex AI based models
            vertexai=True # Indicates usage of Vertex AI backend
        )        # st.sidebar.success("Google GenAI Client Initialized")
        return client
    except Exception as e:
        st.error(f"Failed GenAI Client init: {e}. Project: {GOOGLE_CLOUD_PROJECT}, Location: {GOOGLE_CLOUD_LOCATION}")
        st.text(traceback.format_exc())
        return None

def save_image_to_gcs(image_bytes, file_name_prefix="panel_image", mime_type='image/png'):
    """Saves image bytes to GCS and returns the GCS URI."""
    if not storage_client: # Check if client is initialized
        st.error("GCS save error: GCS client not initialized.")
        return None
    if not image_bytes:
        st.error("GCS save error: image_bytes is None or empty. AI may not have returned image data or file not uploaded correctly.")
        return None

    try:
        unique_id = uuid.uuid4()
        extension = mime_type.split('/')[-1]
        if extension == 'jpeg': extension = 'jpg'
        if not extension or len(extension) > 4 : extension = 'png'

        blob_name = f"{file_name_prefix}_{unique_id}.{extension}"
        
        # Use the configured GCS_BUCKET_NAME for saving
        bucket_to_save_to = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket_to_save_to.blob(blob_name)

        blob.upload_from_string(image_bytes, content_type=mime_type)
        gcs_uri = f"gs://{GCS_BUCKET_NAME}/{blob_name}" # URI uses the target bucket name
        st.success(f"Image successfully saved to GCS: {gcs_uri}")
        return gcs_uri
    except Exception as e:
        blob_name_ref = blob_name if 'blob_name' in locals() else 'N/A'
        st.error(f"!!! FAILED TO SAVE IMAGE TO GCS !!! Bucket: '{GCS_BUCKET_NAME}', Blob: '{blob_name_ref}'.")
        st.error(f"GCS Save Exception: {e}")
        st.text(traceback.format_exc())
        return None

# NEW HELPER FUNCTION
def get_image_bytes_from_gcs(gcs_uri):
    """Downloads an image from GCS and returns its bytes."""
    if not storage_client:
        st.error("GCS client not available for downloading image.")
        return None
    if not gcs_uri or not gcs_uri.startswith("gs://"):
        st.error(f"Invalid GCS URI provided: {gcs_uri}")
        return None
    try:
        # Parse bucket name and blob name from URI
        path_parts = gcs_uri[5:].split("/")
        bucket_name = path_parts[0]
        blob_name = "/".join(path_parts[1:])

        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        if not blob.exists():
            st.error(f"GCS object not found at URI: {gcs_uri}")
            return None
        
        image_bytes = blob.download_as_bytes()
        return image_bytes
    except Exception as e:
        st.error(f"Failed to download image from GCS ({gcs_uri}): {e}")
        # st.text(traceback.format_exc()) # Optional: show full traceback in UI
        print(f"Traceback for GCS download error ({gcs_uri}): {traceback.format_exc()}")
        return None

def extract_text_from_pdf(uploaded_file):
    """Extracts text from an uploaded PDF file."""
    text = ""
    if not uploaded_file:
        return text
    try:
        pdf_bytes = uploaded_file.getvalue()
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
    except Exception as e:
        st.error(f"Error reading PDF '{uploaded_file.name}': {e}")
        st.text(traceback.format_exc())
        return f"Error reading PDF: {e}"
    return text

def generate_initial_panel_descriptions(chapter_text, system_prompt, num_panels):
    """Generates initial panel descriptions using a text-based AI model (expecting JSON output)."""
    client = get_genai_client()
    if not client:
        return [f"Error: AI Client not initialized. Panel {i+1}" for i in range(num_panels)]


    instruction = (
        f"System Prompt:\n{system_prompt}\n\n"
        f"Chapter Text (truncated to approx 25k characters for prompt safety):\n\"\"\"{chapter_text[:25000]}\"\"\"\n\n"
        f"Based on the chapter text and system prompt, generate {num_panels} detailed text descriptions for sequential manga panels. "
        "Each description will serve as a prompt for a multimodal AI to generate an image and accompanying text (dialogue/SFX). "
        "For each panel, focus on: Scene (setting, mood), Characters (appearance, position, expression), Action (what's happening), Emotion (conveyed by characters/scene), "
        "and any key Dialogue or Sound Effects (SFX) that should be explicitly part of the panel's text. "
        "Your response MUST be a single JSON object. This object must have exactly one key: 'response'. "
        "The value for the 'response' key must be a JSON STRING representing an array of panel objects. "
        "Each panel object in this array must have two keys: "
        "1. 'panel_description': A string containing the full detailed description for the panel, starting with '**Panel Description [Number]:**\\n' followed by bullet points for Scene, Characters, etc. (e.g., '* **Scene:** ...'). Ensure newlines within this description are escaped as '\\n', and quotes are escaped as '\\\"'. "
        "2. 'dialogue_sfx': A string containing only the dialogue or SFX for that panel (e.g., 'SFX: CRACK'), or an empty string if none. Ensure quotes are escaped as '\\\"'."
    )

    safety_settings = [
        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    ]
    config = types.GenerateContentConfig(
        temperature=0.6,
        max_output_tokens=8192,
        safety_settings=safety_settings,
        response_mime_type = "application/json",
        response_schema = {"type":"OBJECT","properties":{"response":{"type":"STRING"}}}
    )

    try:
        st.text("Sending request for initial panel descriptions (expecting JSON)...")
        st.text_area("Instruction to Text Model:", instruction, height=300, disabled=True)

        response = client.models.generate_content(
            model=TEXT_MODEL_ID_FOR_INITIAL_PROMPTS,
            contents=instruction,
            config=config,
        )
        prompts_text = response.text or ""
        print(f"Length of prompts_text: {len(prompts_text)}")
        print(f"Last 100 characters of prompts_text: {prompts_text[-100:]}")
        # Also, check the finish reason from the model response
        if response.candidates and response.candidates[0].finish_reason:
            print(f"Model Finish Reason: {response.candidates[0].finish_reason}")
            if response.candidates[0].finish_reason.name == "MAX_TOKENS":
                st.warning("AI response was likely truncated due to reaching the maximum token limit for the model's output.")
        else:
            print("Could not retrieve finish reason from response.")
        print("Raw AI response for panel descriptions (prompts_text - should be outer JSON string):")
        print(prompts_text)
        st.text_area("Raw AI response for panel descriptions:", prompts_text, height=300, key="raw_initial_desc_response")

        panel_descriptions = []
        if prompts_text:
            try:
                if prompts_text.strip().startswith("```json"):
                    prompts_text = prompts_text.strip()[7:-3].strip()
                elif prompts_text.strip().startswith("```"):
                    prompts_text = prompts_text.strip()[3:-3].strip()

                outer_data = json.loads(prompts_text)
                inner_json_array_string = outer_data.get("response")

                if not isinstance(inner_json_array_string, str):
                    st.error(f"Error: The 'response' field in the JSON output was not a string as expected. Got: {type(inner_json_array_string)}")
                    raise ValueError("Inner 'response' value is not a string.")

                panels_list = json.loads(inner_json_array_string)

                if not isinstance(panels_list, list):
                    st.error(f"Error: The parsed 'response' content was not a list as expected. Got: {type(panels_list)}")
                    raise ValueError("Parsed inner 'response' is not a list.")

                for panel_object in panels_list:
                    if not isinstance(panel_object, dict):
                        st.warning(f"Skipping an item in the panels list as it's not a dictionary: {panel_object}")
                        continue
                    description_raw = panel_object.get("panel_description")
                    if description_raw and isinstance(description_raw, str):
                        cleaned_desc = re.sub(r'^\*\*Panel Description \d+:\*\*\s*\n', '', description_raw, count=1)
                        cleaned_desc = re.sub(r'^\*\s+\*\*(.*?):\*\*', r'\1:', cleaned_desc, flags=re.MULTILINE)
                        cleaned_desc = re.sub(r'^\*\s+', '', cleaned_desc, flags=re.MULTILINE)
                        panel_descriptions.append(cleaned_desc.strip())
                    else:
                        st.warning(f"Panel object is missing 'panel_description' or it's not a string: {panel_object}")
            except json.JSONDecodeError as je:
                st.error(f"JSON Decoding Error: {je}. Please check the raw AI response. Is it valid JSON as per the structure requested?")
                st.text(f"Problematic text (first 500 chars): {prompts_text[:500]}")
            except Exception as e:
                st.error(f"An unexpected error occurred while processing JSON panel descriptions: {e}")
                st.text(traceback.format_exc())
        
        print("Parsed and Cleaned panel_descriptions (from JSON):")
        for i, desc in enumerate(panel_descriptions):
            print(f"--- Panel {i+1} ---"); print(repr(desc)); print("--------------------")

        if not panel_descriptions and prompts_text:
            st.warning("Could not parse any panel descriptions from the JSON response. Check raw AI response and parsing logic.")
        elif not panel_descriptions:
            st.warning("AI returned no text or failed to parse panel descriptions from JSON.")

        if len(panel_descriptions) < num_panels:
            st.warning(f"AI generated or parsed only {len(panel_descriptions)} descriptions from JSON, requested {num_panels}. Adding fallbacks.")
            panel_descriptions.extend([f"Fallback description for panel {i+len(panel_descriptions)+1}. (JSON error or insufficient data)" for i in range(num_panels - len(panel_descriptions))])
        return panel_descriptions[:num_panels]
    except Exception as e:
        st.error(f"Error during initial panel description generation (JSON attempt): {e}")
        st.text(traceback.format_exc())
        return [f"Error (exception) generating panel description {i+1}" for i in range(num_panels)]

def generate_panel_content_multimodal(current_panel_description, conversation_history_for_call, system_prompt_for_multimodal):
    """Generates image and text for a panel using a multimodal AI model."""
    client = get_genai_client()
    if not client:
        return None, "Error: AI Client not initialized for multimodal generation."

    current_request_parts = []

    if st.session_state.get('character_reference_image_gcs_uri') and st.session_state.get('character_reference_image_name'):
        character_context_text = (
            f"IMPORTANT CONTEXT: A visual reference for the character "
            f"'{st.session_state.character_reference_image_name}' is provided below. "
            f"If this character is part of the current panel description, adhere to this reference for their appearance. "
            f"This reference image is a guide; adapt it to the panel's specific action, emotion, and perspective."
        )
        current_request_parts.append(types.Part.from_text(text=character_context_text))
        current_request_parts.append(types.Part.from_uri(
            file_uri=st.session_state.character_reference_image_gcs_uri,
            mime_type=st.session_state.character_reference_image_mime_type
        ))
        current_request_parts.append(types.Part.from_text(text="--- End of Character Reference ---"))

    current_request_parts.append(types.Part.from_text(text=f"Panel Description:\n{current_panel_description}"))
    image_creation_text = (
        "\n\nTask: Based on the above panel description, any provided character reference, "
        "and the overall style guide (provided at the start of our conversation and in previous panels), "
        "generate a single manga panel image and any associated dialogue or sound effects (SFX) text. "
        "Ensure the generated image is consistent with previous panel images in the conversation history for characters and style."
    )
    current_request_parts.append(types.Part.from_text(text=image_creation_text))
    contents_for_api_call = list(conversation_history_for_call)
    contents_for_api_call.append(types.Content(role="user", parts=current_request_parts))
    
    print("=============== Multimodal API Call Contents Setup ===============")
    print(contents_for_api_call)
    print("===================================================================")

    safety_settings = [
        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    ]
    config = types.GenerateContentConfig(
        temperature=0.8,
        top_p=0.95,
        response_modalities=["TEXT", "IMAGE"],
        safety_settings=safety_settings,
        max_output_tokens=8192,
    )

    try:
        st.text("Sending request for multimodal panel content...")
        response = client.models.generate_content(
            model=MULTIMODAL_MODEL_ID,
            contents=contents_for_api_call,
            config=config,
        )

        generated_image_bytes = None
        generated_text_for_panel = "AI did not provide specific text for this panel." # Default

        if response.candidates[0].content.parts:
            first_image = next((part for part in response.candidates[0].content.parts if part.inline_data), None)
            if first_image:
                generated_image_bytes = first_image.inline_data.data
                print(f"Image produced ************************")
            else:
                print("No image data found in the response.")
        else:
            print("No image data found in the response.")

        return generated_image_bytes, generated_text_for_panel

    except Exception as e:
        st.error(f"Error during multimodal content generation for '{current_panel_description[:50]}...': {e}")
        st.text(traceback.format_exc())
        return None, f"Error (exception) during multimodal generation: {e}"

# --- Streamlit UI ---
st.title("📚➡️🖼️ AI Manga Storyboard Generator")
st.caption(f"Using Multimodal: `{MULTIMODAL_MODEL_ID}` and Text: `{TEXT_MODEL_ID_FOR_INITIAL_PROMPTS}`")

# Session state initialization
if 'panel_descriptions' not in st.session_state: st.session_state.panel_descriptions = []
if 'current_panel_idx' not in st.session_state: st.session_state.current_panel_idx = 0
if 'conversation_history' not in st.session_state: st.session_state.conversation_history = []
if 'generated_panel_data' not in st.session_state: st.session_state.generated_panel_data = {}
if 'chapter_content' not in st.session_state: st.session_state.chapter_content = None
if 'uploaded_chapter_name' not in st.session_state: st.session_state.uploaded_chapter_name = None
if 'character_reference_image_bytes' not in st.session_state: st.session_state.character_reference_image_bytes = None # Not strictly needed if always downloading
if 'character_reference_image_name' not in st.session_state: st.session_state.character_reference_image_name = ""
if 'character_reference_image_gcs_uri' not in st.session_state: st.session_state.character_reference_image_gcs_uri = None
if 'character_reference_image_mime_type' not in st.session_state: st.session_state.character_reference_image_mime_type = None

with st.sidebar:
    st.header("⚙️ Configuration")
    uploaded_chapter = st.file_uploader("1. Upload Chapter (PDF or TXT)", type=["pdf", "txt"], key="chapter_uploader")
    
    st.info(gcs_connection_message)
    if gcs_client_initialized and gcs_bucket_initialized: # Check if default bucket object is fine
        st.text_input("GCS Bucket for Saves (auto-configured):", value=GCS_BUCKET_NAME, disabled=True)
    elif gcs_client_initialized:
         st.text_input("GCS Bucket for Saves (default not found/accessible):", value=GCS_BUCKET_NAME, disabled=True)
         st.warning(f"App will still attempt to save to '{GCS_BUCKET_NAME}'. Ensure it exists and has permissions.")
    else:
        st.warning(f"GCS Client not initialized. Image saving to GCS will be disabled.")

    st.divider()
    st.subheader("🎨 Character Reference (Optional)")
    char_ref_name_input_val = st.session_state.get('character_reference_image_name', "")
    char_ref_name = st.text_input("Character Name for Reference:", 
                                  value=char_ref_name_input_val, 
                                  key="char_ref_name_input")
    char_ref_image_upload = st.file_uploader("Upload Character Reference Image:", 
                                             type=["png", "jpg", "jpeg"], 
                                             key="char_ref_uploader")

    col_set, col_clear = st.columns(2)
    with col_set:
        if st.button("Set Character Reference", key="set_char_ref_button"):
            # Update char_ref_name from text input immediately before processing
            st.session_state.character_reference_image_name = char_ref_name 
            if char_ref_image_upload and st.session_state.character_reference_image_name:
                with st.spinner("Uploading character reference image..."):
                    image_bytes = char_ref_image_upload.getvalue()
                    mime_type = char_ref_image_upload.type
                    gcs_uri = save_image_to_gcs(image_bytes, 
                                                file_name_prefix=f"character_ref_{st.session_state.character_reference_image_name.replace(' ', '_')}",
                                                mime_type=mime_type)
                    if gcs_uri:
                        st.session_state.character_reference_image_gcs_uri = gcs_uri
                        # Name already set from input field to session_state
                        st.session_state.character_reference_image_mime_type = mime_type
                        st.success(f"Character reference '{st.session_state.character_reference_image_name}' set.")
                        st.rerun() 
                    else:
                        st.error("Failed to save character reference image to GCS.")
            elif not char_ref_image_upload:
                st.warning("Please upload an image for the character reference.")
            elif not st.session_state.character_reference_image_name: # Check updated session state name
                st.warning("Please enter a name for the character reference.")
    with col_clear:
        if st.button("Clear Reference", key="clear_char_ref_button"):
            st.session_state.character_reference_image_gcs_uri = None
            st.session_state.character_reference_image_name = ""
            st.session_state.character_reference_image_mime_type = None
            st.info("Character reference cleared.")
            st.rerun()

    if st.session_state.character_reference_image_gcs_uri:
        st.success(f"Active Reference: '{st.session_state.character_reference_image_name}'")
        # MODIFIED PART TO DOWNLOAD IMAGE FOR DISPLAY
        ref_image_bytes = get_image_bytes_from_gcs(st.session_state.character_reference_image_gcs_uri)
        if ref_image_bytes:
            st.image(ref_image_bytes, caption=f"Reference for {st.session_state.character_reference_image_name}", use_container_width=True)
        else:
            st.warning(f"Could not load reference image from GCS: {st.session_state.character_reference_image_gcs_uri}")
    
    st.divider()

    num_panels = st.slider("Number of Panels to Generate", 5, 40, 10, key="num_panels_slider")
    
    default_sys_prompt = """You are an AI text processing assistant. Your task is to break down a chapter of a story into a series of detailed descriptions for manga panels.
Focus on visual storytelling, character emotions, key actions, and setting details.
The output must be a JSON object as specified in the instructions.
Example of a panel description structure:
**Panel Description [Number]:**
* **Scene:** A dimly lit, narrow alleyway at night. Rain is falling, creating puddles that reflect the neon signs from a nearby street.
* **Characters:** Damian, soaked and shivering, is cornered. The Monstrous Instructor looms over them.
* **Action:** Damian attempts to dodge a strike from the Instructor.
* **Emotion:** Damian shows fear and desperation. The Instructor shows cold fury.
* **Dialogue:**  Damien: "Not yet!"
"""
    system_prompt = st.text_area("System Prompt for Initial Panel Descriptions (Text Model)", value=default_sys_prompt, height=250, key="system_prompt_text_area")

    default_panel_prompt = """You are an AI multimodal assistant creating sequential art for manga.
Style and mood to be determined by the input text and character images provided.

Character Consistency is CRUCIAL:

IMPORTANT CONTEXTUAL INFORMATION:
1.  CHARACTER REFERENCE IMAGE: A specific character reference image (and name) might be provided before the panel description in the user's message. If so, YOU MUST use that image as the primary visual guide for that named character's appearance in the current panel, adapting it to the panel's specific action, emotion, and perspective.
2.  PREVIOUS PANELS: Refer to previously generated panel images (which will be part of our conversation history) to maintain consistency in character appearance (for characters not covered by a specific reference image), art style, and scene continuity.

For each user prompt (which is a panel description, possibly accompanied by a character reference image):
1.  Generate ONE compelling manga panel image that visually represents the description and adheres to the overall style, character references, and previous panels.
2.  Ensure that faces are complete and images are consistent.
3.  Provide any dialogue text as part of this panel, based on the description. This text should be part of the image in the comic book style.

Your output should consist of the generated image.
"""
    panel_prompt = st.text_area("System Prompt for Panel Generation (Multimodal Model)", value=default_panel_prompt, height=400, key="panel_prompt_text_area")

# Main application logic
if uploaded_chapter:
    if st.session_state.get('uploaded_chapter_name') != uploaded_chapter.name:
        st.info(f"Processing uploaded file: {uploaded_chapter.name}...")
        if uploaded_chapter.type == "application/pdf":
            st.session_state.chapter_content = extract_text_from_pdf(uploaded_chapter)
        elif uploaded_chapter.type == "text/plain":
            st.session_state.chapter_content = uploaded_chapter.getvalue().decode("utf-8")
        else:
            st.session_state.chapter_content = "Error: Unsupported file type."

        st.session_state.uploaded_chapter_name = uploaded_chapter.name
        st.session_state.panel_descriptions = []
        st.session_state.current_panel_idx = 0
        st.session_state.generated_panel_data = {}
        st.session_state.conversation_history = [
            types.Content(role="user", parts=[types.Part.from_text(text=panel_prompt)])
        ]
        st.success(f"Chapter '{uploaded_chapter.name}' processed.")
        st.rerun() 

    if st.session_state.chapter_content and not st.session_state.chapter_content.startswith("Error:"):
        st.subheader(f"📖 Chapter: {st.session_state.uploaded_chapter_name}")

        if not st.session_state.panel_descriptions:
            if st.button("📝 Generate Initial Panel Descriptions", key="generate_desc_button"):
                with st.spinner("AI is crafting panel descriptions... this may take a moment."):
                    st.session_state.panel_descriptions = generate_initial_panel_descriptions(
                        st.session_state.chapter_content,
                        system_prompt,
                        num_panels
                    )
                st.rerun()
        
        if st.session_state.panel_descriptions:
            current_idx = st.session_state.current_panel_idx
            
            if not (0 <= current_idx < len(st.session_state.panel_descriptions)):
                st.warning("Panel index out of bounds. Resetting to first panel.")
                st.session_state.current_panel_idx = 0
                current_idx = 0
                if not st.session_state.panel_descriptions: 
                    st.stop()

            current_desc = st.session_state.panel_descriptions[current_idx]
            st.header(f"🎨 Panel {current_idx + 1} of {len(st.session_state.panel_descriptions)}")
            st.markdown(f"**Panel Description:**\n\n```\n{current_desc}\n```")

            if current_idx not in st.session_state.generated_panel_data:
                if st.button(f"✨ Generate Image & Text for Panel {current_idx + 1}", key=f"generate_content_button_{current_idx}"):
                    with st.spinner(f"AI is generating content for panel {current_idx + 1}... please wait."):
                        temp_call_history = []
                        if st.session_state.conversation_history:
                             temp_call_history.append(st.session_state.conversation_history[0])

                        history_end_index = 1 + (current_idx * 2)
                        if len(st.session_state.conversation_history) > 1:
                             temp_call_history.extend(st.session_state.conversation_history[1:history_end_index])

                        image_bytes, panel_text = generate_panel_content_multimodal(
                            current_desc, 
                            temp_call_history,
                            panel_prompt
                        )
                        
                        gcs_uri_result = None
                        if image_bytes and storage_client: # Check storage_client here
                            # Assuming 'image/png' from model, can be refined if model specifies mime_type
                            image_mime_type_from_model = 'image/png' 
                            # Try to get mime_type from response if available, e.g. response.candidates[0].content.parts[img_idx].mime_type

                            gcs_uri_result = save_image_to_gcs(
                                image_bytes, 
                                f"panel_image_{current_idx+1}", 
                                mime_type=image_mime_type_from_model # Pass mime_type
                            )
                        
                        st.session_state.generated_panel_data[current_idx] = {
                            'description': current_desc,
                            'text': panel_text,
                            'gcs_uri': gcs_uri_result,
                            'image_bytes': image_bytes 
                        }

                        current_request_parts_for_history = []
                        if st.session_state.get('character_reference_image_gcs_uri') and st.session_state.get('character_reference_image_name'):
                            char_hist_text = f"[Ctx: Ref img for '{st.session_state.character_reference_image_name}' was provided: {st.session_state.character_reference_image_gcs_uri}]"
                            current_request_parts_for_history.append(types.Part.from_text(text=char_hist_text))
                        current_request_parts_for_history.append(types.Part.from_text(text=current_desc))
                        image_creation_hist_text = ( "\n\nTask: Based on the above panel description, any provided character reference, "
                                                     "and the overall style guide (provided at the start of our conversation and in previous panels), "
                                                     "generate a single manga panel image and any associated dialogue or sound effects (SFX) text. "
                                                     "Ensure the generated image is consistent with previous panel images in the conversation history for characters and style.")
                        current_request_parts_for_history.append(types.Part.from_text(text=image_creation_hist_text))
                        st.session_state.conversation_history.append(types.Content(role="user", parts=current_request_parts_for_history))
                        
                        model_response_parts_for_main_history = []
                        # Determine mime type of the generated image for GCS URI part
                        panel_image_mime_type = 'image/png' # Default if not found
 #                       if image_bytes and response.candidates and response.candidates[0].content.parts:
  #                          for part in response.candidates[0].content.parts:
   #                             if part.mime_type and part.mime_type.startswith("image/"):
    #                                panel_image_mime_type = part.mime_type
     #                               break
                        
                        if gcs_uri_result:
                            model_response_parts_for_main_history.append(types.Part.from_uri(file_uri=gcs_uri_result, mime_type=panel_image_mime_type))
                        elif image_bytes:
                             model_response_parts_for_main_history.append(types.Part.from_data(data=image_bytes, mime_type=panel_image_mime_type))

                        if panel_text:
                            model_response_parts_for_main_history.append(types.Part.from_text(text=panel_text))
                        
                        if model_response_parts_for_main_history:
                            st.session_state.conversation_history.append(types.Content(role="model", parts=model_response_parts_for_main_history))
                        else: 
                            st.session_state.conversation_history.append(types.Content(role="model", parts=[types.Part.from_text(text="[No image or text content generated for this panel turn or GCS save failed]")]))
                        
                        st.rerun()

            if current_idx in st.session_state.generated_panel_data:
                data = st.session_state.generated_panel_data[current_idx]
                if data.get('image_bytes'):
                    st.image(data['image_bytes'], caption=f"Generated Panel {current_idx + 1}", use_container_width=True)
                else:
                    st.warning(f"No image was generated or extracted for Panel {current_idx + 1}.")
                
                if data.get('text'):
                    st.markdown(f"**AI Generated Text/Dialogue:**\n```\n{data['text']}\n```")
                else:
                    st.markdown("**AI Generated Text/Dialogue:** (No text provided by AI for this panel)")

                if data.get('gcs_uri'):
                    st.caption(f"Image stored at GCS: {data['gcs_uri']}")
                elif data.get('image_bytes') and storage_client: # Check storage_client
                    st.warning("Image was generated but may have failed to save to GCS.")
            
            col_prev, col_next = st.columns(2)
            with col_prev:
                if st.button("⬅️ Previous Panel", key=f"prev_panel_{current_idx}", disabled=(current_idx == 0)):
                    st.session_state.current_panel_idx -= 1
                    st.rerun()
            with col_next:
                next_disabled = (current_idx >= len(st.session_state.panel_descriptions) - 1) or \
                                (current_idx not in st.session_state.generated_panel_data)
                if st.button("Next Panel ➡️", key=f"next_panel_{current_idx}", disabled=next_disabled):
                    st.session_state.current_panel_idx += 1
                    st.rerun()

        if st.session_state.panel_descriptions and \
           len(st.session_state.generated_panel_data) == len(st.session_state.panel_descriptions) and \
           len(st.session_state.panel_descriptions) > 0:
            st.divider()
            st.header("🎉 Storyboard Complete! 🎉")
            st.balloons()
            
            num_cols_final = st.slider("Panels per row in final display:", 2, 5, 3, key="final_display_cols_slider")
            num_total_panels = len(st.session_state.panel_descriptions)
            for i in range(0, num_total_panels, num_cols_final):
                cols = st.columns(num_cols_final)
                for j in range(num_cols_final):
                    panel_index = i + j
                    if panel_index < num_total_panels:
                        with cols[j]:
                            panel_to_display = st.session_state.generated_panel_data.get(panel_index)
                            if panel_to_display:
                                st.subheader(f"Panel {panel_index+1}")
                                if panel_to_display.get('image_bytes'):
                                    st.image(panel_to_display['image_bytes'], use_container_width=True)
                                if panel_to_display.get('text'):
                                    st.caption(f"Text: {panel_to_display['text']}")
                                if panel_to_display.get('gcs_uri'):
                                    st.caption(f"GCS: {panel_to_display['gcs_uri']}")
                            else:
                                st.warning(f"Data for Panel {panel_index+1} is missing in the final display.")
                                
    elif st.session_state.chapter_content and st.session_state.chapter_content.startswith("Error:"):
        st.error(st.session_state.chapter_content)

else:
    st.info("👋 Welcome! Please upload a chapter document (PDF or TXT) to begin generating your manga storyboard.")

st.sidebar.markdown("---")
st.sidebar.info(f"Current Date (Server): {datetime.datetime.now().date()}")