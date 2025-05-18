"""Service for interacting with Google Cloud Storage."""

import uuid
from typing import Optional, Tuple, List, Dict
from google.cloud import storage
from google.api_core import retry, exceptions
from src.config.settings import GOOGLE_CLOUD_PROJECT, GCS_BUCKET_NAME
import traceback
import os
from datetime import datetime
import json
from pathlib import Path
import re # Import re for sanitization

class StorageService:
    """Service for interacting with Google Cloud Storage."""
    
    def __init__(self):
        """Initialize the storage service."""
        print("Initializing storage service...")
        try:
            self.client = storage.Client(project=GOOGLE_CLOUD_PROJECT)
            self.bucket = self.client.bucket(GCS_BUCKET_NAME)
            print(f"Using bucket: {GCS_BUCKET_NAME}")
        except Exception as e:
            print(f"Error initializing storage service: {e}")
            self.client = None
            self.bucket = None
        
    def _sanitize_name_for_path(self, name: str) -> str:
        """Sanitize a name to be used as part of a GCS path component."""
        # Replace spaces with underscores
        name = name.replace(" ", "_")
        # Remove characters not typically allowed or problematic in paths/filenames
        # This is not exhaustive but covers common cases.
        name = re.sub(r'[^a-zA-Z0-9_.-]', '', name)
        # Ensure it's not empty after sanitization
        if not name:
            return "untitled"
        return name.lower() # Often good practice to lowercase path components
    
    def _generate_timestamped_path(self, project_id: str, file_type: str, index: int = None) -> str:
        """Generate a timestamped path for project files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if index is not None:
            return f"projects/{project_id}/{file_type}_{index:03d}_{timestamp}"
        return f"projects/{project_id}/{file_type}_{timestamp}"
    
    @retry.Retry(predicate=retry.if_exception_type(Exception))
    def save_image(self, image_bytes: bytes, project_id: str, panel_index: int, variant_type: str, variant_index: int = None) -> str:
        """Save an image to GCS and return its URI."""
        try:
            if not image_bytes:
                raise ValueError("Empty image bytes provided")
            
            # Generate a timestamped path
            base_path = self._generate_timestamped_path(project_id, f"panel_{panel_index:03d}_{variant_type}")
            if variant_index is not None:
                base_path += f"_variant_{variant_index:03d}"
            
            # Save the image
            blob_name = f"{base_path}.png"
            blob = self.bucket.blob(blob_name)
            blob.upload_from_string(image_bytes, content_type="image/png")
            
            # Save the metadata
            metadata_name = f"{base_path}_metadata.json"
            metadata_blob = self.bucket.blob(metadata_name)
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "panel_index": panel_index,
                "variant_type": variant_type,
                "variant_index": variant_index,
                "image_uri": f"gs://{GCS_BUCKET_NAME}/{blob_name}"
            }
            metadata_blob.upload_from_string(
                json.dumps(metadata, indent=2),
                content_type="application/json"
            )
            
            gcs_uri = f"gs://{GCS_BUCKET_NAME}/{blob_name}"
            print(f"Saving image to GCS URI: {gcs_uri}")
            return gcs_uri
            
        except Exception as e:
            print(f"Error saving image: {str(e)}")
            print(f"Full traceback: {traceback.format_exc()}")
            raise
    
    @retry.Retry(predicate=retry.if_exception_type(Exception))
    def save_project_file(self, project_id: str, filename: str, content: bytes, content_type: str) -> Optional[str]:
        """Save a project file to GCS."""
        if not self.bucket:
            print("Storage service not initialized")
            return None

        try:
            blob_name = f"projects/{project_id}/{filename}"
            blob = self.bucket.blob(blob_name)
            blob.upload_from_string(content, content_type=content_type)
            return f"gs://{self.bucket.name}/{blob_name}"
        except Exception as e:
            print(f"Error saving project file: {e}")
            return None
    
    @retry.Retry(predicate=retry.if_exception_type(Exception))
    def save_character_reference(self, project_id: str, character_name: str, image_bytes: bytes, mime_type: str) -> Optional[str]:
        """Save a character reference image to GCS."""
        print(f"[StorageService] save_character_reference called with:")
        print(f"  Project ID: {project_id}")
        print(f"  Character Name (Original): {character_name}")
        print(f"  MIME Type: {mime_type}")
        print(f"  Image Bytes Length: {len(image_bytes) if image_bytes else 'No Bytes'}")

        if not self.bucket:
            print("[StorageService] Error: Storage service bucket not initialized.")
            return None
        if not project_id:
            print("[StorageService] Error: project_id is empty.")
            return None
        if not character_name:
            print("[StorageService] Error: character_name is empty.")
            return None
        if not image_bytes:
            print("[StorageService] Error: image_bytes is empty.")
            return None
        if not mime_type:
            print("[StorageService] Error: mime_type is empty.")
            return None

        try:
            sanitized_char_name = self._sanitize_name_for_path(character_name)
            print(f"[StorageService] Sanitized Character Name: {sanitized_char_name}")
            
            file_extension = mime_type.split('/')[-1] if '/' in mime_type else 'png'
            if not file_extension: # handle cases like 'image/'
                file_extension = 'png' 
            print(f"[StorageService] Determined File Extension: {file_extension}")

            blob_name = f"projects/{project_id}/characters/{sanitized_char_name}.{file_extension}"
            print(f"[StorageService] Attempting to save character reference to GCS blob: {blob_name}")
            
            blob = self.bucket.blob(blob_name)
            print(f"[StorageService] Blob object created: {blob.name}")
            
            print(f"[StorageService] Uploading image with content_type: {mime_type}...")
            blob.upload_from_string(image_bytes, content_type=mime_type)
            print("[StorageService] Image upload successful.")
            
            gcs_uri = f"gs://{self.bucket.name}/{blob_name}"
            print(f"[StorageService] Successfully saved character reference: {gcs_uri}")
            return gcs_uri
        except Exception as e:
            print(f"[StorageService] Error during GCS operation in save_character_reference: {e}")
            print(f"  Project ID: {project_id}")
            print(f"  Character Name (Original): {character_name}")
            print(f"  Sanitized Name: {sanitized_char_name}")
            print(f"  MIME Type: {mime_type}")
            print(f"  Blob Name Attempted: {blob_name if 'blob_name' in locals() else 'Not determined'}")
            print(f"[StorageService] Full traceback: {traceback.format_exc()}")
            return None
    
    @retry.Retry(predicate=retry.if_exception_type(Exception))
    def save_background_reference(self, project_id: str, background_name: str, image_bytes: bytes, mime_type: str) -> Optional[str]:
        """Save a background reference image to GCS."""
        if not self.bucket:
            print("Storage service not initialized")
            return None

        try:
            sanitized_bg_name = self._sanitize_name_for_path(background_name)
            file_extension = mime_type.split('/')[-1] if '/' in mime_type else 'png'
            blob_name = f"projects/{project_id}/backgrounds/{sanitized_bg_name}.{file_extension}"

            print(f"Attempting to save background reference to GCS blob: {blob_name}")
            blob = self.bucket.blob(blob_name)
            blob.upload_from_string(image_bytes, content_type=mime_type)
            gcs_uri = f"gs://{self.bucket.name}/{blob_name}"
            print(f"Successfully saved background reference: {gcs_uri}")
            return gcs_uri
        except Exception as e:
            print(f"Error saving background reference to GCS: {e}")
            print(f"Project ID: {project_id}, Background Name (Original): {background_name}, MIME Type: {mime_type}")
            print(traceback.format_exc())
            return None
    
    @retry.Retry(predicate=retry.if_exception_type(Exception))
    def get_image(self, gcs_uri: str) -> Optional[bytes]:
        """Get an image from GCS using its URI."""
        if not self.bucket or not gcs_uri.startswith(f"gs://{self.bucket.name}/"):
            print("Invalid GCS URI or storage service not initialized")
            return None

        try:
            blob_name = gcs_uri[len(f"gs://{self.bucket.name}/"):]
            blob = self.bucket.blob(blob_name)
            return blob.download_as_bytes()
        except Exception as e:
            print(f"Error getting image: {e}")
            return None
    
    @retry.Retry(predicate=retry.if_exception_type(Exception))
    def get_project_file(self, project_id: str, filename: str) -> Optional[bytes]:
        """Get a project file from GCS."""
        if not self.bucket:
            print("Storage service not initialized")
            return None

        try:
            blob_name = f"projects/{project_id}/{filename}"
            blob = self.bucket.blob(blob_name)
            return blob.download_as_bytes()
        except exceptions.NotFound:
            print(f"Project file not found: {blob_name}")
            return None
        except Exception as e:
            print(f"Error getting project file: {e}")
            return None

    @retry.Retry(predicate=retry.if_exception_type(Exception))
    def list_projects(self) -> List[Dict[str, str]]:
        """List all projects in GCS or local storage."""
        print("[StorageService] list_projects called.")
        projects = []
        project_ids_found = set() # To track IDs and prevent duplicate processing from local if already found in GCS
        
        # Try to list projects from Google Cloud Storage
        if self.bucket:
            print("[StorageService] Attempting to list projects from GCS...")
            try:
                # Iterate through all blobs that look like project metadata files
                # Not using delimiter here to catch all metadata.json files even if nested unexpectedly
                # However, our structure is projects/<project_id>/metadata.json
                gcs_blobs = self.bucket.list_blobs(prefix="projects/")
                found_gcs_project_paths = set()

                for blob in gcs_blobs:
                    if blob.name.endswith("metadata.json"):
                        # Expected path: projects/project_id_value/metadata.json
                        parts = blob.name.split('/')
                        if len(parts) == 3 and parts[0] == 'projects' and parts[2] == 'metadata.json':
                            project_id_from_gcs = parts[1]
                            if project_id_from_gcs not in found_gcs_project_paths:
                                print(f"[StorageService] Found potential GCS project metadata: {blob.name}, Extracted ID: {project_id_from_gcs}")
                                found_gcs_project_paths.add(project_id_from_gcs)
                                try:
                                    metadata_bytes = self.get_project_file(project_id_from_gcs, "metadata.json")
                                    if metadata_bytes:
                                        data = json.loads(metadata_bytes.decode('utf-8')) # Ensure bytes are decoded
                                        project_name = data.get("name", project_id_from_gcs)
                                        projects.append({
                                            "id": project_id_from_gcs,
                                            "name": project_name
                                        })
                                        project_ids_found.add(project_id_from_gcs)
                                        print(f"  Successfully added GCS project: ID='{project_id_from_gcs}', Name='{project_name}'")
                                    else:
                                        print(f"  Warning: metadata.json for GCS project ID '{project_id_from_gcs}' was empty or unreadable by get_project_file.")
                                except Exception as e_parse:
                                    print(f"  Error parsing metadata for GCS project ID '{project_id_from_gcs}': {e_parse}")
                        else:
                            print(f"[StorageService] Found metadata.json at unexpected GCS path, skipping: {blob.name}")
                if not found_gcs_project_paths:
                    print("[StorageService] No GCS projects found with 'projects/<id>/metadata.json' structure.")

            except Exception as e_gcs_list:
                print(f"[StorageService] Error listing GCS projects: {e_gcs_list}")
        else:
            print("[StorageService] GCS bucket not initialized, skipping GCS project listing.")
        
        # Also list projects from local storage
        print("[StorageService] Attempting to list projects from local storage...")
        try:
            local_projects_parent_dir = Path("data") / "projects"
            print(f"[StorageService] Checking local project directory: {local_projects_parent_dir.resolve()}")
            if local_projects_parent_dir.exists() and local_projects_parent_dir.is_dir():
                for project_id_local_folder in local_projects_parent_dir.iterdir():
                    if project_id_local_folder.is_dir(): # Each project is a directory
                        local_project_id_str = project_id_local_folder.name
                        print(f"[StorageService] Found local potential project directory: {local_project_id_str}")
                        if local_project_id_str in project_ids_found:
                            print(f"  Skipping local project '{local_project_id_str}' as it was already found in GCS.")
                            continue
                        
                        metadata_path = project_id_local_folder / "metadata.json"
                        if metadata_path.exists() and metadata_path.is_file():
                            print(f"  Found local metadata.json: {metadata_path}")
                            try:
                                with open(metadata_path, "r", encoding='utf-8') as f:
                                    data = json.load(f)
                                project_name = data.get("name", local_project_id_str)
                                projects.append({
                                    "id": local_project_id_str,
                                    "name": project_name
                                })
                                project_ids_found.add(local_project_id_str) # Also add to avoid GCS reprocessing if order changes
                                print(f"  Successfully added local project: ID='{local_project_id_str}', Name='{project_name}'")
                            except Exception as e_local_parse:
                                print(f"  Error parsing local metadata for project ID '{local_project_id_str}': {e_local_parse}")
                        else:
                            print(f"  No metadata.json found in local project directory: {project_id_local_folder}")
            else:
                print(f"[StorageService] Local projects directory does not exist or is not a directory: {local_projects_parent_dir}")
        except Exception as e_local_list:
            print(f"[StorageService] Error listing local projects: {e_local_list}")
        
        print(f"[StorageService] list_projects finished. Found {len(projects)} projects: {projects}")
        return projects 