"""Service for interacting with Google Cloud Storage."""

import uuid
from typing import Optional, Tuple
from google.cloud import storage
from google.api_core import retry
from config.settings import GOOGLE_CLOUD_PROJECT, GCS_BUCKET_NAME
import traceback
import os
from datetime import datetime
import json

class StorageService:
    """Service for interacting with Google Cloud Storage."""
    
    def __init__(self):
        """Initialize the storage service."""
        print("Initializing storage service...")
        self.client = storage.Client(project=GOOGLE_CLOUD_PROJECT)
        self.bucket = self.client.bucket(GCS_BUCKET_NAME)
        print(f"Using bucket: {GCS_BUCKET_NAME}")
        
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
    def save_project_file(self, project_id: str, filename: str, content: bytes, content_type: str) -> str:
        """Save a project file to GCS."""
        try:
            if not content:
                raise ValueError("Empty content provided")
            
            # Generate a timestamped path
            base_path = self._generate_timestamped_path(project_id, "project_file")
            blob_name = f"{base_path}_{filename}"
            
            blob = self.bucket.blob(blob_name)
            blob.upload_from_string(content, content_type=content_type)
            
            # Save the metadata
            metadata_name = f"{base_path}_{filename}_metadata.json"
            metadata_blob = self.bucket.blob(metadata_name)
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "filename": filename,
                "content_type": content_type,
                "file_uri": f"gs://{GCS_BUCKET_NAME}/{blob_name}"
            }
            metadata_blob.upload_from_string(
                json.dumps(metadata, indent=2),
                content_type="application/json"
            )
            
            return f"gs://{GCS_BUCKET_NAME}/{blob_name}"
            
        except Exception as e:
            print(f"Error saving project file: {str(e)}")
            print(f"Full traceback: {traceback.format_exc()}")
            raise
    
    @retry.Retry(predicate=retry.if_exception_type(Exception))
    def save_character_reference(self, project_id: str, character_name: str, image_bytes: bytes, content_type: str) -> str:
        """Save a character reference image to GCS."""
        try:
            if not image_bytes:
                raise ValueError("Empty image bytes provided")
            
            # Generate a timestamped path
            base_path = self._generate_timestamped_path(project_id, f"character_{character_name}")
            blob_name = f"{base_path}.png"
            
            blob = self.bucket.blob(blob_name)
            blob.upload_from_string(image_bytes, content_type=content_type)
            
            # Save the metadata
            metadata_name = f"{base_path}_metadata.json"
            metadata_blob = self.bucket.blob(metadata_name)
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "character_name": character_name,
                "content_type": content_type,
                "image_uri": f"gs://{GCS_BUCKET_NAME}/{blob_name}"
            }
            metadata_blob.upload_from_string(
                json.dumps(metadata, indent=2),
                content_type="application/json"
            )
            
            return f"gs://{GCS_BUCKET_NAME}/{blob_name}"
            
        except Exception as e:
            print(f"Error saving character reference: {str(e)}")
            print(f"Full traceback: {traceback.format_exc()}")
            raise
    
    @retry.Retry(predicate=retry.if_exception_type(Exception))
    def save_background_reference(self, project_id: str, background_name: str, image_bytes: bytes, content_type: str) -> str:
        """Save a background reference image to GCS."""
        try:
            if not image_bytes:
                raise ValueError("Empty image bytes provided")
            
            # Generate a timestamped path
            base_path = self._generate_timestamped_path(project_id, f"background_{background_name}")
            blob_name = f"{base_path}.png"
            
            blob = self.bucket.blob(blob_name)
            blob.upload_from_string(image_bytes, content_type=content_type)
            
            # Save the metadata
            metadata_name = f"{base_path}_metadata.json"
            metadata_blob = self.bucket.blob(metadata_name)
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "background_name": background_name,
                "content_type": content_type,
                "image_uri": f"gs://{GCS_BUCKET_NAME}/{blob_name}"
            }
            metadata_blob.upload_from_string(
                json.dumps(metadata, indent=2),
                content_type="application/json"
            )
            
            return f"gs://{GCS_BUCKET_NAME}/{blob_name}"
            
        except Exception as e:
            print(f"Error saving background reference: {str(e)}")
            print(f"Full traceback: {traceback.format_exc()}")
            raise
    
    @retry.Retry(predicate=retry.if_exception_type(Exception))
    def get_image(self, gcs_uri: str) -> bytes:
        """Get an image from GCS."""
        try:
            print(f"get_image called with URI: {gcs_uri}")
            if not gcs_uri or not gcs_uri.startswith("gs://"):
                raise ValueError(f"Invalid GCS URI format: {gcs_uri}")
            parts = gcs_uri[5:].split("/", 1)
            bucket_name = parts[0]
            print(f"Extracted bucket name: {bucket_name}")
            if not bucket_name:
                raise ValueError(f"Invalid bucket name: {bucket_name} (from URI: {gcs_uri})")
            # Extract blob name (everything after 'gs://bucket_name/')
            blob_name = gcs_uri[len(f"gs://{bucket_name}/"):]
            if bucket_name != GCS_BUCKET_NAME:
                raise ValueError(f"Invalid bucket name: {bucket_name}")
            blob = self.bucket.blob(blob_name)
            return blob.download_as_bytes()
        except Exception as e:
            print(f"Error getting image: {str(e)}")
            print(f"Full traceback: {traceback.format_exc()}")
            raise
    
    @retry.Retry(predicate=retry.if_exception_type(Exception))
    def get_project_file(self, project_id: str, filename: str) -> bytes:
        """Get a project file from GCS."""
        try:
            # List all files in the project directory
            prefix = f"projects/{project_id}/"
            blobs = self.bucket.list_blobs(prefix=prefix)
            
            # Find the most recent file matching the filename
            matching_blobs = []
            for blob in blobs:
                if filename in blob.name and not blob.name.endswith("_metadata.json"):
                    matching_blobs.append(blob)
            
            if not matching_blobs:
                return None
            
            # Sort by timestamp in the filename
            latest_blob = sorted(matching_blobs, key=lambda x: x.name.split("_")[-1], reverse=True)[0]
            return latest_blob.download_as_bytes()
            
        except Exception as e:
            print(f"Error getting project file: {str(e)}")
            print(f"Full traceback: {traceback.format_exc()}")
            raise

    @retry.Retry(predicate=retry.if_exception_type(Exception))
    def list_projects(self) -> list:
        """List all saved projects."""
        try:
            # List all project directories
            prefix = "projects/"
            blobs = self.bucket.list_blobs(prefix=prefix, delimiter="/")
            
            # Get all project IDs
            project_ids = set()
            for prefix in blobs.prefixes:
                project_id = prefix.split("/")[1]
                project_ids.add(project_id)
            
            # Get project metadata for each project
            projects = []
            for project_id in project_ids:
                try:
                    metadata = self.get_project_file(project_id, "metadata.json")
                    if metadata:
                        project_data = json.loads(metadata)
                        projects.append({
                            "id": project_id,
                            "name": project_data.get("name", "Unnamed Project"),
                            "created_at": project_data.get("created_at", ""),
                            "last_modified": project_data.get("last_modified", "")
                        })
                except Exception as e:
                    print(f"Error getting metadata for project {project_id}: {str(e)}")
                    continue
            
            # Sort projects by last modified date
            return sorted(projects, key=lambda x: x.get("last_modified", ""), reverse=True)
            
        except Exception as e:
            print(f"Error listing projects: {str(e)}")
            print(f"Full traceback: {traceback.format_exc()}")
            raise 