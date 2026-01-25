"""Table template - dining, coffee, and end tables with aprons."""

import logging
from typing import List, Optional, Literal

from .base import BaseTemplate, TemplateResult, LumberPiece, JointMarker

logger = logging.getLogger("SketchupMCPServer")


class TableTemplate(BaseTemplate):
    """Template for creating tables with various configurations."""

    template_name = "table"
    description = "Table with variants: dining, coffee, end table"
    default_joinery = "mortise_tenon"

    # Default dimensions by variant (width x height x depth in mm)
    VARIANT_DEFAULTS = {
        "dining": (1800, 750, 900),
        "coffee": (1200, 450, 600),
        "end": (500, 500, 500),
    }

    def __init__(
        self,
        width: Optional[float] = None,
        height: Optional[float] = None,
        depth: Optional[float] = None,
        variant: Literal["dining", "coffee", "end"] = "dining",
        has_aprons: bool = True,
        has_stretchers: bool = False,
        leg_inset: float = 50,
        lumber: str = "90x45",
        joinery: Optional[str] = None,
        material: str = "pine",
        region: str = "australia",
        **kwargs,
    ):
        """
        Create a table template.

        Args:
            width: Total width in mm (defaults based on variant)
            height: Total height in mm (defaults based on variant)
            depth: Depth in mm (defaults based on variant)
            variant: Table type - "dining", "coffee", or "end"
            has_aprons: Include aprons between legs (default True)
            has_stretchers: Include lower stretchers (default False)
            leg_inset: Distance legs are inset from edges in mm (default 50)
            lumber: Lumber size (default "90x45")
            joinery: Joint type (default "mortise_tenon")
            material: Wood species (default "pine")
            region: Region for lumber (default "australia")
        """
        # Get defaults for variant
        default_dims = self.VARIANT_DEFAULTS.get(
            variant, self.VARIANT_DEFAULTS["dining"]
        )
        width = width if width is not None else default_dims[0]
        height = height if height is not None else default_dims[1]
        depth = depth if depth is not None else default_dims[2]

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
        self.variant = variant
        self.has_aprons = has_aprons
        self.has_stretchers = has_stretchers
        self.leg_inset = leg_inset

        # Store computed dimensions for _get_joint_markers()
        self._leg_size: float = 0
        self._leg_height: float = 0
        self._apron_height: float = 0
        self._apron_thickness: float = 0
        self._leg_x_positions: List[float] = []
        self._leg_y_positions: List[float] = []
        self._apron_z: float = 0
        self._stretcher_z: float = 0

    def _get_joint_markers(self) -> List[JointMarker]:
        """
        Return mortise-tenon joint markers for leg-to-apron connections.

        Markers appear on leg faces where aprons and stretchers connect.
        Each leg can have up to 4 joint markers (2 aprons + 2 stretchers).
        """
        if self._leg_size <= 0 or not self._leg_x_positions:
            return []

        markers = []
        marker_thickness = 0.5
        leg = self._leg_size
        apron_h = self._apron_height

        # Leg corner positions: [(x, y, front_face_dir, side_face_dir), ...]
        # front_face_dir: 'front' or 'back' indicates which Y direction the front-facing face is
        # side_face_dir: 'left' or 'right' indicates which X direction the side-facing face is
        leg_configs = [
            (
                self._leg_x_positions[0],
                self._leg_y_positions[0],
                "front",
                "left",
            ),  # Front-left
            (
                self._leg_x_positions[1],
                self._leg_y_positions[0],
                "front",
                "right",
            ),  # Front-right
            (
                self._leg_x_positions[0],
                self._leg_y_positions[1],
                "back",
                "left",
            ),  # Back-left
            (
                self._leg_x_positions[1],
                self._leg_y_positions[1],
                "back",
                "right",
            ),  # Back-right
        ]

        for i, (lx, ly, front_dir, side_dir) in enumerate(leg_configs):
            leg_num = i + 1

            if self.has_aprons:
                # Front/back apron marker on leg
                if front_dir == "front":
                    # Marker on front face of leg (y = ly)
                    markers.append(
                        JointMarker(
                            name=f"Leg {leg_num} Front Apron",
                            joint_type=self.joinery,
                            x=lx,
                            y=ly - marker_thickness,
                            z=self._apron_z,
                            width=leg,
                            height=apron_h,
                            depth=marker_thickness,
                        )
                    )
                else:
                    # Marker on back face of leg (y = ly + leg)
                    markers.append(
                        JointMarker(
                            name=f"Leg {leg_num} Back Apron",
                            joint_type=self.joinery,
                            x=lx,
                            y=ly + leg,
                            z=self._apron_z,
                            width=leg,
                            height=apron_h,
                            depth=marker_thickness,
                        )
                    )

                # Side apron marker on leg
                if side_dir == "left":
                    # Marker on left face of leg (x = lx)
                    markers.append(
                        JointMarker(
                            name=f"Leg {leg_num} Side Apron",
                            joint_type=self.joinery,
                            x=lx - marker_thickness,
                            y=ly,
                            z=self._apron_z,
                            width=marker_thickness,
                            height=apron_h,
                            depth=leg,
                        )
                    )
                else:
                    # Marker on right face of leg (x = lx + leg)
                    markers.append(
                        JointMarker(
                            name=f"Leg {leg_num} Side Apron",
                            joint_type=self.joinery,
                            x=lx + leg,
                            y=ly,
                            z=self._apron_z,
                            width=marker_thickness,
                            height=apron_h,
                            depth=leg,
                        )
                    )

            if self.has_stretchers and self._stretcher_z > 0:
                # Similar pattern for stretchers at lower position
                if front_dir == "front":
                    markers.append(
                        JointMarker(
                            name=f"Leg {leg_num} Front Stretcher",
                            joint_type=self.joinery,
                            x=lx,
                            y=ly - marker_thickness,
                            z=self._stretcher_z,
                            width=leg,
                            height=apron_h,
                            depth=marker_thickness,
                        )
                    )
                else:
                    markers.append(
                        JointMarker(
                            name=f"Leg {leg_num} Back Stretcher",
                            joint_type=self.joinery,
                            x=lx,
                            y=ly + leg,
                            z=self._stretcher_z,
                            width=leg,
                            height=apron_h,
                            depth=marker_thickness,
                        )
                    )

                if side_dir == "left":
                    markers.append(
                        JointMarker(
                            name=f"Leg {leg_num} Side Stretcher",
                            joint_type=self.joinery,
                            x=lx - marker_thickness,
                            y=ly,
                            z=self._stretcher_z,
                            width=marker_thickness,
                            height=apron_h,
                            depth=leg,
                        )
                    )
                else:
                    markers.append(
                        JointMarker(
                            name=f"Leg {leg_num} Side Stretcher",
                            joint_type=self.joinery,
                            x=lx + leg,
                            y=ly,
                            z=self._stretcher_z,
                            width=marker_thickness,
                            height=apron_h,
                            depth=leg,
                        )
                    )

        return markers

    def generate(self) -> TemplateResult:
        """Generate table Ruby code and cut list."""
        try:
            # Calculate dimensions
            leg_size = self.lumber_thickness  # Square legs
            tabletop_thickness = self.lumber_thickness
            apron_height = self.lumber_width
            apron_thickness = self.lumber_thickness

            # Leg positions (inset from corners)
            leg_x_positions = [self.leg_inset, self.width - self.leg_inset - leg_size]
            leg_y_positions = [self.leg_inset, self.depth - self.leg_inset - leg_size]

            # Apron lengths (between legs)
            long_apron_length = self.width - (2 * self.leg_inset) - (2 * leg_size)
            short_apron_length = self.depth - (2 * self.leg_inset) - (2 * leg_size)

            # Leg height (from floor to underside of tabletop)
            leg_height = self.height - tabletop_thickness

            # Validate dimensions
            if long_apron_length <= 0 or short_apron_length <= 0:
                return TemplateResult(
                    success=False,
                    error=f"Table dimensions too small for {leg_size}mm legs with {self.leg_inset}mm inset. "
                    f"Width must be > {2 * self.leg_inset + 2 * leg_size}mm, "
                    f"depth must be > {2 * self.leg_inset + 2 * leg_size}mm",
                )

            if leg_height <= apron_height:
                return TemplateResult(
                    success=False,
                    error=f"Table height {self.height}mm too small for {apron_height}mm aprons. "
                    f"Minimum height: {tabletop_thickness + apron_height + 50}mm",
                )

            # Store dimensions for _get_joint_markers()
            self._leg_size = leg_size
            self._leg_height = leg_height
            self._apron_height = apron_height
            self._apron_thickness = apron_thickness
            self._leg_x_positions = leg_x_positions
            self._leg_y_positions = leg_y_positions
            self._apron_z = leg_height - apron_height if self.has_aprons else 0
            self._stretcher_z = (
                leg_height / 3 - apron_height / 2 if self.has_stretchers else 0
            )

            # Build cut list
            cut_list = [
                LumberPiece(
                    name="Tabletop",
                    width=tabletop_thickness,
                    height=self.width,
                    length=self.depth,
                    quantity=1,
                    material=self.material,
                    notes="Solid or glued-up panel",
                ),
                LumberPiece(
                    name="Leg",
                    width=leg_size,
                    height=leg_size,
                    length=leg_height,
                    quantity=4,
                    material=self.material,
                    notes=f"Square legs, {self.joinery} joints (green markers)",
                ),
            ]

            if self.has_aprons:
                cut_list.extend(
                    [
                        LumberPiece(
                            name="Long Apron",
                            width=apron_thickness,
                            height=apron_height,
                            length=long_apron_length,
                            quantity=2,
                            material=self.material,
                            notes=f"Front and back aprons, {self.joinery} (green markers)",
                        ),
                        LumberPiece(
                            name="Short Apron",
                            width=apron_thickness,
                            height=apron_height,
                            length=short_apron_length,
                            quantity=2,
                            material=self.material,
                            notes=f"Side aprons, {self.joinery} (green markers)",
                        ),
                    ]
                )

            if self.has_stretchers:
                stretcher_height = leg_height / 3  # Position at 1/3 height
                cut_list.extend(
                    [
                        LumberPiece(
                            name="Long Stretcher",
                            width=apron_thickness,
                            height=apron_height,
                            length=long_apron_length,
                            quantity=2,
                            material=self.material,
                            notes="Front and back stretchers",
                        ),
                        LumberPiece(
                            name="Short Stretcher",
                            width=apron_thickness,
                            height=apron_height,
                            length=short_apron_length,
                            quantity=2,
                            material=self.material,
                            notes="Side stretchers",
                        ),
                    ]
                )

            # Generate Ruby code
            ruby_parts = []

            # Tabletop
            ruby_parts.append(
                self._create_board_ruby(
                    name="Tabletop",
                    width=self.width,
                    height=tabletop_thickness,
                    depth=self.depth,
                    x=0,
                    y=0,
                    z=leg_height,
                )
            )

            # Four legs at corners
            for i, (lx, ly) in enumerate(
                [
                    (leg_x_positions[0], leg_y_positions[0]),
                    (leg_x_positions[1], leg_y_positions[0]),
                    (leg_x_positions[0], leg_y_positions[1]),
                    (leg_x_positions[1], leg_y_positions[1]),
                ]
            ):
                ruby_parts.append(
                    self._create_board_ruby(
                        name=f"Leg {i + 1}",
                        width=leg_size,
                        height=leg_height,
                        depth=leg_size,
                        x=lx,
                        y=ly,
                        z=0,
                    )
                )

            # Aprons (positioned under tabletop, between legs)
            if self.has_aprons:
                apron_z = leg_height - apron_height

                # Front apron
                ruby_parts.append(
                    self._create_board_ruby(
                        name="Front Apron",
                        width=long_apron_length,
                        height=apron_height,
                        depth=apron_thickness,
                        x=leg_x_positions[0] + leg_size,
                        y=leg_y_positions[0],
                        z=apron_z,
                    )
                )

                # Back apron
                ruby_parts.append(
                    self._create_board_ruby(
                        name="Back Apron",
                        width=long_apron_length,
                        height=apron_height,
                        depth=apron_thickness,
                        x=leg_x_positions[0] + leg_size,
                        y=leg_y_positions[1] + leg_size - apron_thickness,
                        z=apron_z,
                    )
                )

                # Left apron
                ruby_parts.append(
                    self._create_board_ruby(
                        name="Left Apron",
                        width=apron_thickness,
                        height=apron_height,
                        depth=short_apron_length,
                        x=leg_x_positions[0],
                        y=leg_y_positions[0] + leg_size,
                        z=apron_z,
                    )
                )

                # Right apron
                ruby_parts.append(
                    self._create_board_ruby(
                        name="Right Apron",
                        width=apron_thickness,
                        height=apron_height,
                        depth=short_apron_length,
                        x=leg_x_positions[1] + leg_size - apron_thickness,
                        y=leg_y_positions[0] + leg_size,
                        z=apron_z,
                    )
                )

            # Stretchers (positioned at 1/3 height)
            if self.has_stretchers:
                stretcher_z = leg_height / 3 - apron_height / 2

                # Front stretcher
                ruby_parts.append(
                    self._create_board_ruby(
                        name="Front Stretcher",
                        width=long_apron_length,
                        height=apron_height,
                        depth=apron_thickness,
                        x=leg_x_positions[0] + leg_size,
                        y=leg_y_positions[0],
                        z=stretcher_z,
                    )
                )

                # Back stretcher
                ruby_parts.append(
                    self._create_board_ruby(
                        name="Back Stretcher",
                        width=long_apron_length,
                        height=apron_height,
                        depth=apron_thickness,
                        x=leg_x_positions[0] + leg_size,
                        y=leg_y_positions[1] + leg_size - apron_thickness,
                        z=stretcher_z,
                    )
                )

                # Left stretcher
                ruby_parts.append(
                    self._create_board_ruby(
                        name="Left Stretcher",
                        width=apron_thickness,
                        height=apron_height,
                        depth=short_apron_length,
                        x=leg_x_positions[0],
                        y=leg_y_positions[0] + leg_size,
                        z=stretcher_z,
                    )
                )

                # Right stretcher
                ruby_parts.append(
                    self._create_board_ruby(
                        name="Right Stretcher",
                        width=apron_thickness,
                        height=apron_height,
                        depth=short_apron_length,
                        x=leg_x_positions[1] + leg_size - apron_thickness,
                        y=leg_y_positions[0] + leg_size,
                        z=stretcher_z,
                    )
                )

            # Add joint markers
            ruby_parts.append(self._generate_markers_ruby())

            # Combine and wrap
            ruby_code = "\n".join(ruby_parts)
            variant_name = self.variant.replace("_", " ").title()
            ruby_code = self._wrap_in_operation(
                ruby_code,
                f"{variant_name} Table {int(self.width)}x{int(self.height)}x{int(self.depth)}",
            )

            return TemplateResult(success=True, ruby_code=ruby_code, cut_list=cut_list)

        except ValueError as e:
            logger.warning(f"Table template validation error: {e}")
            return TemplateResult(success=False, error=str(e))
        except Exception as e:
            logger.exception(f"Table template unexpected error: {e}")
            raise
