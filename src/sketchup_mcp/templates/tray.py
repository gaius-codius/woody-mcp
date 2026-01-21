"""Tray template - serving tray with handles and optional dividers."""

import logging
from typing import Optional

from .base import BaseTemplate, TemplateResult, LumberPiece

logger = logging.getLogger("SketchupMCPServer")


class TrayTemplate(BaseTemplate):
    """Template for creating serving trays."""

    template_name = "tray"
    description = "Serving tray with handles"
    default_joinery = "rabbet"

    def __init__(
        self,
        width: float = 400,
        height: float = 50,
        depth: float = 300,
        has_handles: bool = True,
        wall_height: float = 40,
        has_dividers: bool = False,
        divider_count: int = 1,
        lumber: str = "90x12",
        joinery: Optional[str] = None,
        material: str = "walnut",
        region: str = "australia",
        **kwargs,
    ):
        """
        Create a tray template.

        Args:
            width: Total width in mm (default 400)
            height: Total height in mm (default 50)
            depth: Depth in mm (default 300)
            has_handles: Include handle cutouts in end walls (default True)
            wall_height: Height of tray walls in mm (default 40)
            has_dividers: Include internal dividers (default False)
            divider_count: Number of dividers if has_dividers (default 1)
            lumber: Lumber size (default "90x12")
            joinery: Joint type (default "rabbet")
            material: Wood species (default "walnut")
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
        self.has_handles = has_handles
        self.wall_height = min(wall_height, height - 5)  # Leave room for bottom
        self.has_dividers = has_dividers
        self.divider_count = max(1, int(divider_count))

    def generate(self) -> TemplateResult:
        """Generate tray Ruby code and cut list."""
        try:
            # Calculate dimensions
            wall_thickness = self.lumber_thickness
            bottom_thickness = self.lumber_thickness

            # Interior dimensions
            interior_width = self.width - (2 * wall_thickness)
            interior_depth = self.depth - (2 * wall_thickness)

            # Validate dimensions
            if interior_width <= 0 or interior_depth <= 0:
                return TemplateResult(
                    success=False,
                    error=f"Tray dimensions ({self.width}x{self.depth}mm) too small for "
                    f"{wall_thickness}mm walls. Minimum: {2 * wall_thickness + 50}mm each side.",
                )

            if self.wall_height < 20:
                return TemplateResult(
                    success=False,
                    error=f"Wall height {self.wall_height}mm too small. Minimum: 20mm",
                )

            # Build cut list
            cut_list = [
                LumberPiece(
                    name="Bottom",
                    width=self.lumber_width,
                    height=interior_width,
                    length=interior_depth,
                    quantity=1,
                    material=self.material,
                    notes="Bottom panel, rabbeted into walls",
                ),
                LumberPiece(
                    name="Long Wall",
                    width=wall_thickness,
                    height=self.width,
                    length=self.wall_height,
                    quantity=2,
                    material=self.material,
                    notes=f"Front and back walls, {self.joinery} corners",
                ),
                LumberPiece(
                    name="End Wall",
                    width=wall_thickness,
                    height=interior_depth,
                    length=self.wall_height,
                    quantity=2,
                    material=self.material,
                    notes="End walls with handle cutouts"
                    if self.has_handles
                    else "End walls",
                ),
            ]

            if self.has_dividers:
                divider_length = interior_depth - 10  # Slight gap
                cut_list.append(
                    LumberPiece(
                        name="Divider",
                        width=wall_thickness,
                        height=divider_length,
                        length=self.wall_height - 10,
                        quantity=self.divider_count,
                        material=self.material,
                        notes="Internal dividers",
                    )
                )

            # Generate Ruby code
            ruby_parts = []

            # Bottom panel
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

            # Front wall (long side)
            ruby_parts.append(
                self._create_board_ruby(
                    name="Front Wall",
                    width=self.width,
                    height=self.wall_height,
                    depth=wall_thickness,
                    x=0,
                    y=0,
                    z=bottom_thickness,
                )
            )

            # Back wall (long side)
            ruby_parts.append(
                self._create_board_ruby(
                    name="Back Wall",
                    width=self.width,
                    height=self.wall_height,
                    depth=wall_thickness,
                    x=0,
                    y=self.depth - wall_thickness,
                    z=bottom_thickness,
                )
            )

            # Left end wall (short side, between front and back)
            ruby_parts.append(
                self._create_board_ruby(
                    name="Left End Wall",
                    width=wall_thickness,
                    height=self.wall_height,
                    depth=interior_depth,
                    x=0,
                    y=wall_thickness,
                    z=bottom_thickness,
                )
            )

            # Right end wall
            ruby_parts.append(
                self._create_board_ruby(
                    name="Right End Wall",
                    width=wall_thickness,
                    height=self.wall_height,
                    depth=interior_depth,
                    x=self.width - wall_thickness,
                    y=wall_thickness,
                    z=bottom_thickness,
                )
            )

            # Dividers (vertical partitions along width)
            if self.has_dividers:
                section_width = interior_width / (self.divider_count + 1)
                for i in range(self.divider_count):
                    divider_x = (
                        wall_thickness + (i + 1) * section_width - wall_thickness / 2
                    )
                    ruby_parts.append(
                        self._create_board_ruby(
                            name=f"Divider {i + 1}",
                            width=wall_thickness,
                            height=self.wall_height - 10,
                            depth=interior_depth - 10,
                            x=divider_x,
                            y=wall_thickness + 5,
                            z=bottom_thickness,
                        )
                    )

            # Combine and wrap
            ruby_code = "\n".join(ruby_parts)
            handle_text = " with Handles" if self.has_handles else ""
            ruby_code = self._wrap_in_operation(
                ruby_code,
                f"Serving Tray{handle_text} {int(self.width)}x{int(self.depth)}",
            )

            return TemplateResult(success=True, ruby_code=ruby_code, cut_list=cut_list)

        except ValueError as e:
            logger.warning(f"Tray template validation error: {e}")
            return TemplateResult(success=False, error=str(e))
        except Exception as e:
            logger.exception(f"Tray template unexpected error: {e}")
            raise
