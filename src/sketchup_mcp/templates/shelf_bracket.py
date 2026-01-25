"""Shelf bracket template - wall-mounted shelf with triangular brackets."""

import logging
import math
from typing import List, Optional, Literal

from .base import BaseTemplate, TemplateResult, LumberPiece, JointMarker

logger = logging.getLogger("SketchupMCPServer")


class ShelfBracketTemplate(BaseTemplate):
    """Template for creating wall-mounted shelves with brackets."""

    template_name = "shelf_bracket"
    description = "Wall-mounted shelf with brackets"
    default_joinery = "bracket"

    def __init__(
        self,
        width: float = 600,
        height: float = 200,
        depth: float = 200,
        bracket_style: Literal["triangle", "L_bracket", "corbel"] = "triangle",
        bracket_count: int = 2,
        has_shelf: bool = True,
        lumber: str = "90x19",
        joinery: Optional[str] = None,
        material: str = "pine",
        region: str = "australia",
        **kwargs,
    ):
        """
        Create a shelf bracket template.

        Args:
            width: Shelf length in mm (default 600)
            height: Bracket vertical height in mm (default 200)
            depth: Bracket/shelf depth in mm (default 200)
            bracket_style: Style - "triangle", "L_bracket", or "corbel"
            bracket_count: Number of brackets (default 2)
            has_shelf: Include shelf board (default True)
            lumber: Lumber size (default "90x19")
            joinery: Joint type (default "bracket")
            material: Wood species (default "pine")
            region: Region for lumber (default "australia")
        """
        super().__init__(
            width=width,
            height=height,
            depth=depth,
            lumber=lumber,
            joinery=joinery,
            material=material,
            region=region,
            **kwargs,
        )
        self.bracket_style = bracket_style
        self.bracket_count = max(2, int(bracket_count))
        self.has_shelf = has_shelf

        # Store computed dimensions for _get_joint_markers()
        self._bracket_positions: List[float] = []
        self._board_thickness: float = 0
        self._board_width: float = 0
        self._vertical_length: float = 0

    def _get_joint_markers(self) -> List[JointMarker]:
        """
        Return bracket joint markers where shelf meets brackets.

        Markers appear on bracket horizontals where shelf sits.
        """
        if not self._bracket_positions or self._board_thickness <= 0:
            return []

        markers = []
        marker_thickness = 0.5

        for i, bracket_x in enumerate(self._bracket_positions):
            # Marker on top of horizontal where shelf sits
            markers.append(
                JointMarker(
                    name=f"Bracket {i + 1} Shelf",
                    joint_type=self.joinery,
                    x=bracket_x,
                    y=0,
                    z=self._vertical_length,
                    width=self._board_thickness,
                    height=marker_thickness,
                    depth=self.depth,
                )
            )

        return markers

    def generate(self) -> TemplateResult:
        """Generate shelf bracket Ruby code and cut list."""
        try:
            # Calculate dimensions
            board_thickness = self.lumber_thickness
            board_width = self.lumber_width

            # Bracket dimensions
            vertical_length = self.height
            horizontal_length = self.depth
            # Diagonal for triangle bracket (pythagorean)
            diagonal_length = math.sqrt(vertical_length**2 + horizontal_length**2)

            # Shelf dimensions
            shelf_thickness = board_thickness
            shelf_depth = self.depth

            # Bracket spacing (bracket_count is always >= 2)
            bracket_spacing = (self.width - board_thickness) / (self.bracket_count - 1)

            # Validate dimensions
            if vertical_length < 100:
                return TemplateResult(
                    success=False,
                    error=f"Bracket height {vertical_length}mm too small. Minimum: 100mm",
                )

            if horizontal_length < 100:
                return TemplateResult(
                    success=False,
                    error=f"Bracket depth {horizontal_length}mm too small. Minimum: 100mm",
                )

            # Store dimensions for _get_joint_markers()
            self._board_thickness = board_thickness
            self._board_width = board_width
            self._vertical_length = vertical_length
            self._bracket_positions = [
                i * bracket_spacing if self.bracket_count > 1 else 0
                for i in range(self.bracket_count)
            ]

            # Build cut list
            cut_list = []

            if self.bracket_style == "triangle":
                cut_list.extend(
                    [
                        LumberPiece(
                            name="Vertical (Wall Mount)",
                            width=board_thickness,
                            height=board_width,
                            length=vertical_length,
                            quantity=self.bracket_count,
                            material=self.material,
                            notes="Mounts to wall with screws",
                        ),
                        LumberPiece(
                            name="Horizontal (Support)",
                            width=board_thickness,
                            height=board_width,
                            length=horizontal_length,
                            quantity=self.bracket_count,
                            material=self.material,
                            notes="Supports shelf, attached to vertical",
                        ),
                        LumberPiece(
                            name="Diagonal (Brace)",
                            width=board_thickness,
                            height=board_width,
                            length=diagonal_length,
                            quantity=self.bracket_count,
                            material=self.material,
                            notes=f"Angled cuts on both ends ({math.degrees(math.atan2(vertical_length, horizontal_length)):.1f}°)",
                        ),
                    ]
                )
            elif self.bracket_style == "L_bracket":
                cut_list.extend(
                    [
                        LumberPiece(
                            name="Vertical (Wall Mount)",
                            width=board_thickness,
                            height=board_width,
                            length=vertical_length,
                            quantity=self.bracket_count,
                            material=self.material,
                            notes="Mounts to wall",
                        ),
                        LumberPiece(
                            name="Horizontal (Support)",
                            width=board_thickness,
                            height=board_width,
                            length=horizontal_length,
                            quantity=self.bracket_count,
                            material=self.material,
                            notes="Supports shelf, butt joint to vertical",
                        ),
                    ]
                )
            else:  # corbel
                cut_list.append(
                    LumberPiece(
                        name="Corbel Bracket",
                        width=board_thickness,
                        height=horizontal_length,
                        length=vertical_length,
                        quantity=self.bracket_count,
                        material=self.material,
                        notes="Decorative corbel shape, cut from single board",
                    )
                )

            if self.has_shelf:
                cut_list.append(
                    LumberPiece(
                        name="Shelf Board",
                        width=board_thickness,
                        height=self.width,
                        length=shelf_depth,
                        quantity=1,
                        material=self.material,
                        notes="Sits on bracket horizontals (yellow markers)",
                    )
                )

            # Generate Ruby code
            ruby_parts = []

            # Generate brackets at spacing intervals
            for i in range(self.bracket_count):
                bracket_x = i * bracket_spacing if self.bracket_count > 1 else 0

                if self.bracket_style == "triangle":
                    # Vertical piece (against wall at y=depth)
                    ruby_parts.append(
                        self._create_board_ruby(
                            name=f"Vertical {i + 1}",
                            width=board_thickness,
                            height=vertical_length,
                            depth=board_width,
                            x=bracket_x,
                            y=self.depth - board_width,
                            z=0,
                        )
                    )

                    # Horizontal piece (at top, extending forward)
                    ruby_parts.append(
                        self._create_board_ruby(
                            name=f"Horizontal {i + 1}",
                            width=board_thickness,
                            height=board_width,
                            depth=horizontal_length,
                            x=bracket_x,
                            y=0,
                            z=vertical_length - board_width,
                        )
                    )

                    # Diagonal brace (simplified as a box - actual would be angled)
                    # Position from bottom-front to top-back corner
                    ruby_parts.append(
                        self._create_board_ruby(
                            name=f"Diagonal {i + 1}",
                            width=board_thickness,
                            height=board_width,
                            depth=diagonal_length * 0.8,  # Approximate
                            x=bracket_x,
                            y=board_width,
                            z=board_width,
                        )
                    )

                elif self.bracket_style == "L_bracket":
                    # Vertical piece
                    ruby_parts.append(
                        self._create_board_ruby(
                            name=f"Vertical {i + 1}",
                            width=board_thickness,
                            height=vertical_length,
                            depth=board_width,
                            x=bracket_x,
                            y=self.depth - board_width,
                            z=0,
                        )
                    )

                    # Horizontal piece
                    ruby_parts.append(
                        self._create_board_ruby(
                            name=f"Horizontal {i + 1}",
                            width=board_thickness,
                            height=board_width,
                            depth=horizontal_length,
                            x=bracket_x,
                            y=0,
                            z=vertical_length - board_width,
                        )
                    )

                else:  # corbel - simplified as solid block
                    ruby_parts.append(
                        self._create_board_ruby(
                            name=f"Corbel {i + 1}",
                            width=board_thickness,
                            height=vertical_length,
                            depth=horizontal_length,
                            x=bracket_x,
                            y=0,
                            z=0,
                        )
                    )

            # Shelf board (sits on top of brackets)
            if self.has_shelf:
                shelf_z = (
                    vertical_length - board_width + board_width
                )  # On top of horizontal
                ruby_parts.append(
                    self._create_board_ruby(
                        name="Shelf",
                        width=self.width,
                        height=shelf_thickness,
                        depth=shelf_depth,
                        x=0,
                        y=0,
                        z=vertical_length,
                    )
                )

            # Add joint markers
            ruby_parts.append(self._generate_markers_ruby())

            # Combine and wrap
            ruby_code = "\n".join(ruby_parts)
            style_name = self.bracket_style.replace("_", " ").title()
            ruby_code = self._wrap_in_operation(
                ruby_code,
                f"{style_name} Shelf {int(self.width)}mm",
            )

            return TemplateResult(success=True, ruby_code=ruby_code, cut_list=cut_list)

        except ValueError as e:
            logger.warning(f"Shelf bracket template validation error: {e}")
            return TemplateResult(success=False, error=str(e))
        except Exception as e:
            logger.exception(f"Shelf bracket template unexpected error: {e}")
            raise
