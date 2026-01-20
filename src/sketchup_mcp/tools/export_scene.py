"""export_scene tool - Export the current SketchUp model"""

import json
import logging
from typing import Any, Optional

from ..config import config
from ..connection import get_connection, parse_tool_response

logger = logging.getLogger("SketchupMCPServer")


def export_scene(
    export_format: str = "skp",
    width: Optional[int] = None,
    height: Optional[int] = None,
    request_id: Any = None
) -> str:
    """
    Export the current SketchUp model to a file.

    Args:
        export_format: Export format - "skp" (SketchUp), "png", or "jpg"
        width: Image width in pixels (for png/jpg exports)
        height: Image height in pixels (for png/jpg exports)
        request_id: Optional request ID for tracking

    Returns:
        JSON string with export path or error

    Supported formats:
        - skp: Native SketchUp format
        - png: PNG image (supports transparency)
        - jpg/jpeg: JPEG image
    """
    export_format = export_format.lower()
    valid_formats = ["skp", "png", "jpg", "jpeg"]

    if export_format not in valid_formats:
        return json.dumps({
            "success": False,
            "error": f"Unsupported format: {export_format}. Valid formats: {', '.join(valid_formats)}"
        })

    # Validate image dimensions
    if width is not None:
        if not (config.min_image_dimension <= width <= config.max_image_dimension):
            return json.dumps({
                "success": False,
                "error": f"Width must be between {config.min_image_dimension} and {config.max_image_dimension}"
            })
    if height is not None:
        if not (config.min_image_dimension <= height <= config.max_image_dimension):
            return json.dumps({
                "success": False,
                "error": f"Height must be between {config.min_image_dimension} and {config.max_image_dimension}"
            })

    try:
        logger.info(f"export_scene: format={export_format}")

        arguments = {"format": export_format}
        if width:
            arguments["width"] = width
        if height:
            arguments["height"] = height

        connection = get_connection()
        result = connection.send_command(
            tool_name="export_scene",
            arguments=arguments,
            request_id=request_id
        )

        success, text = parse_tool_response(result)
        if not success:
            return json.dumps({"success": False, "error": text})

        # Parse the path from the response
        if "Exported to:" in text:
            path = text.replace("Exported to:", "").strip()
            return json.dumps({"success": True, "path": path, "format": export_format})
        else:
            return json.dumps({"success": True, "result": text})

    except ConnectionError as e:
        logger.error(f"export_scene connection error: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "hint": "Make sure SketchUp is running with the MCP extension started"
        })

    except Exception as e:
        logger.error(f"export_scene error: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })
