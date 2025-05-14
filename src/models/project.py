"""Project model for manga storyboard generation."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import json
import traceback

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
class PanelVariant:
    """A variant of a panel image."""
    image_uri: str  # GCS URI
    generation_prompt: str
    selected: bool = False
    feedback: Optional[str] = None

@dataclass
class Panel:
    """A panel in the storyboard."""
    description: str
    index: int
    variants: List[PanelVariant] = field(default_factory=list)
    selected_variant: Optional[PanelVariant] = None
    final_variants: List[PanelVariant] = field(default_factory=list)
    approved: bool = False
    notes: str = ""

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
        print(f"\n=== Loading Project from: {project_dir} ===")
        try:
            print("Reading metadata file...")
            with open(project_dir / "metadata.json", "r") as f:
                metadata = json.load(f)
            
            print("Creating project instance...")
            project = cls(
                name=metadata["name"],
                source_text="",  # Load from source file if needed
                source_file=metadata["source_file"],
                created_at=datetime.fromisoformat(metadata["created_at"]),
                updated_at=datetime.fromisoformat(metadata["updated_at"]),
                status=metadata["status"],
                project_dir=project_dir
            )
            
            # Load characters
            print("Loading characters...")
            for char_data in metadata["characters"]:
                print(f"Loading character: {char_data['name']}")
                project.characters[char_data["name"]] = Character(
                    name=char_data["name"],
                    description=char_data["description"],
                    reference_images=char_data["reference_images"],
                    style_notes=char_data["style_notes"]
                )
            
            # Load backgrounds
            print("Loading backgrounds...")
            for bg_data in metadata["backgrounds"]:
                print(f"Loading background: {bg_data['name']}")
                project.backgrounds[bg_data["name"]] = Background(
                    name=bg_data["name"],
                    description=bg_data["description"],
                    reference_image=bg_data["reference_image"],
                    style_notes=bg_data["style_notes"]
                )
            
            # Load panels
            print("Loading panels...")
            for panel_data in metadata["panels"]:
                print(f"Loading panel {panel_data['index'] + 1}")
                panel = Panel(
                    description=panel_data["description"],
                    index=panel_data["index"],
                    approved=panel_data["is_approved"],
                    notes=panel_data["notes"]
                )
                
                # Load variants
                print(f"Loading {len(panel_data['variants'])} variants...")
                for var_data in panel_data["variants"]:
                    variant = PanelVariant(
                        image_uri=var_data["image_uri"],
                        generation_prompt=var_data["generation_prompt"],
                        selected=var_data["is_selected"],
                        feedback=var_data["feedback"]
                    )
                    panel.variants.append(variant)
                    if var_data["is_selected"]:
                        panel.selected_variant = variant
                
                # Load final variants
                print(f"Loading {len(panel_data['final_variants'])} final variants...")
                for var_data in panel_data["final_variants"]:
                    variant = PanelVariant(
                        image_uri=var_data["image_uri"],
                        generation_prompt=var_data["generation_prompt"],
                        selected=var_data["is_selected"],
                        feedback=var_data["feedback"]
                    )
                    panel.final_variants.append(variant)
                
                project.panels.append(panel)
            
            print("Project loaded successfully")
            return project
            
        except Exception as e:
            print(f"Error loading project: {str(e)}")
            print(f"Full traceback: {traceback.format_exc()}")
            raise

    @classmethod
    def from_dict(cls, data: dict) -> 'Project':
        """Reconstruct a Project from a dictionary (parsed JSON from GCS)."""
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
                variants = [PanelVariant(**v) for v in panel_data.get("variants", [])]
                final_variants = [PanelVariant(**v) for v in panel_data.get("final_variants", [])]
                selected_variant = None
                for v in variants:
                    if getattr(v, "selected", False):
                        selected_variant = v
                        break
                panel = Panel(
                    description=panel_data["description"],
                    index=panel_data["index"],
                    variants=variants,
                    selected_variant=selected_variant,
                    final_variants=final_variants,
                    approved=panel_data.get("approved", panel_data.get("is_approved", False)),
                    notes=panel_data.get("notes", "")
                )
                panels.append(panel)
            # Parse timestamps
            created_at = data.get("created_at")
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)
            updated_at = data.get("updated_at")
            if isinstance(updated_at, str):
                updated_at = datetime.fromisoformat(updated_at)
            # Project dir (optional)
            project_dir = data.get("project_dir")
            if project_dir and not isinstance(project_dir, Path):
                project_dir = Path(str(project_dir))
            return cls(
                name=data["name"],
                source_text=data.get("source_text", ""),
                source_file=data.get("source_file", ""),
                created_at=created_at or datetime.now(),
                updated_at=updated_at or datetime.now(),
                characters=characters,
                backgrounds=backgrounds,
                panels=panels,
                status=data.get("status", "created"),
                project_dir=project_dir
            )
        except Exception as e:
            print(f"Error reconstructing Project from dict: {str(e)}")
            print(f"Full traceback: {traceback.format_exc()}")
            raise 