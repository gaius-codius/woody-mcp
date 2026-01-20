"""describe_model tool - Get information about the current SketchUp model"""

import json
import logging
from typing import Any

from ..connection import get_connection, parse_tool_response

logger = logging.getLogger("SketchupMCPServer")


def describe_model(include_details: bool = False, request_id: Any = None) -> str:
    """
    Get information about the current SketchUp model.

    Returns a description of the active model including:
    - Model name and file path
    - Entity counts (groups, components, faces, edges)
    - Current selection
    - Model bounds

    Args:
        include_details: If True, include detailed info about groups/components
        request_id: Optional request ID for tracking

    Returns:
        JSON string with model description
    """
    try:
        logger.info(f"describe_model: include_details={include_details}")

        connection = get_connection()
        result = connection.send_command(
            tool_name="describe_model",
            arguments={"include_details": include_details},
            request_id=request_id
        )

        success, text = parse_tool_response(result)
        if success:
            # The Ruby side returns JSON, pass it through
            return text
        else:
            return json.dumps({"success": False, "error": text})

    except ConnectionError as e:
        logger.error(f"describe_model connection error: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "hint": "Make sure SketchUp is running with the MCP extension started"
        })

    except Exception as e:
        logger.error(f"describe_model error: {str(e)}")
        return json.dumps({"success": False, "error": str(e)})
