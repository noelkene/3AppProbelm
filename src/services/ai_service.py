"""Service for interacting with Google's AI models using google-genai SDK."""

from typing import List, Optional, Tuple, Dict
from google import genai
from google.genai import types
from src.config.settings import GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, MULTIMODAL_MODEL_ID, TEXT_MODEL_ID, DEFAULT_IMAGE_TEMPERATURE
import traceback
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from google.auth import default
import os
import base64
from io import BytesIO
import time
import re

class AIService:
    """Service for interacting with Google's AI models using google-genai SDK."""
    
    def __init__(self):
        """Initialize the AI service."""
        print("Initializing AI service...")
        try:
            # Get default credentials for Google Cloud
            credentials, project = default()
            if not project:
                project = GOOGLE_CLOUD_PROJECT
            
            # Initialize the GenAI client
            self.client = genai.Client(
                credentials=credentials,
                project=project,
                location="global",  # Using global for Gemini models
                vertexai=True  # Use Vertex AI
            )
            
            # Configure safety settings - turn off for creative content
            self.safety_settings = [
                types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
            ]
            
            # Create a thread pool for parallel operations
            self.executor = ThreadPoolExecutor(max_workers=3)
            
            print(f"AI service initialized successfully:")
            print(f"- Project: {project}")
            print(f"- Text model: {TEXT_MODEL_ID}")
            print(f"- Multimodal model: {MULTIMODAL_MODEL_ID}")
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error initializing AI service: {error_msg}")
            raise ValueError(f"Failed to initialize AI client: {error_msg}")

    def _extract_character_names(self, panel_description: str, known_character_names: List[str]) -> List[str]:
        """Extract known character names mentioned in the panel description using whole word matching."""
        mentioned_characters = []
        desc_lower = panel_description.lower()
        
        for char_name in known_character_names:
            if not char_name or not char_name.strip(): # Skip empty or whitespace-only names
                continue
            try:
                # Use regex for whole word, case-insensitive matching.
                # re.escape handles any special regex characters in char_name.
                pattern = r"\b" + re.escape(char_name.lower()) + r"\b"
                if re.search(pattern, desc_lower):
                    mentioned_characters.append(char_name) # Keep original casing
            except re.error as e:
                print(f"[AIService._extract_character_names] Regex error for character name '{char_name}': {e}. Skipping this name.")
        
        return list(set(mentioned_characters))

    def generate_panel_descriptions(self,
                                  chapter_text: str,
                                  system_prompt: str,
                                  num_panels: int,
                                  character_context: Optional[str] = None,
                                  background_context: Optional[str] = None,
                                  batch_size: int = 10) -> List[Dict[str, str]]:
        """
        Generate panel descriptions from chapter text, chunking requests if needed.
        Each panel will have a brief_description, visual_description, and source_text_segment.
        """
        print(f"\n=== Starting Comprehensive Panel Description Generation ===")
        print(f"Number of panels requested: {num_panels}")
        print(f"Batch size: {batch_size}")

        if not chapter_text.strip():
            print("Error: Empty chapter text")
            raise ValueError("Chapter text cannot be empty")

        all_panel_data = [] # This will store list of dicts, each dict is a panel's data
        panels_generated_count = 0

        num_chunks = (num_panels + batch_size - 1) // batch_size
        
        # Simple text splitting per chunk.
        # A more sophisticated method might be needed for better context per chunk.
        words = chapter_text.split()
        total_words = len(words)
        words_per_chunk = total_words // num_chunks if num_chunks > 0 else total_words
        
        text_chunks_for_prompting = []
        if num_chunks > 0:
            for i in range(num_chunks):
                start_word_idx = i * words_per_chunk
                end_word_idx = (i + 1) * words_per_chunk if i < num_chunks -1 else total_words
                text_chunks_for_prompting.append(" ".join(words[start_word_idx:end_word_idx]))
        elif total_words > 0 : # Single chunk if num_panels <= batch_size
             text_chunks_for_prompting.append(chapter_text)
        else: # No text
            text_chunks_for_prompting.append("")


        print(f"Splitting chapter text into {len(text_chunks_for_prompting)} sequential chunks for {num_chunks} panel batches.")

        for chunk_idx, current_text_chunk in enumerate(text_chunks_for_prompting):
            panels_in_this_chunk_request = min(batch_size, num_panels - panels_generated_count)
            if panels_in_this_chunk_request <= 0:
                break

            print(f"\n--- Processing Panel Chunk {chunk_idx+1}/{num_chunks} ({panels_in_this_chunk_request} panels) ---")
            
            # Determine the panel numbers for this specific chunk
            start_panel_num_for_chunk = panels_generated_count + 1
            end_panel_num_for_chunk = panels_generated_count + panels_in_this_chunk_request
            panel_numbers_in_chunk_str = f"{start_panel_num_for_chunk} to {end_panel_num_for_chunk}"
            if panels_in_this_chunk_request == 1:
                panel_numbers_in_chunk_str = str(start_panel_num_for_chunk)


            json_schema_description = f'''
            IMPORTANT: Respond ONLY with a valid JSON object. Do NOT include any explanation, thoughts, or extra text outside the JSON object.
            The JSON object must have a single key: "comic_panels".
            The value for "comic_panels" must be an array of panel objects.
            Generate EXACTLY {panels_in_this_chunk_request} panel objects in the array, corresponding to panels {panel_numbers_in_chunk_str} of the overall story.
            Each panel object in the array must have exactly four keys:
            1.  "panel_number": (Integer) The sequential number of the panel in the overall comic (e.g., for the first panel in this batch, it would be {start_panel_num_for_chunk}).
            2.  "brief_description": (String) A concise, technical description of the panel, including shot type, key character actions, and any critical SFX or Captions that are part of the brief.
                Examples of "brief_description":
                - "EXTREME CLOSE-UP – PROTAGONIST'S EYES. His blue eyes fly open in pure, primal panic. Pupils contracted. Shock, confusion, and raw pain fill the gaze. Blood runs from his brow into one eye. CAPTION: Searing pain."
                - "INSERT – FLASH GLIMPSE. Blurred impression: red teeth, dark fur, bone horns, and a mouth clamped onto flesh. Not fully clear—just trauma images."
                - "WIDE SHOT – FIRST REVEAL. The Gnasher—quadrupedal, monstrous, all sinew and bone—pins the protagonist to the ground, its gaping jaw locked into his left shoulder. Blood pours down torn warrior armor. His bandaged ribs are visible through a gap in shattered plating. SFX: KRRRSHK!"
                - "CLOSE-UP – MOUTH OPEN IN SCREAM. The protagonist lets out a deep, guttural scream. Teeth bared. Veins in neck bulging. His body arches beneath the beast. SFX: ARRRGHHH!"
                - "DYNAMIC ANGLE – BEAST SHAKES HIM. The Gnasher whips its head, jerking the protagonist violently. Blood spatters across the dirt. Armor straps tear. SFX: RRGH-GH-GH!"
            3.  "visual_description": (String) A detailed visual description for the artist, focusing on what is seen. Include details about composition, lighting, camera angle, character positions and expressions, and visual atmosphere. Aim for 2-4 substantial sentences or a short paragraph per panel. Do NOT include dialogue or sound effects here; they belong in the brief if critical or will be added later.
                Examples of "visual_description":
                - "EXTREME CLOSE-UP. A rugged man in his early 30s opens his eyes in shock and pain. His blue eyes are wide, pupils tight. Blood trickles from a cut above his brow. His expression is frozen in panic. The lighting is dim and the background is blurred."
                - "BLURRY FLASH PANEL. A distorted image of a snarling canine monster with sharp bone horns, leathery skin, and flaring nostrils. Its teeth are bared. The scene is overexposed and dreamlike, like a traumatic memory flash."
                - "WIDE SHOT. A muscular man in torn, bloodied warrior armor lies pinned beneath a monstrous quadruped beast. The beast is biting into his left shoulder. The creature's muzzle is covered in bone spikes, and its eye glares with feral intensity. Blood pours from the man's shoulder onto cracked stone ground."
                - "CLOSE-UP. The man screams in pain. His mouth is wide open, teeth clenched. Blood is on his lips and face. His neck veins are tense. The background is chaotic and motion-blurred."
                - "ACTION SHOT. The beast shakes its head violently with the man's shoulder in its jaws. Blood sprays from the wound. The man's upper body twists with the force of the motion. His armor tears at the seams."
            4.  "source_text_segment": (String) The specific, continuous segment of the provided "Story Text for this Batch" that this panel visually represents. This should be a direct quote or a very close paraphrase of the text that inspired the panel's content. If the panel is an insert or an action not explicitly described but implied, indicate that (e.g., "Visual insert, implied from previous text." or "Action sequence between described events.").
            '''

            instruction = f'''
            {system_prompt}

            Story Text for this Batch (Chunk {chunk_idx + 1}/{num_chunks} of the overall story, covering panels {panel_numbers_in_chunk_str}):
            """
            {current_text_chunk}
            """

            Character Context (if any):
            {character_context if character_context else "No specific character context provided for this batch."}

            Background Context (if any):
            {background_context if background_context else "No specific background context provided for this batch."}

            Based on the "Story Text for this Batch", system prompt, and any character/background context, generate {panels_in_this_chunk_request} sequential comic panel data objects.
            These panels should cover the story from panel number {start_panel_num_for_chunk} up to {end_panel_num_for_chunk}.
            Each panel description should be vivid and guide an artist.
            
            {json_schema_description}
            '''
            
            print(f"Instruction length for chunk {chunk_idx+1}: {len(instruction)} characters")

            config = types.GenerateContentConfig(
                temperature=0.7,
                top_p=0.95,
                max_output_tokens=8192, 
                response_mime_type="application/json", # Essential for structured output
                safety_settings=self.safety_settings
            )

            full_response_text = ""
            try:
                print(f"Sending request for panel chunk {chunk_idx+1} to AI model ({TEXT_MODEL_ID})...")
                
                stream = self.client.models.generate_content_stream(
                    model=TEXT_MODEL_ID, 
                    contents=[types.Content(role="user", parts=[types.Part.from_text(text=instruction)])],
                    config=config,
                )
                for chunk_resp in stream:
                    if chunk_resp.text:
                        full_response_text += chunk_resp.text
                
                print(f"Response received for chunk {chunk_idx+1}. Length: {len(full_response_text)} chars.")

                if not full_response_text.strip():
                    print(f"Error: Empty response from model for chunk {chunk_idx+1}")
                    raise Exception("Empty response from AI model")

                # Attempt to clean and parse the JSON
                cleaned_response = full_response_text.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[len("```json"):].strip()
                if cleaned_response.startswith("```"): # Handles cases like ```json\n ... ``` or ```\n ... ```
                     cleaned_response = cleaned_response[len("```"):].strip()
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-len("```")].strip()
                
                json_data = json.loads(cleaned_response)
                
                if "comic_panels" in json_data and isinstance(json_data["comic_panels"], list):
                    chunk_panels_data = json_data["comic_panels"]
                    print(f"Successfully parsed {len(chunk_panels_data)} panels from JSON for chunk {chunk_idx+1}")
                    
                    if len(chunk_panels_data) != panels_in_this_chunk_request:
                        print(f"Warning: AI returned {len(chunk_panels_data)} panels, but {panels_in_this_chunk_request} were expected for this chunk.")
                    
                    for i in range(panels_in_this_chunk_request):
                        actual_panel_num_overall = start_panel_num_for_chunk + i
                        if i < len(chunk_panels_data):
                            panel_obj = chunk_panels_data[i]
                            if not isinstance(panel_obj, dict) or \
                               panel_obj.get("panel_number") != actual_panel_num_overall or \
                               "brief_description" not in panel_obj or \
                               "visual_description" not in panel_obj or \
                               "source_text_segment" not in panel_obj:
                                print(f"Warning: Panel data for panel {actual_panel_num_overall} is malformed. Received: {panel_obj}. Using placeholders.")
                                all_panel_data.append({
                                    "panel_number": actual_panel_num_overall,
                                    "brief_description": panel_obj.get("brief_description", f"Malformed brief description for panel {actual_panel_num_overall}"),
                                    "visual_description": panel_obj.get("visual_description", f"Malformed visual description for panel {actual_panel_num_overall}"),
                                    "source_text_segment": panel_obj.get("source_text_segment", "Malformed source text segment.")
                                })
                            else:
                                all_panel_data.append(panel_obj) # Add valid panel data
                        else: # AI returned fewer panels than requested for the chunk
                            print(f"Warning: AI did not return data for panel {actual_panel_num_overall}. Adding placeholder.")
                            all_panel_data.append({
                                "panel_number": actual_panel_num_overall,
                                "brief_description": f"Error: AI did not generate brief for panel {actual_panel_num_overall}",
                                "visual_description": f"Error: AI did not generate visual for panel {actual_panel_num_overall}",
                                "source_text_segment": "Error: AI did not provide source text."
                            })
                else:
                    print(f"Error: 'comic_panels' key missing or not a list in JSON response for chunk {chunk_idx+1}. Response: {cleaned_response[:500]}...")
                    raise json.JSONDecodeError("Missing 'comic_panels' key or invalid type", cleaned_response, 0)

            except Exception as e: # Catch JSONDecodeError and other general errors
                print(f"Error processing panel chunk {chunk_idx+1}: {str(e)}")
                if full_response_text: print(f"Problematic response for chunk {chunk_idx+1}: {full_response_text[:1000]}...")
                # Add placeholder data for this entire chunk if processing fails
                for i in range(panels_in_this_chunk_request):
                    panel_num = start_panel_num_for_chunk + i
                    all_panel_data.append({
                        "panel_number": panel_num,
                        "brief_description": f"Error processing chunk for panel {panel_num}",
                        "visual_description": f"Error processing chunk for panel {panel_num}",
                        "source_text_segment": "Error processing chunk."
                    })
            
            panels_generated_count += panels_in_this_chunk_request


        # Ensure the final list has the exact number of panels requested, filling with errors if necessary
        if len(all_panel_data) < num_panels:
             print(f"Warning: Generated {len(all_panel_data)} panel data objects, but {num_panels} were requested. Filling missing {num_panels - len(all_panel_data)} with error placeholders.")
             for i in range(len(all_panel_data), num_panels):
                panel_num_overall = i + 1
                all_panel_data.append({
                    "panel_number": panel_num_overall, # Ensure correct overall panel number
                    "brief_description": f"Error: Panel {panel_num_overall} was not generated by AI.",
                    "visual_description": f"Error: Panel {panel_num_overall} was not generated by AI.",
                    "source_text_segment": "Error: Panel {panel_num_overall} was not generated by AI."
                })
        
        print(f"\n=== Comprehensive Panel Description Generation Complete ===")
        print(f"Total panel data objects finalized: {len(all_panel_data)}")
        # Sort by panel_number just in case chunks came back out of order or AI mismatched numbers
        # And then slice to the requested num_panels
        return sorted(all_panel_data, key=lambda p: p.get("panel_number", float('inf')))[:num_panels]

    async def generate_panel_variants_async(self,
                                          panel_description: str,
                                          character_references: List[Dict[str, str]],
                                          background_references: List[Tuple[str, str]],
                                          num_variants: int,
                                          system_prompt: str,
                                          temperature: float = 0.7,
                                          additional_instructions: str = "",
                                          previous_panel_image: Optional[Tuple[bytes, str]] = None) -> List[Tuple[bytes, str]]:
        """Generate multiple variants of a panel image asynchronously."""
        current_request_parts = []
        max_retries = 3
        retry_delay = 1
        
        known_character_names_from_refs = [ref['name'] for ref in character_references]
        
        mentioned_characters = self._extract_character_names(panel_description, known_character_names_from_refs)
        print(f"Panel description: {panel_description[:100]}...")
        print(f"Known characters provided (structured): {[{'name': ref['name'], 'desc': ref['description'][:30]+'...'} for ref in character_references]}")
        print(f"Characters identified in panel description: {mentioned_characters}")
        
        relevant_char_refs_structured = []
        if mentioned_characters:
            for ref in character_references:
                if ref['name'] in mentioned_characters:
                    relevant_char_refs_structured.append(ref)
        print(f"Relevant structured character references being sent to AI: {[{'name': ref['name'], 'desc': ref['description'][:30]+'...', 'uri': ref['uri']} for ref in relevant_char_refs_structured]}")
        
        for char_ref_data in relevant_char_refs_structured:
            char_name = char_ref_data['name']
            char_desc = char_ref_data['description']
            char_uri = char_ref_data['uri']
            
            char_context = (
                f"IMPORTANT CONTEXT FOR CHARACTER: '{char_name}'\n"
                f"Description: {char_desc}\n"
                f"A visual reference image for '{char_name}' is provided. "
                f"If this character is part of the current panel description, "
                f"adhere to this reference image and description for their appearance. "
                f"This reference image is a guide; adapt it to the panel's specific action, emotion, and perspective."
            )
            current_request_parts.append(types.Part.from_text(text=char_context))
            if char_uri and char_uri.strip(): # Ensure URI is not empty
                current_request_parts.append(types.Part.from_uri(file_uri=char_uri, mime_type="image/png")) # Assuming PNG, might need to be flexible
        
        # Add background references (still name, uri tuples)
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
                                          character_references: List[Dict[str, str]],
                                          background_references: List[Tuple[str, str]],
                                          num_variants: int,
                                          system_prompt: str,
                                          temperature: float = 0.7,
                                          additional_instructions: str = "") -> List[Tuple[bytes, str]]:
        """Generate final variants of a panel image asynchronously."""
        current_request_parts = []
        max_retries = 3
        retry_delay = 1
        
        # Process character references (now structured)
        # No need to call _extract_character_names here again if we assume image_generator.py did the filtering.
        # Or, if we want to be safe, we can re-filter. For now, assume image_generator.py sends relevant ones.
        print(f"Final Gen - Received structured character references: {[{'name': ref['name'], 'desc': ref['description'][:30]+'...', 'uri': ref['uri']} for ref in character_references]}")

        for char_ref_data in character_references: # Assumes these are already filtered to be relevant
            char_name = char_ref_data['name']
            char_desc = char_ref_data['description']
            char_uri = char_ref_data['uri']
            
            char_context = (
                f"IMPORTANT CONTEXT FOR CHARACTER: '{char_name}'\n"
                f"Description: {char_desc}\n"
                f"A visual reference image for '{char_name}' is provided. "
                f"If this character is part of the current panel description, "
                f"adhere to this reference image and description for their appearance. "
                f"This reference image is a guide; adapt it to the panel's specific action, emotion, and perspective."
            )
            current_request_parts.append(types.Part.from_text(text=char_context))
            if char_uri and char_uri.strip():
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
        
        # Add the main panel description for context
        current_request_parts.append(types.Part.from_text(text=panel_description))
        
        # Add system prompt if provided and non-empty (optional integration point)
        if system_prompt and system_prompt.strip():
             current_request_parts.insert(0, types.Part.from_text(text=system_prompt)) # Prepend system prompt

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

    def generate_panel_image(
        self, 
        prompt: str,
        character_image_bytes: List[bytes] = None,
        background_image_bytes: bytes = None,
        temperature: float = DEFAULT_IMAGE_TEMPERATURE
    ) -> Optional[bytes]:
        """Generate a panel image from a prompt using google-genai SDK."""
        try:
            print(f"Generating panel image with prompt: {prompt[:100]}...")
            
            # Create parts for the content
            parts = [types.Part.from_text(text=prompt)]
            
            # Add character reference images if provided
            if character_image_bytes:
                for img_bytes in character_image_bytes:
                    parts.append(types.Part(inline_data=types.Blob(
                        data=img_bytes,
                        mime_type="image/png"
                    )))
                print(f"Added {len(character_image_bytes)} character reference images")
            
            # Add background reference image if provided
            if background_image_bytes:
                parts.append(types.Part(inline_data=types.Blob(
                    data=background_image_bytes,
                    mime_type="image/png"
                )))
                print("Added background reference image")
            
            # Create content
            content = types.Content(
                role="user",
                parts=parts
            )
            
            # Configure generation
            generate_config = types.GenerateContentConfig(
                temperature=temperature,
                top_p=0.95,
                max_output_tokens=8192,
                response_modalities=["TEXT", "IMAGE"],
                safety_settings=self.safety_settings
            )
            
            # Generate image
            try:
                print(f"Sending request to model: {MULTIMODAL_MODEL_ID}")
                response = self.client.models.generate_content(
                    model=MULTIMODAL_MODEL_ID,
                    contents=[content],
                    config=generate_config
                )
                
                # Extract image from response
                if response.candidates:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            print("Successfully generated panel image")
                            return part.inline_data.data
                
                print("No image generated in response")
                return None
                
            except Exception as e:
                error_message = str(e)
                if "400" in error_message:
                    print("API Error 400: Bad Request. This could be due to:")
                    print("- Model not available in your region")
                    print("- Prompt contains prohibited content")
                    print("- Quota exceeded")
                    print(f"Complete error: {error_message}")
                elif "403" in error_message:
                    print("API Error 403: Forbidden. This could be due to:")
                    print("- Missing API permissions")
                    print("- API not enabled for your project")
                    print(f"Complete error: {error_message}")
                elif "404" in error_message:
                    print("API Error 404: Not Found. This could be due to:")
                    print("- Incorrect model ID")
                    print("- Model not available in your region")
                    print(f"Complete error: {error_message}")
                else:
                    print(f"Error generating panel image: {error_message}")
                return None
                
        except Exception as e:
            print(f"Error setting up panel image generation: {e}")
            return None
    
    def enhance_panel_description(self, 
                                base_description: str, 
                                project_context: str = "",
                                character_descriptions: List[str] = None,
                                background_descriptions: List[str] = None,
                                skip: bool = False) -> Optional[str]:
        """Enhance a panel description with more details."""
        # If skip flag is set, return the base description without enhancement
        if skip:
            print("Skipping enhancement as requested")
            return base_description
        
        max_retries = 2
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries + 1):
            try:
                print(f"Enhancing panel description (attempt {attempt+1}/{max_retries+1})")
                
                # Build prompt with context
                prompt = f"Create a detailed, visual description for a comic panel based on this context:\n\n{base_description}\n\n"
                
                if project_context:
                    prompt += f"Project context: {project_context}\n\n"
                
                if character_descriptions:
                    prompt += "Characters:\n"
                    for desc in character_descriptions:
                        prompt += f"- {desc}\n"
                    prompt += "\n"
                
                if background_descriptions:
                    prompt += "Backgrounds:\n"
                    for desc in background_descriptions:
                        prompt += f"- {desc}\n"
                    prompt += "\n"
                
                prompt += """
                Instructions:
                1. Create a detailed visual description that a comic artist could use to draw this panel
                2. Include details about composition, lighting, camera angle, character positions and expressions
                3. Focus ONLY on what can be seen in this specific panel - it's a frozen moment in time
                4. Don't include dialogue or sound effects in the description
                5. Be specific about visual elements rather than abstract concepts
                6. Length should be 3-5 paragraphs
                """
                
                # Create content
                content = types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)]
                )
                
                # Configure generation with reasonable values for creative text
                generate_config = types.GenerateContentConfig(
                    temperature=0.7,
                    top_p=0.95,
                    top_k=40,
                    max_output_tokens=4096,
                    safety_settings=self.safety_settings
                )
                
                # Generate enhanced description
                print("Sending request to AI model")
                response = None
                
                # Use streaming to better handle long responses
                full_response = ""
                for chunk_resp in self.client.models.generate_content_stream(
                    model=TEXT_MODEL_ID,
                    contents=[content],
                    config=generate_config
                ):
                    if chunk_resp.text:
                        full_response += chunk_resp.text
                        print(".", end="", flush=True)  # Simple progress indicator
                
                print("\nResponse received.")
                
                if full_response:
                    # Clean up response - remove any markdown formatting or other artifacts
                    cleaned_response = full_response.strip()
                    cleaned_response = cleaned_response.replace("**", "")
                    
                    # Sometimes the model adds titles or headers - remove them
                    lines = cleaned_response.split('\n')
                    if len(lines) > 1 and (lines[0].startswith('Panel') or lines[0].startswith('#')):
                        cleaned_response = '\n'.join(lines[1:]).strip()
                    
                    print(f"Generated description ({len(cleaned_response)} chars)")
                    return cleaned_response
                
                print("Empty response received from model")
                if attempt < max_retries:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                
            except Exception as e:
                print(f"Error in enhance_panel_description (attempt {attempt+1}): {str(e)}")
                if attempt < max_retries:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
        
        # If we've exhausted all retries, return a simplified version of the base description
        print("All retries failed, returning basic description")
        if base_description:
            return base_description
        
        return None 

    def split_panel_descriptions(self, 
                               original_description: str,
                               brief_description: str,
                               source_text: str,
                               num_panels: int = 2) -> List[Dict[str, str]]:
        """Generate descriptions for split panels based on the original panel."""
        print(f"Generating descriptions for {num_panels} split panels...")
        
        prompt = f"""
        I need to split this comic panel into {num_panels} sequential panels that show the action in more detail.
        
        Original Panel Brief Description:
        {brief_description}
        
        Original Panel Detailed Description:
        {original_description}
        
        Source Text:
        {source_text}
        
        Please create {num_panels} new panel descriptions that break down this scene into sequential moments.
        For each panel, provide both a brief technical description (shot type, key action) and a detailed visual description.
        
        Format your response as a valid JSON object with the following structure:
        {{
          "panels": [
            {{
              "brief_description": "SHOT TYPE - Key action description",
              "visual_description": "Detailed visual description for the artist..."
            }},
            {{
              "brief_description": "SHOT TYPE - Key action description",
              "visual_description": "Detailed visual description for the artist..."
            }}
          ]
        }}
        
        Make sure each panel flows naturally from one to the next and captures a distinct moment in the action.
        """
        
        config = types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.95,
            max_output_tokens=4096,
            response_mime_type="application/json",
            safety_settings=self.safety_settings
        )
        
        try:
            full_response = ""
            print("Sending split panel request to AI model...")
            for chunk_resp in self.client.models.generate_content_stream(
                model=TEXT_MODEL_ID,
                contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
                config=config,
            ):
                if chunk_resp.text:
                    full_response += chunk_resp.text
                    print(".", end="", flush=True)  # Simple progress indicator
            
            print("\nResponse received")
            
            # Parse response as JSON
            try:
                json_data = json.loads(full_response)
                panels = json_data.get("panels", [])
                print(f"Successfully parsed {len(panels)} panel descriptions")
                return panels
            except json.JSONDecodeError:
                # Try to extract JSON from the response if there's text before/after
                json_pattern = r'(\{[\s\S]*\})'
                match = re.search(json_pattern, full_response)
                
                if match:
                    try:
                        potential_json = match.group(1)
                        json_data = json.loads(potential_json)
                        panels = json_data.get("panels", [])
                        if panels:
                            print(f"Successfully extracted {len(panels)} panel descriptions from text")
                            return panels
                    except Exception:
                        pass
                
                # If all else fails, return empty descriptions
                print(f"Failed to parse JSON response: {full_response[:200]}...")
                return [{"brief_description": f"PANEL {i+1}/{num_panels}", 
                         "visual_description": f"Split from original panel, part {i+1} of {num_panels}"} 
                        for i in range(num_panels)]
        
        except Exception as e:
            print(f"Error generating split panel descriptions: {str(e)}")
            return [{"brief_description": f"PANEL {i+1}/{num_panels}", 
                     "visual_description": f"Split from original panel, part {i+1} of {num_panels}"} 
                    for i in range(num_panels)] 