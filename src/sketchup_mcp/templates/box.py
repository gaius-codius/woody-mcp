"""Box template - storage boxes with panels positioned for finger joint assembly."""

import logging
from typing import Optional

from .base import BaseTemplate, TemplateResult, LumberPiece

logger = logging.getLogger("SketchupMCPServer")


class BoxTemplate(BaseTemplate):
    """Template for creating boxes with panels positioned for joinery."""

    template_name = "box"
    description = "Storage box with optional lid"
    default_joinery = "finger_joint"

    def __init__(
        self,
        width: float = 200,
        height: float = 100,
        depth: float = 150,
        has_lid: bool = True,
        lumber: str = "90x12",
        joinery: Optional[str] = None,
        material: str = "pine",
        region: str = "australia",
        **kwargs,
    ):
        """
        Create a box template.

        Args:
            width: Width in mm (default 200)
            height: Height in mm (default 100)
            depth: Depth in mm (default 150)
            has_lid: Include a lid (default True)
            lumber: Lumber size (default "90x12")
            joinery: Joint type (default "finger_joint")
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
        self.has_lid = has_lid

    def generate(self) -> TemplateResult:
        """Generate box Ruby code and cut list."""
        try:
            # Use parsed lumber dimensions
            wall_thickness = self.lumber_thickness
            bottom_thickness = self.lumber_thickness

            # Interior dimensions
            interior_width = self.width - (2 * wall_thickness)
            interior_depth = self.depth - (2 * wall_thickness)
            box_height = self.height - bottom_thickness
            if self.has_lid:
                box_height -= wall_thickness  # Account for lid

            # Validate dimensions
            if box_height <= 0:
                min_height = (
                    bottom_thickness + wall_thickness + 1
                    if self.has_lid
                    else bottom_thickness + 1
                )
                return TemplateResult(
                    success=False,
                    error=f"Height {self.height}mm is too small for a box with {wall_thickness}mm lumber"
                    f"{' and lid' if self.has_lid else ''}. Minimum height required: {min_height}mm",
                )

            if interior_width <= 0 or interior_depth <= 0:
                min_dim = (2 * wall_thickness) + 1
                return TemplateResult(
                    success=False,
                    error=f"Width ({self.width}mm) or depth ({self.depth}mm) is too small for {wall_thickness}mm lumber. "
                    f"Minimum required: {min_dim}mm",
                )

            # Build cut list
            cut_list = [
                LumberPiece(
                    name="Front/Back Panel",
                    width=self.lumber_width,
                    height=self.width,
                    length=box_height,
                    quantity=2,
                    material=self.material,
                    notes=f"Front and back, {self.joinery}",
                ),
                LumberPiece(
                    name="Side Panel",
                    width=self.lumber_width,
                    height=interior_depth,
                    length=box_height,
                    quantity=2,
                    material=self.material,
                    notes=f"Left and right sides, {self.joinery}",
                ),
                LumberPiece(
                    name="Bottom",
                    width=self.lumber_width,
                    height=interior_width,
                    length=interior_depth,
                    quantity=1,
                    material=self.material,
                    notes="Bottom panel, sized to fit inside walls",
                ),
            ]

            if self.has_lid:
                cut_list.append(
                    LumberPiece(
                        name="Lid",
                        width=self.lumber_width,
                        height=self.width + 10,  # Slight overhang
                        length=self.depth + 10,
                        quantity=1,
                        material=self.material,
                        notes="Lid with slight overhang",
                    )
                )

            # Generate Ruby code
            ruby_parts = []

            # Front panel
            ruby_parts.append(
                self._create_board_ruby(
                    name="Front",
                    width=self.width,
                    height=box_height,
                    depth=wall_thickness,
                    x=0,
                    y=0,
                    z=bottom_thickness,
                )
            )

            # Back panel
            ruby_parts.append(
                self._create_board_ruby(
                    name="Back",
                    width=self.width,
                    height=box_height,
                    depth=wall_thickness,
                    x=0,
                    y=self.depth - wall_thickness,
                    z=bottom_thickness,
                )
            )

            # Left side
            ruby_parts.append(
                self._create_board_ruby(
                    name="Left Side",
                    width=wall_thickness,
                    height=box_height,
                    depth=interior_depth,
                    x=0,
                    y=wall_thickness,
                    z=bottom_thickness,
                )
            )

            # Right side
            ruby_parts.append(
                self._create_board_ruby(
                    name="Right Side",
                    width=wall_thickness,
                    height=box_height,
                    depth=interior_depth,
                    x=self.width - wall_thickness,
                    y=wall_thickness,
                    z=bottom_thickness,
                )
            )

            # Bottom
            ruby_parts.append(
                self._create_board_ruby(
                    name="Bottom",
                    width=interior_width,
                    height=bottom_thickness,
                    depth=interior_depth,
                    x=wall_thickness,
                    y=wall_thickness,
                    z=0,
                )
            )

            # Lid (offset slightly above)
            if self.has_lid:
                lid_z = bottom_thickness + box_height + 20  # 20mm gap for visibility
                ruby_parts.append(
                    self._create_board_ruby(
                        name="Lid",
                        width=self.width + 10,
                        height=wall_thickness,
                        depth=self.depth + 10,
                        x=-5,
                        y=-5,
                        z=lid_z,
                    )
                )

            # Combine and wrap
            ruby_code = "\n".join(ruby_parts)
            ruby_code = self._wrap_in_operation(
                ruby_code, f"Box {int(self.width)}x{int(self.height)}x{int(self.depth)}"
            )

            return TemplateResult(success=True, ruby_code=ruby_code, cut_list=cut_list)

        except ValueError as e:
            logger.warning(f"Box template validation error: {e}")
            return TemplateResult(success=False, error=str(e))
        except Exception as e:
            logger.exception(f"Box template unexpected error: {e}")
            raise
