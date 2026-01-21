"""
SketchUp MCP Server

A Model Context Protocol server for integrating SketchUp with Claude.
Designed for woodworkers, makers, and beginners using SketchUp Make 2017.
"""

from mcp.server.fastmcp import FastMCP, Context
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any, Optional

from . import __version__
from .connection import get_connection, close_connection
from .tools import eval_ruby as eval_ruby_tool
from .tools import describe_model as describe_model_tool
from .tools import export_scene as export_scene_tool
from .tools import build_project as build_project_tool
from .tools import get_cut_list as get_cut_list_tool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SketchupMCPServer")


@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Manage server startup and shutdown lifecycle"""
    logger.info(f"SketchUp MCP Server v{__version__} starting")

    # Try to connect on startup (non-fatal if it fails)
    # Note: connect() is blocking but acceptable for startup.
    # Consider asyncio.to_thread() if connection latency becomes an issue.
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
    export_format: str = "skp",
    width: Optional[int] = None,
    height: Optional[int] = None
) -> str:
    """
    Export the current SketchUp model to a file.

    Args:
        export_format: Export format - "skp", "png", or "jpg"
        width: Image width in pixels (for png/jpg, default 1920)
        height: Image height in pixels (for png/jpg, default 1080)

    Returns:
        JSON with success status and file path
    """
    return export_scene_tool.export_scene(
        export_format=export_format,
        width=width,
        height=height,
        request_id=ctx.request_id
    )


@mcp.tool()
def build_project(
    ctx: Context,
    template_type: str,
    width: Optional[float] = None,
    height: Optional[float] = None,
    depth: Optional[float] = None,
    lumber: str = "90x19",
    joinery: Optional[str] = None,
    material: str = "pine",
    region: str = "australia",
    options: Optional[Dict[str, Any]] = None
) -> str:
    """
    Build a woodworking project from a template.

    Creates complete 3D models in SketchUp from predefined templates.
    Templates include furniture (bookshelf, table) and small projects (box, cutting board).

    Args:
        template_type: Type of project - "bookshelf", "box", etc.
        width: Width in mm (uses template default if not specified)
        height: Height in mm (uses template default if not specified)
        depth: Depth in mm (uses template default if not specified)
        lumber: Lumber size (e.g., "90x19" for Australia, "2x4" for North America)
        joinery: Joint type - "butt", "dado", "finger_joint", "mortise_tenon", etc.
        material: Wood species - "pine", "oak", "walnut", etc.
        region: Region for lumber standards - "australia", "north_america", "uk", "europe"
        options: Template-specific options (e.g., {"shelves": 4} for bookshelf)

    Returns:
        JSON with success status, cut_list with lumber requirements, and dimensions

    Examples:
        build_project("bookshelf", width=600, height=1000, depth=300, options={"shelves": 3})
        build_project("box", width=200, height=100, depth=150, options={"has_lid": True})
    """
    return build_project_tool.build_project(
        template_type=template_type,
        width=width,
        height=height,
        depth=depth,
        lumber=lumber,
        joinery=joinery,
        material=material,
        region=region,
        options=options,
        request_id=ctx.request_id
    )


@mcp.tool()
def list_templates(ctx: Context) -> str:
    """
    List all available project templates.

    Returns information about each template including name, description,
    and default joinery type.

    Returns:
        JSON with list of available templates
    """
    return build_project_tool.list_templates()


@mcp.tool()
def get_cut_list(
    ctx: Context,
    region: str = "australia",
    include_hardware: bool = False
) -> str:
    """
    Generate a lumber shopping list from the current SketchUp model.

    Analyzes all groups and components, extracts dimensions, and formats
    them as a cut list with quantities. Similar pieces are grouped together.

    Args:
        region: Region for lumber sizing - "australia", "north_america", "uk", "europe"
        include_hardware: Include hardware notes from component names

    Returns:
        JSON with cut_list array, total pieces, and total volume

    Example output:
        {
            "cut_list": [
                {"dimensions": "19x90x1000mm", "quantity": 2, "parts": ["Left Side", "Right Side"]},
                {"dimensions": "19x90x562mm", "quantity": 4, "parts": ["Shelf 1", "Shelf 2", ...]}
            ],
            "total_pieces": 6,
            "total_volume": "0.0123 cubic meters"
        }
    """
    return get_cut_list_tool.get_cut_list(
        region=region,
        include_hardware=include_hardware,
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
