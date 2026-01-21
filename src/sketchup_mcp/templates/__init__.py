"""Project templates for woodworking projects."""

from .base import BaseTemplate, TemplateResult, LumberPiece
from .bookshelf import BookshelfTemplate
from .box import BoxTemplate

# Template registry for discovery
TEMPLATES = {
    "bookshelf": BookshelfTemplate,
    "box": BoxTemplate,
}

__all__ = [
    "BaseTemplate",
    "TemplateResult",
    "LumberPiece",
    "BookshelfTemplate",
    "BoxTemplate",
    "TEMPLATES",
]
