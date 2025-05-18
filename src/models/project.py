from __future__ import annotations
"""Project model for manga storyboard generation."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import json
import traceback

from src.models.panel import Panel, PanelVariant, PanelScript

class ProjectJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for Project and related classes."""
    def default(self, obj):
        if isinstance(obj, (Project, Character, Background, Panel, PanelVariant)):
            return asdict(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Path):
            return str(obj)
        return super().default(obj)

@dataclass
class Character:
    """Character model with reference images and descriptions."""
    name: str
    description: str
    reference_images: List[str] = field(default_factory=list)  # List of GCS URIs
    style_notes: str = ""

@dataclass
class Background:
    """Background style reference."""
    name: str
    description: str
    reference_image: str  # GCS URI
    style_notes: str = ""

@dataclass
class Project:
    """A manga storyboard project."""
    name: str
    source_text: str
    source_file: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    characters: Dict[str, Character] = field(default_factory=dict)
    backgrounds: Dict[str, Background] = field(default_factory=dict)
    panels: List[Panel] = field(default_factory=list)
    status: str = "created"  # created, generating_prompts, reviewing_prompts, generating_images, reviewing_images, completed
    project_dir: Optional[Path] = None

    def save(self):
        """Save project state to disk."""
        print(f"\n=== Saving Project: {self.name} ===")
        try:
            # Create project directory if it doesn't exist
            print(f"Creating project directory: {self.project_dir}")
            self.project_dir.mkdir(parents=True, exist_ok=True)
            
            # Save metadata
            print("Preparing metadata...")
            metadata = asdict(self)
            
            print(f"Saving metadata to: {self.project_dir / 'metadata.json'}")
            with open(self.project_dir / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=2, cls=ProjectJSONEncoder)
            
            print("Project saved successfully")
            return metadata
            
        except Exception as e:
            print(f"Error saving project: {str(e)}")
            print(f"Full traceback: {traceback.format_exc()}")
            raise

    @classmethod
    def load(cls, project_dir: Path) -> 'Project':
        """Load project from disk."""
        print(f"\n=== Loading Project from local disk: {project_dir} ===")
        try:
            metadata_path = project_dir / "metadata.json"
            print(f"Reading metadata file: {metadata_path}")
            with open(metadata_path, "r", encoding='utf-8') as f:
                metadata = json.load(f)
            
            # For local disk loading, it's better to reuse from_dict logic
            # after loading the dictionary from the file.
            print("Reconstructing project using from_dict logic...")
            # Add project_dir to metadata if it's not already there, as from_dict might use it.
            # However, from_dict itself can derive it if passed as a separate argument or if it expects it.
            # For simplicity, if from_dict is self-contained with the dict, this is enough.
            # Let's assume `from_dict` can handle the `project_dir` if it's in the `data` dict or is smart about it.
            # If `project_dir` is crucial for `from_dict` and not in `metadata`, it needs to be passed.
            # The current `from_dict` in the latest version seems to get `project_dir` from the dict itself.
            metadata['project_dir'] = str(project_dir) # Ensure project_dir is in the dict for from_dict
            return cls.from_dict(metadata)
            
        except FileNotFoundError:
            print(f"Error: metadata.json not found in {project_dir}")
            raise
        except json.JSONDecodeError:
            print(f"Error: Could not parse metadata.json in {project_dir}")
            raise
        except Exception as e:
            print(f"Error loading project from {project_dir}: {str(e)}")
            print(f"Full traceback: {traceback.format_exc()}")
            raise

    @classmethod
    def from_dict(cls, data: dict) -> 'Project':
        """Reconstruct a Project from a dictionary (parsed JSON from GCS or local)."""
        print("DEBUG: Project.from_dict called.")
        try:
            # Parse characters
            if isinstance(data.get("characters"), dict):
                characters = {name: Character(**char) for name, char in data["characters"].items()}
            else:
                # fallback for list of dicts
                characters = {char["name"]: Character(**char) for char in data.get("characters", [])}
            # Parse backgrounds
            if isinstance(data.get("backgrounds"), dict):
                backgrounds = {name: Background(**bg) for name, bg in data["backgrounds"].items()}
            else:
                backgrounds = {bg["name"]: Background(**bg) for bg in data.get("backgrounds", [])}
            # Parse panels
            panels = []
            for panel_data in data.get("panels", []):
                print(f"DEBUG: from_dict - Processing panel_data for index {panel_data.get('index')}")
                print(f"DEBUG: from_dict - panel_data raw official_final_image_uri: {panel_data.get('official_final_image_uri')}")
                script_data = panel_data.get("script", {})
                visual_desc_val = script_data.get("visual_description", panel_data.get("description"))
                if not visual_desc_val: visual_desc_val = ""
                script = PanelScript(
                    visual_description=visual_desc_val,
                    brief_description=script_data.get("brief_description", ""),
                    source_text=script_data.get("source_text", ""),
                    dialogue=script_data.get("dialogue", []),
                    captions=script_data.get("captions", []),
                    sfx=script_data.get("sfx", []),
                    thoughts=script_data.get("thoughts", []),
                    skip_enhancement=script_data.get("skip_enhancement", False)
                )
                variants_data = panel_data.get("variants", [])
                variants = [PanelVariant(**v) for v in variants_data]
                final_variants_data = panel_data.get("final_variants", [])
                final_variants = [PanelVariant(**v) for v in final_variants_data]
                selected_variant = None
                for v_data_idx, v_data_item in enumerate(variants_data):
                    if v_data_item.get("selected", False):
                        if v_data_idx < len(variants):
                             selected_variant = variants[v_data_idx]
                        break

                panel = Panel(
                    index=panel_data["index"],
                    script=script,
                    variants=variants,
                    selected_variant=selected_variant, 
                    final_variants=final_variants,
                    approved=panel_data.get("approved", panel_data.get("is_approved", False)),
                    notes=panel_data.get("notes", ""),
                    official_final_image_uri=panel_data.get("official_final_image_uri")
                )
                print(f"DEBUG: from_dict - Created Panel object with official_final_image_uri: {panel.official_final_image_uri}")
                panels.append(panel)
            
            created_at_str = data.get("created_at")
            created_at = datetime.fromisoformat(created_at_str) if isinstance(created_at_str, str) else datetime.now()
            updated_at_str = data.get("updated_at")
            updated_at = datetime.fromisoformat(updated_at_str) if isinstance(updated_at_str, str) else datetime.now()
            
            project_dir_val = data.get("project_dir")
            project_dir = Path(str(project_dir_val)) if project_dir_val else None

            return cls(
                name=data["name"],
                source_text=data.get("source_text", ""),
                source_file=data.get("source_file", ""),
                created_at=created_at,
                updated_at=updated_at,
                characters={name: Character(**char) for name, char in data.get("characters", {}).items()},
                backgrounds={name: Background(**bg) for name, bg in data.get("backgrounds", {}).items()},
                panels=panels,
                status=data.get("status", "created"),
                project_dir=project_dir
            )
        except Exception as e:
            print(f"Error reconstructing Project from dict: {str(e)}")
            print(f"Full traceback: {traceback.format_exc()}")
            raise 

    def to_dict(self) -> dict:
        """Convert project to a dictionary for serialization."""
        print("DEBUG: Project.to_dict called.")
        result = {
            "name": self.name,
            "source_text": self.source_text,
            "source_file": self.source_file,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
            "status": self.status,
            "project_dir": str(self.project_dir) if self.project_dir else None,
            "characters": {},
            "backgrounds": {},
            "panels": []
        }
        for name, char_obj in self.characters.items(): # Renamed char to char_obj to avoid conflict
            result["characters"][name] = asdict(char_obj)
        for name, bg_obj in self.backgrounds.items(): # Renamed bg to bg_obj
            result["backgrounds"][name] = asdict(bg_obj)

        for panel_obj in self.panels: # Renamed panel to panel_obj
            panel_dict = {
                "index": panel_obj.index,
                "script": asdict(panel_obj.script) if hasattr(panel_obj, 'script') and panel_obj.script else {},
                "variants": [asdict(v) for v in panel_obj.variants],
                "selected_variant": asdict(panel_obj.selected_variant) if panel_obj.selected_variant else None,
                "final_variants": [asdict(v) for v in panel_obj.final_variants],
                "official_final_image_uri": getattr(panel_obj, "official_final_image_uri", None),
                "approved": getattr(panel_obj, "approved", False),
                "notes": getattr(panel_obj, "notes", "")
            }
            print(f"DEBUG: to_dict - panel_dict for index {panel_obj.index} being added: official_final_image_uri='{panel_dict.get('official_final_image_uri')}'")
            result["panels"].append(panel_dict)
        
        return result 