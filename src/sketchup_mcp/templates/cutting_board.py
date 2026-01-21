"""Cutting board template - simple board with edge or end grain pattern."""

import logging
from typing import Optional, Literal

from .base import BaseTemplate, TemplateResult, LumberPiece

logger = logging.getLogger("SketchupMCPServer")


class CuttingBoardTemplate(BaseTemplate):
    """Template for creating cutting boards."""

    template_name = "cutting_board"
    description = "Cutting board with edge or end grain pattern"
    default_joinery = "butt"

    def __init__(
        self,
        width: float = 400,
        height: float = 25,
        depth: float = 300,
        pattern: Literal["edge_grain", "end_grain"] = "edge_grain",
        stripe_count: int = 5,
        lumber: str = "90x25",
        joinery: Optional[str] = None,
        material: str = "maple",
        region: str = "australia",
        **kwargs,
    ):
        """
        Create a cutting board template.

        Args:
            width: Total width in mm (default 400)
            height: Thickness in mm (default 25)
            depth: Depth in mm (default 300)
            pattern: Grain pattern - "edge_grain" or "end_grain"
            stripe_count: Number of stripes for visual effect (default 5)
            lumber: Lumber size (default "90x25")
            joinery: Joint type (default "butt")
            material: Wood species (default "maple" - food safe)
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
        self.pattern = pattern
        self.stripe_count = max(1, int(stripe_count))

    def generate(self) -> TemplateResult:
        """Generate cutting board Ruby code and cut list."""
        try:
            board_thickness = self.height

            # Validate dimensions
            if board_thickness < 15:
                return TemplateResult(
                    success=False,
                    error=f"Cutting board thickness {board_thickness}mm is too thin. "
                    f"Minimum recommended: 15mm for durability.",
                )

            if self.width < 100 or self.depth < 100:
                return TemplateResult(
                    success=False,
                    error=f"Cutting board dimensions ({self.width}x{self.depth}mm) too small. "
                    f"Minimum recommended: 100x100mm.",
                )

            # Calculate stripe dimensions
            stripe_width = self.width / self.stripe_count

            # Build cut list
            if self.pattern == "end_grain":
                # End grain boards are made from strips turned on end
                cut_list = [
                    LumberPiece(
                        name="End Grain Strip",
                        width=self.lumber_width,
                        height=board_thickness,
                        length=self.depth,
                        quantity=self.stripe_count,
                        material=self.material,
                        notes="Cut strips, rotate 90°, glue faces together for end grain pattern",
                    ),
                ]
            else:
                # Edge grain boards are simple glued strips
                cut_list = [
                    LumberPiece(
                        name="Edge Grain Strip",
                        width=stripe_width,
                        height=board_thickness,
                        length=self.depth,
                        quantity=self.stripe_count,
                        material=self.material,
                        notes="Glue strips edge-to-edge for edge grain pattern",
                    ),
                ]

            # Generate Ruby code - single solid board visualization
            # (The stripes are construction detail, final product is one piece)
            ruby_parts = []

            # Main board
            ruby_parts.append(
                self._create_board_ruby(
                    name="Cutting Board",
                    width=self.width,
                    height=board_thickness,
                    depth=self.depth,
                    x=0,
                    y=0,
                    z=0,
                )
            )

            # Combine and wrap
            ruby_code = "\n".join(ruby_parts)
            pattern_name = self.pattern.replace("_", " ").title()
            ruby_code = self._wrap_in_operation(
                ruby_code,
                f"{pattern_name} Cutting Board {int(self.width)}x{int(self.depth)}",
            )

            return TemplateResult(success=True, ruby_code=ruby_code, cut_list=cut_list)

        except ValueError as e:
            logger.warning(f"Cutting board template validation error: {e}")
            return TemplateResult(success=False, error=str(e))
        except Exception as e:
            logger.exception(f"Cutting board template unexpected error: {e}")
            raise
