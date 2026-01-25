"""Base template class for woodworking project templates."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("SketchupMCPServer")


# Joint type to color mapping for visual markers
JOINT_COLORS: Dict[str, str] = {
    "dado": "#E53935",  # Red
    "rabbet": "#1E88E5",  # Blue
    "finger_joint": "#FB8C00",  # Orange
    "miter": "#8E24AA",  # Purple
    "mortise_tenon": "#43A047",  # Green
    "butt": "#757575",  # Gray
    "bracket": "#FDD835",  # Yellow
}


@dataclass
class JointMarker:
    """
    Declarative specification for a visual joint marker.

    Markers are thin colored rectangles showing where joints should be cut.
    Templates return lists of JointMarker instances, and the base class
    handles Ruby code generation uniformly.
    """

    name: str  # Descriptive name (e.g., "Dado - Shelf 1 Left")
    joint_type: str  # Key into JOINT_COLORS (e.g., "dado", "rabbet")
    x: float  # X position in mm
    y: float  # Y position in mm
    z: float  # Z position in mm
    width: float  # Width in mm
    height: float  # Height in mm (typically 0.5 for thin marker)
    depth: float  # Depth in mm

    @property
    def color(self) -> str:
        """Get the hex color for this joint type."""
        return JOINT_COLORS.get(self.joint_type, JOINT_COLORS["butt"])


@dataclass
class LumberPiece:
    """
    Represents a piece of lumber in the cut list.

    Dimension semantics follow lumber industry convention:
    - width: The widest face dimension (board width)
    - height: The thickness of the board
    - length: The longest dimension (grain direction)

    All dimensions are in millimeters.
    """

    name: str
    width: float  # mm - board width (widest face)
    height: float  # mm - board thickness
    length: float  # mm - board length (grain direction)
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
                    "notes": p.notes,
                }
                for p in self.cut_list
            ],
            "error": self.error,
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
        show_joints: bool = True,
        **kwargs,
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
            show_joints: Whether to show visual joint markers (default True)
            **kwargs: Template-specific options
        """
        self.width = float(width)
        self.height = float(height)
        self.depth = float(depth)
        self.lumber = lumber
        self.joinery = joinery or self.default_joinery
        self.material = material
        self.region = region
        self.show_joints = show_joints
        self.options = kwargs

        # Parse lumber dimensions
        self.lumber_width, self.lumber_thickness = self._parse_lumber(lumber)

    def _parse_lumber(self, lumber: str) -> tuple[float, float]:
        """
        Parse lumber string like '90x19' into (width, thickness) in mm.

        Expects metric dimensions in WIDTHxTHICKNESS format.
        Does not convert imperial dimensions (e.g., '2x4') - use metric values.

        Args:
            lumber: Lumber size string (e.g., '90x19', '100x25')

        Returns:
            Tuple of (width, thickness) in mm

        Raises:
            ValueError: If lumber format is invalid or dimensions are not positive
        """
        try:
            parts = lumber.lower().replace("x", " ").split()
            if len(parts) != 2:
                raise ValueError(
                    f"Invalid lumber format '{lumber}'. "
                    f"Expected format: 'WIDTHxTHICKNESS' (e.g., '90x19', '100x25')"
                )
            width = float(parts[0])
            thickness = float(parts[1])
            if width <= 0 or thickness <= 0:
                raise ValueError(
                    f"Lumber dimensions must be positive. "
                    f"Got: width={width}, thickness={thickness}"
                )
            return width, thickness
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(
                f"Could not parse lumber '{lumber}'. "
                f"Expected numeric dimensions like '90x19'. Error: {e}"
            )

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
        z: float = 0,
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

    def _create_joint_marker_ruby(self, marker: "JointMarker") -> str:
        """
        Generate Ruby code to create a visual joint marker.

        Markers are thin colored rectangles showing joint positions.
        They are created as separate groups with colored materials.

        Args:
            marker: JointMarker specification with position and dimensions

        Returns:
            Ruby code string to create the marker
        """
        # Sanitize name for Ruby variable
        var_name = marker.name.lower().replace(" ", "_").replace("-", "_")
        mat_name = f"Joint_{marker.joint_type}"

        return f'''
# Create joint marker: {marker.name}
marker_group = model.active_entities.add_group
marker_group.name = "Joint: {marker.name}"
marker_ents = marker_group.entities

marker_pts = [
  [{self._mm(marker.x)}, {self._mm(marker.y)}, {self._mm(marker.z)}],
  [{self._mm(marker.x + marker.width)}, {self._mm(marker.y)}, {self._mm(marker.z)}],
  [{self._mm(marker.x + marker.width)}, {self._mm(marker.y + marker.depth)}, {self._mm(marker.z)}],
  [{self._mm(marker.x)}, {self._mm(marker.y + marker.depth)}, {self._mm(marker.z)}]
]
marker_face = marker_ents.add_face(marker_pts)
marker_face.reverse! if marker_face.normal.z < 0
marker_face.pushpull({self._mm(marker.height)})

# Apply colored material
{var_name}_mat = model.materials["{mat_name}"] || model.materials.add("{mat_name}")
{var_name}_mat.color = "{marker.color}"
marker_group.material = {var_name}_mat
'''

    def _get_joint_markers(self) -> List["JointMarker"]:
        """
        Return list of joint markers for this template.

        Override in subclasses to define template-specific marker positions.
        This is the hook that templates implement to declaratively specify
        where joint markers should appear.

        Returns:
            List of JointMarker instances (empty by default)
        """
        return []

    def _generate_markers_ruby(self) -> str:
        """
        Generate Ruby code for all joint markers if show_joints is enabled.

        Calls _get_joint_markers() to get the declarative marker specs,
        then generates Ruby code for each marker.

        Returns:
            Ruby code string for all markers, or empty string if disabled
        """
        if not self.show_joints:
            return ""

        markers = self._get_joint_markers()
        if not markers:
            return ""

        ruby_parts = ["\n# Joint markers"]
        for marker in markers:
            ruby_parts.append(self._create_joint_marker_ruby(marker))

        return "\n".join(ruby_parts)

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
            "default_joinery": cls.default_joinery,
        }
