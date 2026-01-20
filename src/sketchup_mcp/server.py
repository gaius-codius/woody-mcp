"""
SketchUp MCP Server

A Model Context Protocol server for integrating SketchUp with Claude.
Designed for woodworkers, makers, and beginners using SketchUp Make 2017.
"""

from mcp.server.fastmcp import FastMCP, Context
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any, Optional

from .connection import get_connection, close_connection
from .tools import eval_ruby as eval_ruby_tool
from .tools import describe_model as describe_model_tool
from .tools import export_scene as export_scene_tool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SketchupMCPServer")

__version__ = "0.2.0"


@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Manage server startup and shutdown lifecycle"""
    logger.info(f"SketchUp MCP Server v{__version__} starting")

    # Try to connect on startup (non-fatal if it fails)
    try:
        connection = get_connection()
        if connection.connect():
            logger.info("Connected to SketchUp on startup")
        else:
            logger.warning(
                "Could not connect to SketchUp on startup. "
                "Make sure SketchUp is running with the MCP extension started."
            )
    except Exception as e:
        logger.warning(f"SketchUp connection not available: {str(e)}")

    yield {}

    # Cleanup on shutdown
    logger.info("Shutting down SketchUp MCP Server")
    close_connection()


# Create MCP server
mcp = FastMCP(
    "SketchupMCP",
    lifespan=server_lifespan
)


# =============================================================================
# Tool Definitions
# =============================================================================

@mcp.tool()
def eval_ruby(ctx: Context, code: str) -> str:
    """
    Execute Ruby code in SketchUp.

    This is the power tool for advanced operations. It can execute any valid
    SketchUp Ruby API code. Use this for operations not covered by other tools.

    Args:
        code: Ruby code to execute in SketchUp

    Returns:
        JSON with success status and result or error message

    Examples:
        - Get entity count: "Sketchup.active_model.entities.length"
        - Create a cube: See resources/recipes.md for code patterns
        - Apply material: "Sketchup.active_model.selection[0].material = 'red'"
    """
    return eval_ruby_tool.eval_ruby(code, request_id=ctx.request_id)


@mcp.tool()
def describe_model(ctx: Context, include_details: bool = False) -> str:
    """
    Get information about the current SketchUp model.

    Returns a description of the active model including entity counts,
    current selection, and model bounds.

    Args:
        include_details: If True, include detailed info about each group/component

    Returns:
        JSON with model information:
        - name: Model name
        - path: File path (if saved)
        - units: Model units setting
        - entities: Counts of groups, components, faces, edges
        - selection: Currently selected items
        - bounds: Model bounding box dimensions
    """
    return describe_model_tool.describe_model(
        include_details=include_details,
        request_id=ctx.request_id
    )


@mcp.tool()
def export_scene(
    ctx: Context,
    format: str = "skp",
    width: Optional[int] = None,
    height: Optional[int] = None
) -> str:
    """
    Export the current SketchUp model to a file.

    Args:
        format: Export format - "skp", "png", or "jpg"
        width: Image width in pixels (for png/jpg, default 1920)
        height: Image height in pixels (for png/jpg, default 1080)

    Returns:
        JSON with success status and file path
    """
    return export_scene_tool.export_scene(
        format=format,
        width=width,
        height=height,
        request_id=ctx.request_id
    )


# =============================================================================
# Entry Point
# =============================================================================

def main():
    """Run the MCP server"""
    logger.info(f"Starting SketchUp MCP Server v{__version__}")
    mcp.run()


if __name__ == "__main__":
    main()
