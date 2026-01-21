"""Desk template - writing or computer desk with optional drawers."""

import logging
from typing import Optional, Literal

from .base import BaseTemplate, TemplateResult, LumberPiece

logger = logging.getLogger("SketchupMCPServer")


class DeskTemplate(BaseTemplate):
    """Template for creating desks with panel legs and optional drawers."""

    template_name = "desk"
    description = "Writing or computer desk"
    default_joinery = "dado"

    def __init__(
        self,
        width: float = 1400,
        height: float = 750,
        depth: float = 700,
        has_drawer: bool = True,
        drawer_side: Literal["left", "right", "both"] = "right",
        has_keyboard_tray: bool = False,
        has_back_panel: bool = False,
        lumber: str = "90x19",
        joinery: Optional[str] = None,
        material: str = "pine",
        region: str = "australia",
        **kwargs,
    ):
        """
        Create a desk template.

        Args:
            width: Total width in mm (default 1400)
            height: Total height in mm (default 750)
            depth: Depth in mm (default 700)
            has_drawer: Include drawer unit (default True)
            drawer_side: Which side for drawer - "left", "right", or "both"
            has_keyboard_tray: Include keyboard tray (default False)
            has_back_panel: Include back panel for cable management (default False)
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
        self.has_drawer = has_drawer
        self.drawer_side = drawer_side
        self.has_keyboard_tray = has_keyboard_tray
        self.has_back_panel = has_back_panel

    def generate(self) -> TemplateResult:
        """Generate desk Ruby code and cut list."""
        try:
            # Calculate dimensions
            panel_thickness = self.lumber_thickness
            desktop_thickness = self.lumber_thickness

            # Leg panel dimensions
            leg_panel_height = self.height - desktop_thickness
            leg_panel_depth = self.depth - 50  # Inset from front

            # Drawer unit dimensions
            drawer_unit_width = 400
            drawer_height = 150

            # Validate dimensions
            if self.width < 600:
                return TemplateResult(
                    success=False,
                    error=f"Desk width {self.width}mm too small. Minimum: 600mm",
                )

            if leg_panel_height < 400:
                return TemplateResult(
                    success=False,
                    error=f"Desk height {self.height}mm too small. Minimum: {desktop_thickness + 400}mm",
                )

            # Calculate knee space (between leg panels)
            left_drawer = self.has_drawer and self.drawer_side in ["left", "both"]
            right_drawer = self.has_drawer and self.drawer_side in ["right", "both"]

            left_panel_x = 0
            right_panel_x = self.width - panel_thickness

            # Build cut list
            cut_list = [
                LumberPiece(
                    name="Desktop",
                    width=self.lumber_width,
                    height=self.width,
                    length=self.depth,
                    quantity=1,
                    material=self.material,
                    notes="Solid or glued-up panel",
                ),
                LumberPiece(
                    name="Leg Panel",
                    width=self.lumber_width,
                    height=leg_panel_depth,
                    length=leg_panel_height,
                    quantity=2,
                    material=self.material,
                    notes="Left and right leg panels",
                ),
                LumberPiece(
                    name="Back Rail",
                    width=self.lumber_width,
                    height=self.width - (2 * panel_thickness),
                    length=self.lumber_width,
                    quantity=1,
                    material=self.material,
                    notes="Connects leg panels at back",
                ),
            ]

            # Drawer pieces
            drawer_count = (1 if left_drawer else 0) + (1 if right_drawer else 0)
            if drawer_count > 0:
                cut_list.extend(
                    [
                        LumberPiece(
                            name="Drawer Front",
                            width=self.lumber_width,
                            height=drawer_unit_width - 20,
                            length=drawer_height - 10,
                            quantity=drawer_count,
                            material=self.material,
                            notes="Drawer face",
                        ),
                        LumberPiece(
                            name="Drawer Side",
                            width=self.lumber_width,
                            height=leg_panel_depth - 50,
                            length=drawer_height - 30,
                            quantity=drawer_count * 2,
                            material=self.material,
                            notes="Left and right drawer sides",
                        ),
                        LumberPiece(
                            name="Drawer Back",
                            width=self.lumber_width,
                            height=drawer_unit_width - 60,
                            length=drawer_height - 30,
                            quantity=drawer_count,
                            material=self.material,
                            notes="Drawer back panel",
                        ),
                        LumberPiece(
                            name="Drawer Bottom",
                            width=self.lumber_width,
                            height=drawer_unit_width - 60,
                            length=leg_panel_depth - 70,
                            quantity=drawer_count,
                            material=self.material,
                            notes="Drawer bottom (plywood recommended)",
                        ),
                    ]
                )

            if self.has_keyboard_tray:
                cut_list.append(
                    LumberPiece(
                        name="Keyboard Tray",
                        width=self.lumber_width,
                        height=600,
                        length=300,
                        quantity=1,
                        material=self.material,
                        notes="Slides under desktop on runners",
                    )
                )

            if self.has_back_panel:
                cut_list.append(
                    LumberPiece(
                        name="Back Panel",
                        width=self.lumber_width,
                        height=self.width - (2 * panel_thickness),
                        length=leg_panel_height - 200,
                        quantity=1,
                        material=self.material,
                        notes="Cable management panel",
                    )
                )

            # Generate Ruby code
            ruby_parts = []

            # Desktop
            ruby_parts.append(
                self._create_board_ruby(
                    name="Desktop",
                    width=self.width,
                    height=desktop_thickness,
                    depth=self.depth,
                    x=0,
                    y=0,
                    z=leg_panel_height,
                )
            )

            # Left leg panel
            ruby_parts.append(
                self._create_board_ruby(
                    name="Left Leg Panel",
                    width=panel_thickness,
                    height=leg_panel_height,
                    depth=leg_panel_depth,
                    x=left_panel_x,
                    y=self.depth - leg_panel_depth,
                    z=0,
                )
            )

            # Right leg panel
            ruby_parts.append(
                self._create_board_ruby(
                    name="Right Leg Panel",
                    width=panel_thickness,
                    height=leg_panel_height,
                    depth=leg_panel_depth,
                    x=right_panel_x,
                    y=self.depth - leg_panel_depth,
                    z=0,
                )
            )

            # Back rail (connects legs at back, near top)
            rail_z = leg_panel_height - self.lumber_width - 50
            ruby_parts.append(
                self._create_board_ruby(
                    name="Back Rail",
                    width=self.width - (2 * panel_thickness),
                    height=self.lumber_width,
                    depth=panel_thickness,
                    x=panel_thickness,
                    y=self.depth - panel_thickness,
                    z=rail_z,
                )
            )

            # Drawers (simplified box representation)
            if left_drawer:
                drawer_z = leg_panel_height - drawer_height - 50
                ruby_parts.append(
                    self._create_board_ruby(
                        name="Left Drawer",
                        width=drawer_unit_width - 20,
                        height=drawer_height - 10,
                        depth=leg_panel_depth - 50,
                        x=panel_thickness + 10,
                        y=self.depth - leg_panel_depth + 25,
                        z=drawer_z,
                    )
                )

            if right_drawer:
                drawer_z = leg_panel_height - drawer_height - 50
                ruby_parts.append(
                    self._create_board_ruby(
                        name="Right Drawer",
                        width=drawer_unit_width - 20,
                        height=drawer_height - 10,
                        depth=leg_panel_depth - 50,
                        x=self.width - panel_thickness - drawer_unit_width + 10,
                        y=self.depth - leg_panel_depth + 25,
                        z=drawer_z,
                    )
                )

            # Keyboard tray (positioned under desktop, center)
            if self.has_keyboard_tray:
                tray_z = leg_panel_height - 50
                tray_x = (self.width - 600) / 2
                ruby_parts.append(
                    self._create_board_ruby(
                        name="Keyboard Tray",
                        width=600,
                        height=panel_thickness,
                        depth=300,
                        x=tray_x,
                        y=50,  # Near front edge
                        z=tray_z,
                    )
                )

            # Back panel
            if self.has_back_panel:
                ruby_parts.append(
                    self._create_board_ruby(
                        name="Back Panel",
                        width=self.width - (2 * panel_thickness),
                        height=leg_panel_height - 200,
                        depth=panel_thickness,
                        x=panel_thickness,
                        y=self.depth - panel_thickness - 10,
                        z=100,
                    )
                )

            # Combine and wrap
            ruby_code = "\n".join(ruby_parts)
            ruby_code = self._wrap_in_operation(
                ruby_code,
                f"Desk {int(self.width)}x{int(self.height)}x{int(self.depth)}",
            )

            return TemplateResult(success=True, ruby_code=ruby_code, cut_list=cut_list)

        except ValueError as e:
            logger.warning(f"Desk template validation error: {e}")
            return TemplateResult(success=False, error=str(e))
        except Exception as e:
            logger.exception(f"Desk template unexpected error: {e}")
            raise
