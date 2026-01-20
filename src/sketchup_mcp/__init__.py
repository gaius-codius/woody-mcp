"""
SketchUp MCP - Model Context Protocol server for SketchUp

A tool for integrating SketchUp with Claude, designed for woodworkers,
makers, and beginners using SketchUp Make 2017.
"""

__version__ = "0.2.0"

from .server import mcp, main

__all__ = ["mcp", "main", "__version__"]
