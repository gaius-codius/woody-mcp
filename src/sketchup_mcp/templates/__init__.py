"""Project templates for woodworking projects."""

from .base import BaseTemplate, TemplateResult, LumberPiece, JointMarker, JOINT_COLORS
from .bookshelf import BookshelfTemplate
from .box import BoxTemplate
from .table import TableTemplate
from .cabinet import CabinetTemplate
from .workbench import WorkbenchTemplate
from .desk import DeskTemplate
from .cutting_board import CuttingBoardTemplate
from .picture_frame import PictureFrameTemplate
from .shelf_bracket import ShelfBracketTemplate
from .tray import TrayTemplate

# Template registry for discovery
TEMPLATES = {
    "bookshelf": BookshelfTemplate,
    "box": BoxTemplate,
    "table": TableTemplate,
    "cabinet": CabinetTemplate,
    "workbench": WorkbenchTemplate,
    "desk": DeskTemplate,
    "cutting_board": CuttingBoardTemplate,
    "picture_frame": PictureFrameTemplate,
    "shelf_bracket": ShelfBracketTemplate,
    "tray": TrayTemplate,
}

__all__ = [
    "BaseTemplate",
    "TemplateResult",
    "LumberPiece",
    "JointMarker",
    "JOINT_COLORS",
    "BookshelfTemplate",
    "BoxTemplate",
    "TableTemplate",
    "CabinetTemplate",
    "WorkbenchTemplate",
    "DeskTemplate",
    "CuttingBoardTemplate",
    "PictureFrameTemplate",
    "ShelfBracketTemplate",
    "TrayTemplate",
    "TEMPLATES",
]
