"""Centralized configuration for SketchUp MCP Server"""

from dataclasses import dataclass, field
import os


@dataclass
class MCPConfig:
    """Configuration settings for the MCP server."""

    host: str = "127.0.0.1"
    port: int = 9876
    timeout: float = 15.0
    max_retries: int = 2
    buffer_size: int = 8192

    # Image export defaults
    default_image_width: int = 1920
    default_image_height: int = 1080
    max_image_dimension: int = 8192
    min_image_dimension: int = 1

    # Authentication (optional shared secret)
    auth_secret: str = field(
        default_factory=lambda: os.environ.get("SKETCHUP_MCP_SECRET", "")
    )


# Global config instance
config = MCPConfig()
