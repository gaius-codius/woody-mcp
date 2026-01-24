"""Cabinet template - storage cabinet with optional doors and shelves."""

import logging
from typing import Optional

from .base import BaseTemplate, TemplateResult, LumberPiece

logger = logging.getLogger("SketchupMCPServer")


class CabinetTemplate(BaseTemplate):
    """Template for creating storage cabinets."""

    template_name = "cabinet"
    description = "Storage cabinet with optional doors"
    default_joinery = "dado"

    def __init__(
        self,
        width: float = 600,
        height: float = 800,
        depth: float = 400,
        has_doors: bool = True,
        door_count: int = 2,
        shelf_count: int = 2,
        has_base: bool = True,
        base_height: float = 80,
        lumber: str = "90x19",
        joinery: Optional[str] = None,
        material: str = "pine",
        region: str = "australia",
        **kwargs,
    ):
        """
        Create a cabinet template.

        Args:
            width: Total width in mm (default 600)
            height: Total height in mm (default 800)
            depth: Depth in mm (default 400)
            has_doors: Include doors (default True)
            door_count: Number of doors, 1 or 2 (default 2)
            shelf_count: Number of internal shelves (default 2)
            has_base: Include toe kick base (default True)
            base_height: Height of toe kick in mm (default 80)
            lumber: Lumber size (default "90x19")
            joinery: Joint type (default "dado")
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
        self.has_doors = has_doors
        self.door_count = max(1, min(2, int(door_count)))
        self.shelf_count = max(0, int(shelf_count))
        self.has_base = has_base
        self.base_height = base_height

    def generate(self) -> TemplateResult:
        """Generate cabinet Ruby code and cut list."""
        try:
            # Calculate dimensions
            panel_thickness = self.lumber_thickness
            door_thickness = self.lumber_thickness

            # Carcass dimensions
            carcass_height = self.height - (self.base_height if self.has_base else 0)
            interior_width = self.width - (2 * panel_thickness)
            interior_depth = self.depth - panel_thickness  # Back panel inset

            # Validate dimensions
            if interior_width <= 0:
                return TemplateResult(
                    success=False,
                    error=f"Cabinet width {self.width}mm too small for {panel_thickness}mm panels. "
                    f"Minimum: {2 * panel_thickness + 50}mm",
                )

            if carcass_height <= panel_thickness * 2:
                return TemplateResult(
                    success=False,
                    error=f"Cabinet height {self.height}mm too small with {self.base_height}mm base. "
                    f"Minimum: {self.base_height + panel_thickness * 3}mm",
                )

            # Shelf spacing
            available_height = carcass_height - (2 * panel_thickness)
            if self.shelf_count > 0:
                shelf_spacing = available_height / (self.shelf_count + 1)
            else:
                shelf_spacing = available_height

            # Door dimensions (overlay style)
            door_width = (
                self.width / self.door_count if self.door_count > 1 else self.width
            )
            door_height = carcass_height

            # Build cut list
            cut_list = [
                LumberPiece(
                    name="Side Panel",
                    width=self.lumber_width,
                    height=carcass_height,
                    length=self.depth,
                    quantity=2,
                    material=self.material,
                    notes=f"Left and right sides, {self.joinery} for shelves",
                ),
                LumberPiece(
                    name="Top Panel",
                    width=self.lumber_width,
                    height=interior_width,
                    length=self.depth,
                    quantity=1,
                    material=self.material,
                    notes="Top of carcass",
                ),
                LumberPiece(
                    name="Bottom Panel",
                    width=self.lumber_width,
                    height=interior_width,
                    length=self.depth,
                    quantity=1,
                    material=self.material,
                    notes="Bottom of carcass",
                ),
                LumberPiece(
                    name="Back Panel",
                    width=self.lumber_width,
                    height=interior_width,
                    length=carcass_height - (2 * panel_thickness),
                    quantity=1,
                    material=self.material,
                    notes="Back panel, rabbeted into sides",
                ),
            ]

            if self.shelf_count > 0:
                cut_list.append(
                    LumberPiece(
                        name="Shelf",
                        width=self.lumber_width,
                        height=interior_width,
                        length=interior_depth - 10,  # Slight inset from front
                        quantity=self.shelf_count,
                        material=self.material,
                        notes=f"Adjustable shelves, {self.joinery}",
                    )
                )

            if self.has_base:
                cut_list.append(
                    LumberPiece(
                        name="Base/Toe Kick",
                        width=self.lumber_width,
                        height=self.width - (2 * panel_thickness),
                        length=self.base_height,
                        quantity=1,
                        material=self.material,
                        notes="Toe kick, recessed 50mm from front",
                    )
                )

            if self.has_doors:
                cut_list.append(
                    LumberPiece(
                        name="Door",
                        width=self.lumber_width,
                        height=door_width - 3,  # 3mm gap between doors
                        length=door_height - 3,
                        quantity=self.door_count,
                        material=self.material,
                        notes="Overlay doors with hinges",
                    )
                )

            # Generate Ruby code
            ruby_parts = []

            # Base Z offset
            base_z = self.base_height if self.has_base else 0

            # Left side
            ruby_parts.append(
                self._create_board_ruby(
                    name="Left Side",
                    width=panel_thickness,
                    height=carcass_height,
                    depth=self.depth,
                    x=0,
                    y=0,
                    z=base_z,
                )
            )

            # Right side
            ruby_parts.append(
                self._create_board_ruby(
                    name="Right Side",
                    width=panel_thickness,
                    height=carcass_height,
                    depth=self.depth,
                    x=self.width - panel_thickness,
                    y=0,
                    z=base_z,
                )
            )

            # Top
            ruby_parts.append(
                self._create_board_ruby(
                    name="Top",
                    width=interior_width,
                    height=panel_thickness,
                    depth=self.depth,
                    x=panel_thickness,
                    y=0,
                    z=base_z + carcass_height - panel_thickness,
                )
            )

            # Bottom
            ruby_parts.append(
                self._create_board_ruby(
                    name="Bottom",
                    width=interior_width,
                    height=panel_thickness,
                    depth=self.depth,
                    x=panel_thickness,
                    y=0,
                    z=base_z,
                )
            )

            # Back panel (inset from back edge)
            ruby_parts.append(
                self._create_board_ruby(
                    name="Back Panel",
                    width=interior_width,
                    height=carcass_height - (2 * panel_thickness),
                    depth=panel_thickness,
                    x=panel_thickness,
                    y=self.depth - panel_thickness,
                    z=base_z + panel_thickness,
                )
            )

            # Shelves
            for i in range(self.shelf_count):
                shelf_z = base_z + panel_thickness + (i + 1) * shelf_spacing
                ruby_parts.append(
                    self._create_board_ruby(
                        name=f"Shelf {i + 1}",
                        width=interior_width,
                        height=panel_thickness,
                        depth=interior_depth - 10,
                        x=panel_thickness,
                        y=0,
                        z=shelf_z,
                    )
                )

            # Base/toe kick (recessed 50mm from front)
            if self.has_base:
                ruby_parts.append(
                    self._create_board_ruby(
                        name="Toe Kick",
                        width=self.width - (2 * panel_thickness),
                        height=self.base_height,
                        depth=panel_thickness,
                        x=panel_thickness,
                        y=50,
                        z=0,
                    )
                )

            # Doors (offset slightly in front for visibility)
            if self.has_doors:
                door_gap = 3
                for i in range(self.door_count):
                    door_x = i * door_width + (door_gap / 2)
                    actual_door_width = door_width - door_gap
                    ruby_parts.append(
                        self._create_board_ruby(
                            name=f"Door {i + 1}",
                            width=actual_door_width,
                            height=door_height - door_gap,
                            depth=door_thickness,
                            x=door_x,
                            y=-20,  # Offset in front for visibility
                            z=base_z + (door_gap / 2),
                        )
                    )

            # Combine and wrap
            ruby_code = "\n".join(ruby_parts)
            ruby_code = self._wrap_in_operation(
                ruby_code,
                f"Cabinet {int(self.width)}x{int(self.height)}x{int(self.depth)}",
            )

            return TemplateResult(success=True, ruby_code=ruby_code, cut_list=cut_list)

        except ValueError as e:
            logger.warning(f"Cabinet template validation error: {e}")
            return TemplateResult(success=False, error=str(e))
        except Exception as e:
            logger.exception(f"Cabinet template unexpected error: {e}")
            raise
