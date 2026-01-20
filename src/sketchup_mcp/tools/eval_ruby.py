"""eval_ruby tool - Execute arbitrary Ruby code in SketchUp"""

import json
import logging
from typing import Dict, Any

from ..connection import get_connection, parse_tool_response

logger = logging.getLogger("SketchupMCPServer")


def eval_ruby(code: str, request_id: Any = None) -> str:
    """
    Execute Ruby code in SketchUp and return the result.

    This is the power tool for advanced users. It can execute any valid
    SketchUp Ruby API code. The code runs in SketchUp's Ruby environment
    with full access to the SketchUp API.

    Args:
        code: Ruby code to execute
        request_id: Optional request ID for tracking

    Returns:
        JSON string with success status and result/error

    Example:
        eval_ruby("Sketchup.active_model.entities.length")
        eval_ruby("model = Sketchup.active_model; model.entities.add_face([0,0,0], [10,0,0], [10,10,0], [0,10,0])")
    """
    if not code or not code.strip():
        return json.dumps({
            "success": False,
            "error": "No code provided"
        })

    try:
        logger.info(f"eval_ruby: executing {len(code)} chars of Ruby code")

        connection = get_connection()
        result = connection.send_command(
            tool_name="eval_ruby",
            arguments={"code": code},
            request_id=request_id
        )

        success, text = parse_tool_response(result)
        if success:
            return json.dumps({"success": True, "result": text})
        else:
            return json.dumps({"success": False, "error": text})

    except ConnectionError as e:
        logger.error(f"eval_ruby connection error: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "hint": "Make sure SketchUp is running with the MCP extension started"
        })

    except Exception as e:
        logger.error(f"eval_ruby error: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })
