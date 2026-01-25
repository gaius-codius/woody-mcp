"""Picture frame template - frame with rabbet for glass and backing."""

import logging
from typing import List, Optional

from .base import BaseTemplate, TemplateResult, LumberPiece, JointMarker

logger = logging.getLogger("SketchupMCPServer")


class PictureFrameTemplate(BaseTemplate):
    """Template for creating picture frames with mitered corners."""

    template_name = "picture_frame"
    description = "Picture frame with rabbet for glass"
    default_joinery = "miter"

    def __init__(
        self,
        width: float = 300,
        height: float = 400,
        depth: float = 20,
        frame_width: float = 50,
        rabbet_depth: float = 10,
        mat_width: float = 0,
        lumber: str = "50x20",
        joinery: Optional[str] = None,
        material: str = "oak",
        region: str = "australia",
        **kwargs,
    ):
        """
        Create a picture frame template.

        Args:
            width: Outer frame width in mm (default 300)
            height: Outer frame height in mm (default 400)
            depth: Frame thickness/depth in mm (default 20)
            frame_width: Width of frame rails in mm (default 50)
            rabbet_depth: Depth of rabbet for glass/backing in mm (default 10)
            mat_width: Width of mat border if used (default 0 - no mat)
            lumber: Lumber size (default "50x20")
            joinery: Joint type (default "miter")
            material: Wood species (default "oak")
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
        self.frame_width = frame_width
        self.rabbet_depth = min(rabbet_depth, depth - 5)  # Leave 5mm face
        self.mat_width = mat_width

        # Store computed dimensions for _get_joint_markers()
        self._inner_width: float = 0
        self._inner_height: float = 0
        self._frame_thickness: float = 0

    def _get_joint_markers(self) -> List[JointMarker]:
        """
        Return miter joint markers at frame corners and rabbet markers.

        Picture frames use miter joints at corners (purple) and rabbet
        along inner edge (blue) for glass/backing.
        """
        if self._inner_width <= 0:
            return []

        markers = []
        marker_thickness = 0.5
        fw = self.frame_width
        ft = self._frame_thickness

        # Miter markers at 4 corners (on the corner edges)
        # Top-left corner
        markers.append(
            JointMarker(
                name="Miter Top-Left",
                joint_type="miter",
                x=0,
                y=0,
                z=self.height - fw,
                width=fw,
                height=marker_thickness,
                depth=fw,
            )
        )
        # Top-right corner
        markers.append(
            JointMarker(
                name="Miter Top-Right",
                joint_type="miter",
                x=self.width - fw,
                y=0,
                z=self.height - fw,
                width=fw,
                height=marker_thickness,
                depth=fw,
            )
        )
        # Bottom-left corner
        markers.append(
            JointMarker(
                name="Miter Bottom-Left",
                joint_type="miter",
                x=0,
                y=0,
                z=0,
                width=fw,
                height=marker_thickness,
                depth=fw,
            )
        )
        # Bottom-right corner
        markers.append(
            JointMarker(
                name="Miter Bottom-Right",
                joint_type="miter",
                x=self.width - fw,
                y=0,
                z=0,
                width=fw,
                height=marker_thickness,
                depth=fw,
            )
        )

        # Rabbet markers along inner edge (where glass sits)
        rabbet_y = ft - self.rabbet_depth
        # Top rabbet
        markers.append(
            JointMarker(
                name="Rabbet Top",
                joint_type="rabbet",
                x=fw,
                y=rabbet_y,
                z=self.height - fw - marker_thickness,
                width=self._inner_width,
                height=marker_thickness,
                depth=self.rabbet_depth,
            )
        )
        # Bottom rabbet
        markers.append(
            JointMarker(
                name="Rabbet Bottom",
                joint_type="rabbet",
                x=fw,
                y=rabbet_y,
                z=fw,
                width=self._inner_width,
                height=marker_thickness,
                depth=self.rabbet_depth,
            )
        )

        return markers

    def generate(self) -> TemplateResult:
        """Generate picture frame Ruby code and cut list."""
        try:
            # Calculate dimensions
            frame_thickness = self.depth

            # Inner opening (where glass/picture sits)
            inner_width = self.width - (2 * self.frame_width)
            inner_height = self.height - (2 * self.frame_width)

            # Picture/artwork visible area (inside mat if present)
            if self.mat_width > 0:
                picture_width = inner_width - (2 * self.mat_width)
                picture_height = inner_height - (2 * self.mat_width)
            else:
                picture_width = inner_width
                picture_height = inner_height

            # Validate dimensions
            if inner_width <= 0 or inner_height <= 0:
                return TemplateResult(
                    success=False,
                    error=f"Frame dimensions ({self.width}x{self.height}mm) too small for "
                    f"{self.frame_width}mm frame width. Inner opening would be negative.",
                )

            if self.mat_width > 0 and (picture_width <= 0 or picture_height <= 0):
                return TemplateResult(
                    success=False,
                    error=f"Mat width {self.mat_width}mm too large for inner opening "
                    f"({inner_width}x{inner_height}mm). Reduce mat or increase frame size.",
                )

            # Store dimensions for _get_joint_markers()
            self._inner_width = inner_width
            self._inner_height = inner_height
            self._frame_thickness = frame_thickness

            # Rail lengths (long dimension for mitered pieces)
            # For miter joints, length is outer dimension
            top_bottom_length = self.width
            side_length = self.height

            # Build cut list
            cut_list = [
                LumberPiece(
                    name="Top/Bottom Rail",
                    width=self.frame_width,
                    height=frame_thickness,
                    length=top_bottom_length,
                    quantity=2,
                    material=self.material,
                    notes=f"45° miter cuts (purple markers), {self.rabbet_depth}mm rabbet (blue markers)",
                ),
                LumberPiece(
                    name="Side Rail",
                    width=self.frame_width,
                    height=frame_thickness,
                    length=side_length,
                    quantity=2,
                    material=self.material,
                    notes=f"45° miter cuts (purple markers), {self.rabbet_depth}mm rabbet (blue markers)",
                ),
                LumberPiece(
                    name="Glass",
                    width=3,  # Standard picture glass
                    height=inner_width + 4,  # Slight overlap into rabbet
                    length=inner_height + 4,
                    quantity=1,
                    material="glass",
                    notes="Cut by glass shop to fit rabbet",
                ),
                LumberPiece(
                    name="Backing Board",
                    width=3,  # MDF or cardboard
                    height=inner_width + 4,
                    length=inner_height + 4,
                    quantity=1,
                    material="mdf",
                    notes="Holds picture in place, secured with points",
                ),
            ]

            if self.mat_width > 0:
                cut_list.append(
                    LumberPiece(
                        name="Mat Board",
                        width=2,
                        height=inner_width,
                        length=inner_height,
                        quantity=1,
                        material="mat_board",
                        notes=f"Cut {self.mat_width}mm border, 45° bevel on inner edge",
                    )
                )

            # Generate Ruby code
            ruby_parts = []

            # Top rail
            ruby_parts.append(
                self._create_board_ruby(
                    name="Top Rail",
                    width=self.width,
                    height=frame_thickness,
                    depth=self.frame_width,
                    x=0,
                    y=0,
                    z=self.height - self.frame_width,
                )
            )

            # Bottom rail
            ruby_parts.append(
                self._create_board_ruby(
                    name="Bottom Rail",
                    width=self.width,
                    height=frame_thickness,
                    depth=self.frame_width,
                    x=0,
                    y=0,
                    z=0,
                )
            )

            # Left rail (between top and bottom)
            ruby_parts.append(
                self._create_board_ruby(
                    name="Left Rail",
                    width=self.frame_width,
                    height=frame_thickness,
                    depth=inner_height,
                    x=0,
                    y=0,
                    z=self.frame_width,
                )
            )

            # Right rail
            ruby_parts.append(
                self._create_board_ruby(
                    name="Right Rail",
                    width=self.frame_width,
                    height=frame_thickness,
                    depth=inner_height,
                    x=self.width - self.frame_width,
                    y=0,
                    z=self.frame_width,
                )
            )

            # Glass (inset into rabbet)
            glass_inset = frame_thickness - self.rabbet_depth
            ruby_parts.append(
                self._create_board_ruby(
                    name="Glass",
                    width=inner_width + 4,
                    height=3,
                    depth=inner_height + 4,
                    x=self.frame_width - 2,
                    y=glass_inset,
                    z=self.frame_width - 2,
                )
            )

            # Backing (behind glass)
            ruby_parts.append(
                self._create_board_ruby(
                    name="Backing",
                    width=inner_width + 4,
                    height=3,
                    depth=inner_height + 4,
                    x=self.frame_width - 2,
                    y=glass_inset + 5,
                    z=self.frame_width - 2,
                )
            )

            # Add joint markers
            ruby_parts.append(self._generate_markers_ruby())

            # Combine and wrap
            ruby_code = "\n".join(ruby_parts)
            ruby_code = self._wrap_in_operation(
                ruby_code,
                f"Picture Frame {int(self.width)}x{int(self.height)}",
            )

            return TemplateResult(success=True, ruby_code=ruby_code, cut_list=cut_list)

        except ValueError as e:
            logger.warning(f"Picture frame template validation error: {e}")
            return TemplateResult(success=False, error=str(e))
        except Exception as e:
            logger.exception(f"Picture frame template unexpected error: {e}")
            raise
