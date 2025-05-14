"""Service for interacting with Google's AI models."""

from typing import List, Optional, Tuple
from google import genai
from google.genai import types
from config.settings import GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, MULTIMODAL_MODEL_ID, TEXT_MODEL_ID
import traceback
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from google.auth import default

class AIService:
    """Service for interacting with Google's AI models."""
    
    def __init__(self):
        """Initialize the AI service."""
        print("Initializing AI service...")
        try:
            # Get default credentials for Vertex AI
            credentials, project = default()
            if not project:
                project = GOOGLE_CLOUD_PROJECT
                
            # Initialize the client
            self.client = genai.Client(
                project=project,
                location=GOOGLE_CLOUD_LOCATION,
                credentials=credentials,
                vertexai=True
            )
            
            # Configure safety settings
            self.safety_settings = [
                types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
            ]
            
            # Create a thread pool for parallel operations
            self.executor = ThreadPoolExecutor(max_workers=3)
            
        except Exception as e:
            error_msg = str(e)
            if "Could not automatically determine credentials" in error_msg:
                raise ValueError(
                    "Could not find Google Cloud credentials. Please ensure you have:\n"
                    "1. Google Cloud SDK installed and configured\n"
                    "2. Run 'gcloud auth application-default login' if running locally\n"
                    "3. Proper service account credentials if running in production"
                )
            elif "Permission denied" in error_msg:
                raise ValueError(
                    "Permission denied accessing Vertex AI. Please ensure:\n"
                    "1. Your account has the necessary Vertex AI permissions\n"
                    "2. The project has Vertex AI API enabled\n"
                    "3. You're using the correct project ID"
                )
            else:
                raise ValueError(f"Failed to initialize AI client: {error_msg}")

    def _extract_character_names(self, panel_description: str) -> List[str]:
        """Extract character names mentioned in the panel description."""
        # Convert to lowercase for case-insensitive matching
        desc_lower = panel_description.lower()
        
        # Common words to exclude
        exclude_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'from'}
        
        # Split into words and clean
        words = [word.strip('.,!?()[]{}":;') for word in desc_lower.split()]
        words = [word for word in words if word and word not in exclude_words]
        
        # Look for character names (words that start with capital letters in the original text)
        character_names = []
        for word in panel_description.split():
            clean_word = word.strip('.,!?()[]{}":;')
            if clean_word and clean_word[0].isupper() and clean_word.lower() not in exclude_words:
                character_names.append(clean_word)
        
        return list(set(character_names))  # Remove duplicates

    def generate_panel_descriptions(self, 
                                  chapter_text: str, 
                                  system_prompt: str, 
                                  num_panels: int,
                                  character_context: Optional[str] = None,
                                  background_context: Optional[str] = None) -> List[str]:
        """Generate panel descriptions from chapter text, chunking requests if needed and using sequential text chunks for continuity."""
        print(f"\n=== Starting Panel Description Generation ===")
        print(f"Number of panels requested: {num_panels}")
        print(f"Character context provided: {bool(character_context)}")
        print(f"Background context provided: {bool(background_context)}")
        
        # Validate input
        if not chapter_text.strip():
            print("Error: Empty chapter text")
            raise ValueError("Chapter text cannot be empty")
        
        max_panels_per_chunk = 10
        all_panel_descriptions = []
        panels_remaining = num_panels
        chunk_idx = 0
        # Split the chapter text into sequential chunks for each batch
        num_chunks = (num_panels + max_panels_per_chunk - 1) // max_panels_per_chunk
        text_length = len(chapter_text)
        chunk_size = text_length // num_chunks if num_chunks > 0 else text_length
        text_chunks = [chapter_text[i*chunk_size:(i+1)*chunk_size] for i in range(num_chunks)]
        print(f"Splitting chapter text into {len(text_chunks)} sequential chunks for {num_chunks} panel batches.")
        
        for chunk_idx, text_chunk in enumerate(text_chunks):
            panels_in_this_chunk = min(max_panels_per_chunk, panels_remaining)
            print(f"\n--- Processing Panel Chunk {chunk_idx+1}/{len(text_chunks)} ({panels_in_this_chunk} panels) ---")
            print(f"Text chunk length: {len(text_chunk)}")
            # STRONGER SYSTEM PROMPT
            strict_json_instruction = (
                "IMPORTANT: Respond ONLY with a valid JSON object as described below. "
                "Do NOT include any explanation, thoughts, or extra text. "
                "Your entire response must be a single JSON object with exactly one key: 'response'. "
                "The value for 'response' must be a JSON string containing an array of panel objects. "
                "Each panel object must have exactly two keys: 'panel_description' and 'dialogue_sfx'. "
                "Do not include any preamble, explanation, or commentary. Only output the JSON object.\n"
            )
            instruction = (
                f"System Prompt:\n{system_prompt}\n\n"
                f"{strict_json_instruction}"
            )
            if character_context:
                instruction += f"Character Context:\n{character_context}\n\n"
            if background_context:
                instruction += f"Background Context:\n{background_context}\n\n"
            instruction += (
                f"Chapter Text (Part {chunk_idx+1} of {len(text_chunks)}):\n\"\"\"{text_chunk}\"\"\"\n\n"
                f"Based on this part of the chapter text and system prompt, generate {panels_in_this_chunk} detailed text descriptions for sequential manga panels. "
                "Each description will serve as a prompt for a multimodal AI to generate an image and accompanying text (dialogue/SFX). "
                "For each panel, focus on: Scene (setting, mood), Characters (appearance, position, expression), Action (what's happening), Emotion (conveyed by characters/scene), "
                "and any key Dialogue or Sound Effects (SFX) that should be explicitly part of the panel's text. "
                "IMPORTANT: Your response MUST be a valid JSON object with exactly one key 'response'. "
                "The value for 'response' must be a JSON string containing an array of panel objects. "
                "Each panel object must have exactly two keys: 'panel_description' and 'dialogue_sfx'. "
                "The panel_description should be a string starting with '**Panel Description [Number]:**\\n' followed by bullet points. "
                "The dialogue_sfx should be a string containing only the dialogue or SFX for that panel. "
                "Make sure all strings are properly escaped and the JSON is valid."
            )
            print(f"Instruction length: {len(instruction)} characters")
            print("Sending request to AI model...")
            config = types.GenerateContentConfig(
                temperature=0.6,
                top_p=0.95,
                max_output_tokens=8192,
                response_modalities=["TEXT"],
                safety_settings=self.safety_settings,
                response_mime_type="application/json",
                response_schema={"type":"OBJECT","properties":{"response":{"type":"STRING"}}}
            )
            try:
                full_response = ""
                for chunk_resp in self.client.models.generate_content_stream(
                    model=TEXT_MODEL_ID,
                    contents=[types.Content(role="user", parts=[types.Part.from_text(text=instruction)])],
                    config=config,
                ):
                    if chunk_resp.text:
                        full_response += chunk_resp.text
                if not full_response:
                    print("Error: Empty response from model")
                    raise Exception("Empty response received from AI model")
                print(f"\nRaw AI response for panel chunk {chunk_idx+1}:")
                print(f"Response length: {len(full_response)} characters")
                print(f"Response preview: {full_response[:200]}...")
                # Try to parse as JSON
                try:
                    outer_data = json.loads(full_response)
                except Exception as e:
                    print(f"Initial JSON decode error: {str(e)}")
                    print(f"Problematic text: {full_response[:200]}...")
                    # IMPROVED FALLBACK: Try to extract as many panel descriptions as possible
                    panel_descriptions = []
                    current_panel = []
                    in_panel = False
                    for line in full_response.split('\n'):
                        line = line.strip()
                        if '**Panel Description' in line:
                            if current_panel:
                                panel_descriptions.append('\n'.join(current_panel))
                            current_panel = [line]
                            in_panel = True
                        elif in_panel and line:
                            current_panel.append(line)
                    if current_panel:
                        panel_descriptions.append('\n'.join(current_panel))
                    if panel_descriptions:
                        print(f"Extracted {len(panel_descriptions)} panel descriptions from text (fallback mode)")
                        all_panel_descriptions.extend(panel_descriptions)
                        panels_remaining -= len(panel_descriptions)
                        continue
                    else:
                        print("No valid panel descriptions could be extracted from fallback mode.")
                        continue
                # Parse the inner JSON string from the response with improved validation
                inner_json_string = outer_data.get("response", "")
                if not inner_json_string:
                    print("No 'response' key found in JSON")
                    continue
                try:
                    inner_json_string = inner_json_string.strip()
                    if inner_json_string.startswith('[') and inner_json_string.endswith(']'):
                        panels_list = json.loads(inner_json_string)
                    else:
                        inner_json_string = inner_json_string.replace('\\"', '"')
                        inner_json_string = inner_json_string.replace('""', '"')
                        panels_list = json.loads(inner_json_string)
                    print(f"Successfully parsed inner JSON array with {len(panels_list)} panels")
                except json.JSONDecodeError as je:
                    print(f"JSON decode error for inner array: {je}")
                    print(f"Problematic inner JSON: {inner_json_string[:200]}...")
                    continue
                if not isinstance(panels_list, list):
                    print(f"Expected list of panels, got {type(panels_list)}")
                    continue
                print(f"Found {len(panels_list)} panels in response")
                for panel_object in panels_list:
                    if not isinstance(panel_object, dict):
                        print(f"Skipping invalid panel object: {panel_object}")
                        continue
                    description_raw = panel_object.get("panel_description", "")
                    if not description_raw:
                        print(f"Panel object missing description: {panel_object}")
                        continue
                    cleaned_desc = description_raw.replace("**Panel Description [Number]:**\n", "")
                    cleaned_desc = cleaned_desc.replace("* **", "").replace(":**", ":")
                    cleaned_desc = cleaned_desc.replace("* ", "")
                    all_panel_descriptions.append(cleaned_desc.strip())
                print(f"Successfully processed {len(all_panel_descriptions)} panels so far")
                panels_remaining -= len(panels_list)
            except Exception as e:
                print(f"Error processing panel chunk {chunk_idx+1}: {str(e)}")
                print(f"Full traceback: {traceback.format_exc()}")
                if not all_panel_descriptions:  # Only raise if we have no descriptions at all
                    raise Exception(f"Error generating panel descriptions: {str(e)}")
                else:
                    print(f"Continuing with {len(all_panel_descriptions)} panels generated so far")
                    panels_remaining -= panels_in_this_chunk  # Assume chunk failed, move on
        if not all_panel_descriptions:
            print("No valid panel descriptions were generated from any chunk")
            raise Exception("No valid panel descriptions were generated from any chunk")
        print(f"\n=== Panel Description Generation Complete ===")
        print(f"Total panels generated: {len(all_panel_descriptions)}")
        return all_panel_descriptions[:num_panels]

    async def generate_panel_variants_async(self,
                                          panel_description: str,
                                          character_references: List[Tuple[str, str]],
                                          background_references: List[Tuple[str, str]],
                                          num_variants: int,
                                          system_prompt: str,
                                          temperature: float = 0.7,
                                          additional_instructions: str = "",
                                          previous_panel_image: Optional[Tuple[bytes, str]] = None) -> List[Tuple[bytes, str]]:
        """Generate multiple variants of a panel image asynchronously."""
        current_request_parts = []
        max_retries = 3
        retry_delay = 1  # seconds
        
        # Extract character names from the panel description
        mentioned_characters = self._extract_character_names(panel_description)
        print(f"Characters mentioned in panel: {mentioned_characters}")
        
        # Filter character references to only include mentioned characters
        relevant_char_refs = [
            (char_name, char_uri) for char_name, char_uri in character_references
            if any(mentioned_char.lower() in char_name.lower() for mentioned_char in mentioned_characters)
        ]
        print(f"Relevant character references: {[name for name, _ in relevant_char_refs]}")
        
        # Add character references
        for char_name, char_uri in relevant_char_refs:
            char_context = (
                f"IMPORTANT CONTEXT: A visual reference for the character '{char_name}' "
                f"is provided below. If this character is part of the current panel description, "
                f"adhere to this reference for their appearance. "
                f"This reference image is a guide; adapt it to the panel's specific action, emotion, and perspective."
            )
            current_request_parts.append(types.Part.from_text(text=char_context))
            current_request_parts.append(types.Part.from_uri(file_uri=char_uri, mime_type="image/png"))
        
        # Add background references
        for bg_name, bg_uri in background_references:
            bg_context = (
                f"IMPORTANT CONTEXT: A visual reference for the background '{bg_name}' "
                f"is provided below. If this background is part of the current panel description, "
                f"adhere to this reference for its appearance. "
                f"This reference image is a guide; adapt it to the panel's specific lighting, mood, and perspective."
            )
            current_request_parts.append(types.Part.from_text(text=bg_context))
            current_request_parts.append(types.Part.from_uri(file_uri=bg_uri, mime_type="image/png"))
        
        # Add previous panel image if available
        if previous_panel_image:
            prev_image, prev_text = previous_panel_image
            current_request_parts.append(types.Part.from_text(text=(
                "IMPORTANT CONTEXT: The previous panel in the sequence is provided below. "
                "Maintain visual continuity with this panel, including character appearances, "
                "art style, and scene progression. The new panel should feel like a natural "
                "continuation of the story."
            )))
            current_request_parts.append(types.Part(inline_data=types.Blob(
                data=prev_image,
                mime_type="image/png"
            )))
            current_request_parts.append(types.Part.from_text(text=f"Previous Panel Context: {prev_text}"))
        
        # Add the panel description
        current_request_parts.append(types.Part.from_text(text=panel_description))
        
        # Add additional instructions if provided
        if additional_instructions:
            current_request_parts.append(types.Part.from_text(text=f"\nAdditional Instructions:\n{additional_instructions}"))
        
        async def generate_single_variant():
            """Generate a single variant with retry logic."""
            for attempt in range(max_retries):
                try:
                    response = await asyncio.get_event_loop().run_in_executor(
                        self.executor,
                        lambda: self.client.models.generate_content(
                            model=MULTIMODAL_MODEL_ID,
                            contents=[types.Content(role="user", parts=current_request_parts)],
                            config=types.GenerateContentConfig(
                                temperature=temperature,
                                top_p=0.95,
                                max_output_tokens=8192,
                                response_modalities=["TEXT", "IMAGE"],
                                safety_settings=self.safety_settings
                            )
                        )
                    )
                    
                    if not response or not response.candidates:
                        raise Exception("Empty response from model")
                        
                    candidate = response.candidates[0]
                    if not candidate.content or not candidate.content.parts:
                        raise Exception("No content in response candidate")
                        
                    image_data = None
                    text_data = None
                    
                    for part in candidate.content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            image_data = part.inline_data.data
                        elif hasattr(part, 'text') and part.text:
                            text_data = part.text
                            
                    if not image_data:
                        raise Exception("No image data in response")
                    if not text_data:
                        raise Exception("No text data in response")
                        
                    return (image_data, text_data)
                    
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    else:
                        raise Exception(f"Failed to generate variant after {max_retries} attempts: {str(e)}")
        
        # Generate variants in parallel with a limit on concurrent requests
        max_concurrent = min(num_variants, 3)  # Limit concurrent requests
        successful_results = []
        remaining_variants = num_variants
        
        while remaining_variants > 0:
            current_batch = min(max_concurrent, remaining_variants)
            tasks = [generate_single_variant() for _ in range(current_batch)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    print(f"Failed to generate variant: {str(result)}")
                else:
                    successful_results.append(result)
                    
            remaining_variants -= current_batch
            
            if remaining_variants > 0:
                await asyncio.sleep(1)  # Brief pause between batches
                
        if not successful_results:
            raise Exception("Failed to generate any valid variants")
            
        return successful_results

    async def generate_final_variants_async(self,
                                          panel_description: str,
                                          selected_variant: Tuple[bytes, str],
                                          character_references: List[Tuple[str, str]],
                                          background_references: List[Tuple[str, str]],
                                          num_variants: int,
                                          temperature: float = 0.7,
                                          additional_instructions: str = "") -> List[Tuple[bytes, str]]:
        """Generate final variants of a panel image asynchronously."""
        current_request_parts = []
        max_retries = 3
        retry_delay = 1  # seconds
        
        # Add character references
        for char_name, char_uri in character_references:
            char_context = (
                f"IMPORTANT CONTEXT: A visual reference for the character '{char_name}' "
                f"is provided below. If this character is part of the current panel description, "
                f"adhere to this reference for their appearance. "
                f"This reference image is a guide; adapt it to the panel's specific action, emotion, and perspective."
            )
            current_request_parts.append(types.Part.from_text(text=char_context))
            current_request_parts.append(types.Part.from_uri(file_uri=char_uri, mime_type="image/png"))
            
        # Add background references
        for bg_name, bg_uri in background_references:
            bg_context = (
                f"IMPORTANT CONTEXT: A visual reference for the background '{bg_name}' "
                f"is provided below. If this background is part of the current panel description, "
                f"adhere to this reference for its appearance. "
                f"This reference image is a guide; adapt it to the panel's specific lighting, mood, and perspective."
            )
            current_request_parts.append(types.Part.from_text(text=bg_context))
            current_request_parts.append(types.Part.from_uri(file_uri=bg_uri, mime_type="image/png"))
            
        # Add the selected variant as reference
        selected_image, selected_text = selected_variant
        current_request_parts.append(types.Part.from_text(text="Selected Variant Reference:"))
        current_request_parts.append(types.Part(inline_data=types.Blob(
            data=selected_image,
            mime_type="image/png"
        )))
        current_request_parts.append(types.Part.from_text(text=f"Reference Text: {selected_text}"))
        
        # Add the panel description
        current_request_parts.append(types.Part.from_text(text=panel_description))
        
        # Add additional instructions if provided
        if additional_instructions:
            current_request_parts.append(types.Part.from_text(text=f"\nAdditional Instructions:\n{additional_instructions}"))
        
        async def generate_single_variant():
            """Generate a single variant with retry logic."""
            for attempt in range(max_retries):
                try:
                    response = await asyncio.get_event_loop().run_in_executor(
                        self.executor,
                        lambda: self.client.models.generate_content(
                            model=MULTIMODAL_MODEL_ID,
                            contents=[types.Content(role="user", parts=current_request_parts)],
                            config=types.GenerateContentConfig(
                                temperature=temperature,
                                top_p=0.95,
                                max_output_tokens=8192,
                                response_modalities=["TEXT", "IMAGE"],
                                safety_settings=self.safety_settings
                            )
                        )
                    )
                    
                    if not response or not response.candidates:
                        raise Exception("Empty response from model")
                        
                    candidate = response.candidates[0]
                    if not candidate.content or not candidate.content.parts:
                        raise Exception("No content in response candidate")
                        
                    image_data = None
                    text_data = None
                    
                    for part in candidate.content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            image_data = part.inline_data.data
                        elif hasattr(part, 'text') and part.text:
                            text_data = part.text
                            
                    if not image_data:
                        raise Exception("No image data in response")
                    if not text_data:
                        raise Exception("No text data in response")
                        
                    return (image_data, text_data)
                    
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    else:
                        raise Exception(f"Failed to generate variant after {max_retries} attempts: {str(e)}")
        
        # Generate variants in parallel with a limit on concurrent requests
        max_concurrent = min(num_variants, 3)  # Limit concurrent requests
        successful_results = []
        remaining_variants = num_variants
        
        while remaining_variants > 0:
            current_batch = min(max_concurrent, remaining_variants)
            tasks = [generate_single_variant() for _ in range(current_batch)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    print(f"Failed to generate variant: {str(result)}")
                else:
                    successful_results.append(result)
                    
            remaining_variants -= current_batch
            
            if remaining_variants > 0:
                await asyncio.sleep(1)  # Brief pause between batches
                
        if not successful_results:
            raise Exception("Failed to generate any valid variants")
            
        return successful_results

    # Keep the existing synchronous methods for backward compatibility
    def generate_panel_variants(self, *args, **kwargs):
        """Synchronous wrapper for generate_panel_variants_async."""
        return asyncio.run(self.generate_panel_variants_async(*args, **kwargs))

    def generate_final_variants(self, *args, **kwargs):
        """Synchronous wrapper for generate_final_variants_async."""
        return asyncio.run(self.generate_final_variants_async(*args, **kwargs)) 