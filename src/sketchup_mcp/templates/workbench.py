"""Workbench template - heavy-duty workshop workbench."""

import logging
from typing import Optional, Literal

from .base import BaseTemplate, TemplateResult, LumberPiece

logger = logging.getLogger("SketchupMCPServer")


class WorkbenchTemplate(BaseTemplate):
    """Template for creating heavy-duty workbenches."""

    template_name = "workbench"
    description = "Heavy-duty workshop workbench"
    default_joinery = "mortise_tenon"

    def __init__(
        self,
        width: float = 1800,
        height: float = 900,
        depth: float = 600,
        has_shelf: bool = True,
        leg_count: Literal[4, 6] = 4,
        apron_style: Literal["full", "rails_only"] = "full",
        top_thickness: float = 45,
        lumber: str = "90x45",
        joinery: Optional[str] = None,
        material: str = "pine",
        region: str = "australia",
        **kwargs,
    ):
        """
        Create a workbench template.

        Args:
            width: Total width in mm (default 1800)
            height: Total height in mm (default 900)
            depth: Depth in mm (default 600)
            has_shelf: Include lower shelf (default True)
            leg_count: Number of legs - 4 or 6 (default 4, use 6 for benches > 2000mm)
            apron_style: "full" aprons or "rails_only" (default "full")
            top_thickness: Thickness of benchtop in mm (default 45)
            lumber: Lumber size for legs (default "90x45")
            joinery: Joint type (default "mortise_tenon")
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
        self.has_shelf = has_shelf
        self.leg_count = 6 if leg_count == 6 or width > 2000 else 4
        self.apron_style = apron_style
        self.top_thickness = max(45, top_thickness)  # Minimum 45mm for workbench

    def generate(self) -> TemplateResult:
        """Generate workbench Ruby code and cut list."""
        try:
            # Calculate dimensions - workbench uses heavier lumber
            leg_size = self.lumber_thickness  # Square legs from lumber thickness
            apron_height = self.lumber_width
            apron_thickness = self.lumber_thickness

            # Leg inset from edges
            leg_inset = 50

            # Leg height (floor to underside of top)
            leg_height = self.height - self.top_thickness

            # Shelf height (1/3 from floor)
            shelf_z = leg_height / 3

            # Calculate leg positions
            if self.leg_count == 6:
                # 6 legs: corners + 2 middle legs
                leg_x_positions = [
                    leg_inset,
                    (self.width - leg_size) / 2,
                    self.width - leg_inset - leg_size,
                ]
            else:
                # 4 legs: corners only
                leg_x_positions = [leg_inset, self.width - leg_inset - leg_size]

            leg_y_positions = [leg_inset, self.depth - leg_inset - leg_size]

            # Apron/rail lengths
            if self.leg_count == 6:
                long_rail_length = (self.width - leg_size) / 2 - leg_inset - leg_size
            else:
                long_rail_length = self.width - (2 * leg_inset) - (2 * leg_size)
            short_rail_length = self.depth - (2 * leg_inset) - (2 * leg_size)

            # Validate dimensions
            if long_rail_length <= 0 or short_rail_length <= 0:
                return TemplateResult(
                    success=False,
                    error=f"Workbench dimensions too small for {leg_size}mm legs. "
                    f"Minimum width: {2 * leg_inset + 2 * leg_size + 100}mm",
                )

            if leg_height < apron_height + 100:
                return TemplateResult(
                    success=False,
                    error=f"Workbench height {self.height}mm too small. "
                    f"Minimum: {self.top_thickness + apron_height + 200}mm",
                )

            # Build cut list
            cut_list = [
                LumberPiece(
                    name="Benchtop",
                    width=self.lumber_width,
                    height=self.width,
                    length=self.depth,
                    quantity=1,
                    material=self.material,
                    notes=f"Laminated top, {self.top_thickness}mm thick minimum",
                ),
                LumberPiece(
                    name="Leg",
                    width=leg_size,
                    height=leg_size,
                    length=leg_height,
                    quantity=self.leg_count,
                    material=self.material,
                    notes=f"Heavy square legs, {self.joinery} joints",
                ),
            ]

            # Rails/aprons
            rail_qty_multiplier = (
                2 if self.leg_count == 4 else 4
            )  # More sections with 6 legs
            if self.apron_style == "full":
                cut_list.extend(
                    [
                        LumberPiece(
                            name="Long Apron",
                            width=apron_thickness,
                            height=apron_height,
                            length=long_rail_length,
                            quantity=rail_qty_multiplier,
                            material=self.material,
                            notes="Front and back aprons",
                        ),
                        LumberPiece(
                            name="Short Apron",
                            width=apron_thickness,
                            height=apron_height,
                            length=short_rail_length,
                            quantity=2,
                            material=self.material,
                            notes="End aprons",
                        ),
                    ]
                )
            else:
                # Rails only - just top and bottom rails
                cut_list.append(
                    LumberPiece(
                        name="Long Rail",
                        width=apron_thickness,
                        height=apron_height,
                        length=long_rail_length,
                        quantity=rail_qty_multiplier * 2,  # Top and bottom
                        material=self.material,
                        notes="Horizontal rails",
                    )
                )

            # Stretchers (lower rails for shelf support)
            cut_list.extend(
                [
                    LumberPiece(
                        name="Long Stretcher",
                        width=apron_thickness,
                        height=apron_height,
                        length=long_rail_length,
                        quantity=rail_qty_multiplier,
                        material=self.material,
                        notes="Lower stretchers for shelf",
                    ),
                    LumberPiece(
                        name="Short Stretcher",
                        width=apron_thickness,
                        height=apron_height,
                        length=short_rail_length,
                        quantity=2,
                        material=self.material,
                        notes="End stretchers",
                    ),
                ]
            )

            if self.has_shelf:
                shelf_width = self.width - (2 * leg_inset) - leg_size
                shelf_depth = self.depth - (2 * leg_inset) - leg_size
                cut_list.append(
                    LumberPiece(
                        name="Lower Shelf",
                        width=self.lumber_width,
                        height=shelf_width,
                        length=shelf_depth,
                        quantity=1,
                        material=self.material,
                        notes="Shelf rests on stretchers",
                    )
                )

            # Generate Ruby code
            ruby_parts = []

            # Benchtop
            ruby_parts.append(
                self._create_board_ruby(
                    name="Benchtop",
                    width=self.width,
                    height=self.top_thickness,
                    depth=self.depth,
                    x=0,
                    y=0,
                    z=leg_height,
                )
            )

            # Legs at all positions
            leg_num = 1
            for lx in leg_x_positions:
                for ly in leg_y_positions:
                    ruby_parts.append(
                        self._create_board_ruby(
                            name=f"Leg {leg_num}",
                            width=leg_size,
                            height=leg_height,
                            depth=leg_size,
                            x=lx,
                            y=ly,
                            z=0,
                        )
                    )
                    leg_num += 1

            # Upper aprons/rails (under benchtop)
            apron_z = leg_height - apron_height

            # Front and back long aprons
            for section_idx in range(len(leg_x_positions) - 1):
                start_x = leg_x_positions[section_idx] + leg_size
                section_length = leg_x_positions[section_idx + 1] - start_x

                # Front apron
                ruby_parts.append(
                    self._create_board_ruby(
                        name=f"Front Apron {section_idx + 1}",
                        width=section_length,
                        height=apron_height,
                        depth=apron_thickness,
                        x=start_x,
                        y=leg_y_positions[0],
                        z=apron_z,
                    )
                )

                # Back apron
                ruby_parts.append(
                    self._create_board_ruby(
                        name=f"Back Apron {section_idx + 1}",
                        width=section_length,
                        height=apron_height,
                        depth=apron_thickness,
                        x=start_x,
                        y=leg_y_positions[1] + leg_size - apron_thickness,
                        z=apron_z,
                    )
                )

            # End aprons
            ruby_parts.append(
                self._create_board_ruby(
                    name="Left Apron",
                    width=apron_thickness,
                    height=apron_height,
                    depth=short_rail_length,
                    x=leg_x_positions[0],
                    y=leg_y_positions[0] + leg_size,
                    z=apron_z,
                )
            )

            ruby_parts.append(
                self._create_board_ruby(
                    name="Right Apron",
                    width=apron_thickness,
                    height=apron_height,
                    depth=short_rail_length,
                    x=leg_x_positions[-1] + leg_size - apron_thickness,
                    y=leg_y_positions[0] + leg_size,
                    z=apron_z,
                )
            )

            # Lower stretchers (at shelf height)
            stretcher_z = shelf_z - apron_height

            for section_idx in range(len(leg_x_positions) - 1):
                start_x = leg_x_positions[section_idx] + leg_size
                section_length = leg_x_positions[section_idx + 1] - start_x

                # Front stretcher
                ruby_parts.append(
                    self._create_board_ruby(
                        name=f"Front Stretcher {section_idx + 1}",
                        width=section_length,
                        height=apron_height,
                        depth=apron_thickness,
                        x=start_x,
                        y=leg_y_positions[0],
                        z=stretcher_z,
                    )
                )

                # Back stretcher
                ruby_parts.append(
                    self._create_board_ruby(
                        name=f"Back Stretcher {section_idx + 1}",
                        width=section_length,
                        height=apron_height,
                        depth=apron_thickness,
                        x=start_x,
                        y=leg_y_positions[1] + leg_size - apron_thickness,
                        z=stretcher_z,
                    )
                )

            # End stretchers
            ruby_parts.append(
                self._create_board_ruby(
                    name="Left Stretcher",
                    width=apron_thickness,
                    height=apron_height,
                    depth=short_rail_length,
                    x=leg_x_positions[0],
                    y=leg_y_positions[0] + leg_size,
                    z=stretcher_z,
                )
            )

            ruby_parts.append(
                self._create_board_ruby(
                    name="Right Stretcher",
                    width=apron_thickness,
                    height=apron_height,
                    depth=short_rail_length,
                    x=leg_x_positions[-1] + leg_size - apron_thickness,
                    y=leg_y_positions[0] + leg_size,
                    z=stretcher_z,
                )
            )

            # Lower shelf
            if self.has_shelf:
                shelf_x = leg_x_positions[0] + leg_size
                shelf_y = leg_y_positions[0] + leg_size
                shelf_width_actual = leg_x_positions[-1] - shelf_x
                shelf_depth_actual = leg_y_positions[1] - shelf_y

                ruby_parts.append(
                    self._create_board_ruby(
                        name="Lower Shelf",
                        width=shelf_width_actual,
                        height=self.lumber_thickness,
                        depth=shelf_depth_actual,
                        x=shelf_x,
                        y=shelf_y,
                        z=shelf_z,
                    )
                )

            # Combine and wrap
            ruby_code = "\n".join(ruby_parts)
            ruby_code = self._wrap_in_operation(
                ruby_code,
                f"Workbench {int(self.width)}x{int(self.height)}x{int(self.depth)}",
            )

            return TemplateResult(success=True, ruby_code=ruby_code, cut_list=cut_list)

        except ValueError as e:
            logger.warning(f"Workbench template validation error: {e}")
            return TemplateResult(success=False, error=str(e))
        except Exception as e:
            logger.exception(f"Workbench template unexpected error: {e}")
            raise
