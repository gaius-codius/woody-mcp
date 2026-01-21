"""Bookshelf template - adjustable shelves with dado joints."""

import logging
from typing import Optional

from .base import BaseTemplate, TemplateResult, LumberPiece

logger = logging.getLogger("SketchupMCPServer")


class BookshelfTemplate(BaseTemplate):
    """Template for creating bookshelves with adjustable shelves."""

    template_name = "bookshelf"
    description = "Bookshelf with adjustable shelves"
    default_joinery = "dado"

    def __init__(
        self,
        width: float = 600,
        height: float = 1000,
        depth: float = 300,
        shelves: int = 3,
        lumber: str = "90x19",
        joinery: Optional[str] = None,
        material: str = "pine",
        region: str = "australia",
        **kwargs
    ):
        """
        Create a bookshelf template.

        Args:
            width: Total width in mm (default 600)
            height: Total height in mm (default 1000)
            depth: Depth in mm (default 300)
            shelves: Number of shelves (default 3)
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
            **kwargs
        )
        self.shelves = max(1, int(shelves))

    def generate(self) -> TemplateResult:
        """Generate bookshelf Ruby code and cut list."""
        try:
            # Calculate dimensions
            side_thickness = self.lumber_thickness
            shelf_thickness = self.lumber_thickness

            # Interior width (between sides)
            interior_width = self.width - (2 * side_thickness)

            # Shelf spacing (evenly distributed)
            total_shelf_height = self.shelves * shelf_thickness
            top_bottom_thickness = 2 * shelf_thickness  # Account for top and bottom panels
            available_height = self.height - total_shelf_height - top_bottom_thickness

            # Validate dimensions
            if available_height <= 0:
                min_height = total_shelf_height + top_bottom_thickness + (self.shelves + 1)
                return TemplateResult(
                    success=False,
                    error=f"Height {self.height}mm is too small for {self.shelves} shelves with {shelf_thickness}mm lumber. "
                          f"Minimum height required: {min_height}mm"
                )

            shelf_spacing = available_height / (self.shelves + 1)

            # Build cut list
            cut_list = [
                LumberPiece(
                    name="Side Panel",
                    width=self.lumber_width,
                    height=self.height,
                    length=self.depth,
                    quantity=2,
                    material=self.material,
                    notes="Left and right sides"
                ),
                LumberPiece(
                    name="Shelf",
                    width=self.lumber_width,
                    height=interior_width,
                    length=self.depth,
                    quantity=self.shelves,
                    material=self.material,
                    notes=f"Adjustable shelves, {self.joinery} joints"
                ),
                LumberPiece(
                    name="Top Panel",
                    width=self.lumber_width,
                    height=interior_width,
                    length=self.depth,
                    quantity=1,
                    material=self.material,
                    notes="Top of bookshelf"
                ),
                LumberPiece(
                    name="Bottom Panel",
                    width=self.lumber_width,
                    height=interior_width,
                    length=self.depth,
                    quantity=1,
                    material=self.material,
                    notes="Bottom of bookshelf"
                )
            ]

            # Generate Ruby code
            ruby_parts = []

            # Left side
            ruby_parts.append(self._create_board_ruby(
                name="Left Side",
                width=side_thickness,
                height=self.height,
                depth=self.depth,
                x=0, y=0, z=0
            ))

            # Right side
            ruby_parts.append(self._create_board_ruby(
                name="Right Side",
                width=side_thickness,
                height=self.height,
                depth=self.depth,
                x=self.width - side_thickness, y=0, z=0
            ))

            # Top
            ruby_parts.append(self._create_board_ruby(
                name="Top",
                width=interior_width,
                height=shelf_thickness,
                depth=self.depth,
                x=side_thickness, y=0, z=self.height - shelf_thickness
            ))

            # Bottom
            ruby_parts.append(self._create_board_ruby(
                name="Bottom",
                width=interior_width,
                height=shelf_thickness,
                depth=self.depth,
                x=side_thickness, y=0, z=0
            ))

            # Shelves - position above bottom panel
            for i in range(self.shelves):
                shelf_z = shelf_thickness + (i + 1) * shelf_spacing + (i * shelf_thickness)
                ruby_parts.append(self._create_board_ruby(
                    name=f"Shelf {i + 1}",
                    width=interior_width,
                    height=shelf_thickness,
                    depth=self.depth,
                    x=side_thickness, y=0, z=shelf_z
                ))

            # Combine and wrap
            ruby_code = "\n".join(ruby_parts)
            ruby_code = self._wrap_in_operation(
                ruby_code,
                f"Bookshelf {int(self.width)}x{int(self.height)}x{int(self.depth)}"
            )

            return TemplateResult(
                success=True,
                ruby_code=ruby_code,
                cut_list=cut_list
            )

        except ValueError as e:
            logger.warning(f"Bookshelf template validation error: {e}")
            return TemplateResult(
                success=False,
                error=str(e)
            )
        except Exception as e:
            logger.exception(f"Bookshelf template unexpected error: {e}")
            raise
