"""export_scene tool - Export the current SketchUp model"""

import json
import logging
from typing import Any, Optional

from ..connection import get_connection

logger = logging.getLogger("SketchupMCPServer")


def export_scene(
    format: str = "skp",
    width: Optional[int] = None,
    height: Optional[int] = None,
    request_id: Any = None
) -> str:
    """
    Export the current SketchUp model to a file.

    Args:
        format: Export format - "skp" (SketchUp), "png", or "jpg"
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
    format = format.lower()
    valid_formats = ["skp", "png", "jpg", "jpeg"]

    if format not in valid_formats:
        return json.dumps({
            "success": False,
            "error": f"Unsupported format: {format}. Valid formats: {', '.join(valid_formats)}"
        })

    try:
        logger.info(f"export_scene: format={format}")

        arguments = {"format": format}
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

        # Extract the text result
        content = result.get("content", [])
        if isinstance(content, list) and len(content) > 0:
            text = content[0].get("text", "")
            is_error = result.get("isError", False)

            if is_error:
                return json.dumps({
                    "success": False,
                    "error": text
                })
            else:
                # Parse the path from the response
                if "Exported to:" in text:
                    path = text.replace("Exported to:", "").strip()
                    return json.dumps({
                        "success": True,
                        "path": path,
                        "format": format
                    })
                else:
                    return json.dumps({
                        "success": True,
                        "result": text
                    })
        else:
            return json.dumps({
                "success": False,
                "error": "No response from SketchUp"
            })

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
