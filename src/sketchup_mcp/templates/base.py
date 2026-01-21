"""Base template class for woodworking project templates."""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pathlib import Path

logger = logging.getLogger("SketchupMCPServer")


@dataclass
class LumberPiece:
    """Represents a piece of lumber in the cut list."""
    name: str
    width: float  # mm
    height: float  # mm
    length: float  # mm
    quantity: int = 1
    material: str = "pine"
    notes: str = ""


@dataclass
class TemplateResult:
    """Result from template execution."""
    success: bool
    ruby_code: str = ""
    cut_list: List[LumberPiece] = field(default_factory=list)
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "ruby_code": self.ruby_code,
            "cut_list": [
                {
                    "name": p.name,
                    "width": p.width,
                    "height": p.height,
                    "length": p.length,
                    "quantity": p.quantity,
                    "material": p.material,
                    "notes": p.notes
                }
                for p in self.cut_list
            ],
            "error": self.error
        }


class BaseTemplate(ABC):
    """Abstract base class for project templates."""

    # Override in subclasses
    template_name: str = "base"
    description: str = "Base template"
    default_joinery: str = "butt"

    def __init__(
        self,
        width: float,
        height: float,
        depth: float,
        lumber: str = "90x19",
        joinery: Optional[str] = None,
        material: str = "pine",
        region: str = "australia",
        **kwargs
    ):
        """
        Initialize template with dimensions.

        Args:
            width: Width in mm
            height: Height in mm
            depth: Depth in mm
            lumber: Lumber size string (e.g., "90x19", "2x4")
            joinery: Joint type (defaults to template's default_joinery)
            material: Wood species for appearance
            region: Region for lumber standards
            **kwargs: Template-specific options
        """
        self.width = float(width)
        self.height = float(height)
        self.depth = float(depth)
        self.lumber = lumber
        self.joinery = joinery or self.default_joinery
        self.material = material
        self.region = region
        self.options = kwargs

        # Parse lumber dimensions
        self.lumber_width, self.lumber_thickness = self._parse_lumber(lumber)

    def _parse_lumber(self, lumber: str) -> tuple[float, float]:
        """Parse lumber string like '90x19' into (width, thickness) in mm."""
        try:
            parts = lumber.lower().replace("x", " ").split()
            if len(parts) == 2:
                return float(parts[0]), float(parts[1])
        except (ValueError, IndexError):
            pass
        # Default to 90x19 if parsing fails
        logger.warning(f"Could not parse lumber '{lumber}', defaulting to 90x19")
        return 90.0, 19.0

    def _mm(self, value: float) -> str:
        """Format value as Ruby mm unit."""
        return f"{value}.mm"

    def _create_board_ruby(
        self,
        name: str,
        width: float,
        height: float,
        depth: float,
        x: float = 0,
        y: float = 0,
        z: float = 0
    ) -> str:
        """Generate Ruby code to create a board as a component."""
        return f'''
# Create {name}
group = model.active_entities.add_group
group.name = "{name}"
entities = group.entities

# Create face and extrude
pts = [
  [{self._mm(x)}, {self._mm(y)}, {self._mm(z)}],
  [{self._mm(x + width)}, {self._mm(y)}, {self._mm(z)}],
  [{self._mm(x + width)}, {self._mm(y + depth)}, {self._mm(z)}],
  [{self._mm(x)}, {self._mm(y + depth)}, {self._mm(z)}]
]
face = entities.add_face(pts)
face.reverse! if face.normal.z < 0
face.pushpull({self._mm(height)})
'''

    def _apply_material_ruby(self, group_name: str, color: str) -> str:
        """Generate Ruby code to apply material to a group."""
        return f'''
# Apply material to {group_name}
{group_name.lower().replace(" ", "_")}_group = model.active_entities.grep(Sketchup::Group).find {{ |g| g.name == "{group_name}" }}
if {group_name.lower().replace(" ", "_")}_group
  mat = model.materials.add("{self.material}")
  mat.color = "{color}"
  {group_name.lower().replace(" ", "_")}_group.material = mat
end
'''

    def _wrap_in_operation(self, ruby_code: str, operation_name: str) -> str:
        """Wrap Ruby code in an undo operation."""
        return f'''
model = Sketchup.active_model
model.start_operation("{operation_name}", true)

begin
{ruby_code}
  model.commit_operation
  "Created {operation_name} successfully"
rescue => e
  model.abort_operation
  raise e
end
'''

    @abstractmethod
    def generate(self) -> TemplateResult:
        """
        Generate the Ruby code and cut list for this template.

        Returns:
            TemplateResult with ruby_code and cut_list
        """
        pass

    @classmethod
    def get_template_info(cls) -> Dict[str, Any]:
        """Return template metadata for discovery."""
        return {
            "name": cls.template_name,
            "description": cls.description,
            "default_joinery": cls.default_joinery
        }
