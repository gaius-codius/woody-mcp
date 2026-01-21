"""build_project - Create woodworking projects from templates."""

import json
import logging
from typing import Any, Dict, Optional

from ..connection import get_connection, parse_tool_response
from ..templates import TEMPLATES, TemplateResult

logger = logging.getLogger("SketchupMCPServer")


def build_project(
    template_type: str,
    width: Optional[float] = None,
    height: Optional[float] = None,
    depth: Optional[float] = None,
    lumber: str = "90x19",
    joinery: Optional[str] = None,
    material: str = "pine",
    region: str = "australia",
    options: Optional[Dict[str, Any]] = None,
    request_id: Any = None
) -> str:
    """
    Build a woodworking project from a template.

    Args:
        template_type: Type of project ("bookshelf", "box", etc.)
        width: Width in mm (uses template default if not specified)
        height: Height in mm (uses template default if not specified)
        depth: Depth in mm (uses template default if not specified)
        lumber: Lumber size string (e.g., "90x19", "2x4")
        joinery: Joint type (uses template default if not specified)
        material: Wood species for appearance
        region: Region for lumber standards ("australia", "north_america", etc.)
        options: Template-specific options (e.g., {"shelves": 4} for bookshelf)
        request_id: Optional request ID for tracking

    Returns:
        JSON string with success status, cut_list, and result or error
    """
    # Validate template type
    if not template_type or template_type.lower() not in TEMPLATES:
        available = ", ".join(TEMPLATES.keys())
        return json.dumps({
            "success": False,
            "error": f"Unknown template type: '{template_type}'. Available: {available}"
        })

    template_class = TEMPLATES[template_type.lower()]

    try:
        logger.info(f"build_project: template={template_type}, {width}x{height}x{depth}")

        # Build kwargs, only including specified values
        kwargs = {
            "lumber": lumber,
            "material": material,
            "region": region,
        }

        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        if depth is not None:
            kwargs["depth"] = depth
        if joinery is not None:
            kwargs["joinery"] = joinery
        if options:
            kwargs.update(options)

        # Create template and generate
        template = template_class(**kwargs)
        result: TemplateResult = template.generate()

        if not result.success:
            return json.dumps({
                "success": False,
                "error": result.error
            })

        # Execute the Ruby code via eval_ruby
        connection = get_connection()
        eval_result = connection.send_command(
            tool_name="eval_ruby",
            arguments={"code": result.ruby_code},
            request_id=request_id
        )

        success, text = parse_tool_response(eval_result)

        if success:
            return json.dumps({
                "success": True,
                "result": text,
                "cut_list": result.to_dict()["cut_list"],
                "template": template_type,
                "dimensions": {
                    "width": template.width,
                    "height": template.height,
                    "depth": template.depth
                }
            })
        else:
            return json.dumps({
                "success": False,
                "error": f"SketchUp error: {text}",
                "ruby_code": result.ruby_code  # Include for debugging
            })

    except ConnectionError as e:
        logger.error(f"build_project connection error: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "hint": "Make sure SketchUp is running with the MCP extension started"
        })

    except (ValueError, TypeError) as e:
        logger.warning(f"build_project validation error: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })

    except Exception as e:
        logger.exception(f"build_project unexpected error: {e}")
        raise


def list_templates() -> str:
    """
    List all available project templates.

    Returns:
        JSON string with template information
    """
    try:
        templates = []
        for name, cls in TEMPLATES.items():
            info = cls.get_template_info()
            templates.append(info)

        return json.dumps({
            "success": True,
            "templates": templates
        })
    except Exception as e:
        logger.exception(f"list_templates unexpected error: {e}")
        raise
