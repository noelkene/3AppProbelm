from __future__ import annotations
"""Panel model for manga storyboard generation."""

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class PanelVariant:
    """A variant of a panel image."""
    image_uri: str  # GCS URI
    generation_prompt: str
    selected: bool = False
    feedback: Optional[str] = None
    evaluation_score: Optional[float] = None  # AI evaluation score (0-10)
    evaluation_reasoning: Optional[str] = None  # AI reasoning for the score

@dataclass
class PanelScript:
    """Script content for a panel."""
    visual_description: str  # Used for image generation
    brief_description: str = ""  # Brief technical description (shot type, action, etc.)
    source_text: str = ""  # Relevant text from the chapter for this panel
    dialogue: List[str] = field(default_factory=list)  # Character dialogue
    captions: List[str] = field(default_factory=list)  # Narrative captions
    sfx: List[str] = field(default_factory=list)  # Sound effects
    thoughts: List[str] = field(default_factory=list)  # Character thoughts
    skip_enhancement: bool = False  # Flag to indicate if we should skip enhancement

@dataclass
class Panel:
    """A panel in the storyboard."""
    index: int
    script: PanelScript
    variants: List[PanelVariant] = field(default_factory=list)
    selected_variant: Optional[PanelVariant] = None
    final_variants: List[PanelVariant] = field(default_factory=list)
    official_final_image_uri: Optional[str] = None
    approved: bool = False
    notes: str = ""

    @property
    def full_script(self) -> str:
        """Returns the full script including all text elements."""
        elements = [
            f"Panel {self.index + 1}:",
            f"Brief Description: {self.script.brief_description}" if self.script.brief_description else "",
            f"Visual Description: {self.script.visual_description}"
        ]
        
        if self.script.dialogue:
            elements.append("Dialogue:")
            elements.extend(f"  - {d}" for d in self.script.dialogue)
            
        if self.script.captions:
            elements.append("Captions:")
            elements.extend(f"  - {c}" for c in self.script.captions)
            
        if self.script.sfx:
            elements.append("Sound Effects:")
            elements.extend(f"  - {s}" for s in self.script.sfx)
            
        if self.script.thoughts:
            elements.append("Thoughts:")
            elements.extend(f"  - {t}" for t in self.script.thoughts)
            
        if self.notes:
            elements.append(f"Notes: {self.notes}")
            
        return "\n".join([e for e in elements if e])  # Filter out empty strings

    @property
    def panel_description(self) -> str:
        """Returns only the visual description for image generation."""
        return self.script.visual_description
        
    @staticmethod
    def create_empty(index: int) -> 'Panel':
        """Create an empty panel with default values."""
        return Panel(
            index=index,
            script=PanelScript(
                visual_description=f"Panel {index + 1} description",
                brief_description="",
                source_text=""
            )
        )
        
    @staticmethod
    def split_panel(original_panel: 'Panel', num_new_panels: int = 2) -> List['Panel']:
        """Split a panel into multiple panels."""
        new_panels = []
        for i in range(num_new_panels):
            new_panel = Panel(
                index=original_panel.index + i,
                script=PanelScript(
                    visual_description=f"Split from panel {original_panel.index + 1}, part {i + 1}",
                    brief_description=f"SPLIT {i + 1}/{num_new_panels} - " + original_panel.script.brief_description,
                    source_text=original_panel.script.source_text
                ),
                notes=f"Split from panel {original_panel.index + 1}"
            )
            new_panels.append(new_panel)
        return new_panels 