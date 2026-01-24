"""get_cut_list - Generate lumber shopping list from SketchUp model."""

import json
import logging
from typing import Any
from pathlib import Path

from ..connection import get_connection, parse_tool_response

logger = logging.getLogger("SketchupMCPServer")


def load_lumber_standards() -> dict:
    """
    Load regional lumber standards from resources.

    Returns:
        Dict of regional lumber standards

    Raises:
        ValueError: If standards file is missing or corrupted
    """
    resources_path = (
        Path(__file__).parent.parent / "resources" / "lumber_standards.json"
    )
    try:
        with open(resources_path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Lumber standards file not found at {resources_path}")
        raise ValueError(
            f"Regional lumber standards configuration is missing. "
            f"Expected file at: {resources_path}"
        )
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in lumber standards file: {e}")
        raise ValueError(f"Regional lumber standards file is corrupted: {e}")


def get_cut_list(region: str = "australia", request_id: Any = None) -> str:
    """
    Generate a cut list (lumber shopping list) from the current SketchUp model.

    Analyzes all groups and components in the model, extracts their dimensions,
    and formats them as a lumber shopping list using regional standards.

    Args:
        region: Region for lumber sizing ("australia", "north_america", "uk", "europe")
        request_id: Optional request ID for tracking

    Returns:
        JSON string with cut_list array and total board feet/meters
    """
    try:
        logger.info(f"get_cut_list: region={region}")

        # Load lumber standards for region
        standards = load_lumber_standards()

        # Validate region
        if region not in standards:
            available_regions = list(standards.keys())
            if "australia" in standards:
                logger.warning(
                    f"Unknown region '{region}', falling back to australia. "
                    f"Available: {available_regions}"
                )
                region_data = standards["australia"]
                region_warning = (
                    f"Note: Region '{region}' not found, using Australian standards"
                )
            else:
                return json.dumps(
                    {
                        "success": False,
                        "error": f"Unknown region '{region}' and no fallback available. "
                        f"Valid regions: {', '.join(available_regions)}",
                    }
                )
        else:
            region_data = standards[region]
            region_warning = None

        units = region_data.get("units", "mm")

        # Ruby code to extract all groups and components with their bounding box dimensions
        ruby_code = """
result = []
model = Sketchup.active_model
entities = model.active_entities

entities.grep(Sketchup::Group).each do |group|
  bounds = group.bounds
  # Get dimensions in mm
  width = bounds.width.to_mm
  height = bounds.height.to_mm
  depth = bounds.depth.to_mm

  # Sort dimensions to get length (longest), width, thickness (shortest)
  dims = [width, height, depth].sort.reverse

  result << {
    "name" => group.name.empty? ? "Unnamed" : group.name,
    "length" => dims[0].round(1),
    "width" => dims[1].round(1),
    "thickness" => dims[2].round(1)
  }
end

entities.grep(Sketchup::ComponentInstance).each do |comp|
  bounds = comp.bounds
  dims = [bounds.width.to_mm, bounds.height.to_mm, bounds.depth.to_mm].sort.reverse

  result << {
    "name" => comp.definition.name,
    "length" => dims[0].round(1),
    "width" => dims[1].round(1),
    "thickness" => dims[2].round(1)
  }
end

result.to_json
"""

        connection = get_connection()
        eval_result = connection.send_command(
            tool_name="eval_ruby", arguments={"code": ruby_code}, request_id=request_id
        )

        success, text = parse_tool_response(eval_result)

        if not success:
            return json.dumps(
                {"success": False, "error": f"Failed to analyze model: {text}"}
            )

        # Parse the result
        try:
            pieces = json.loads(text)
        except json.JSONDecodeError:
            return json.dumps(
                {"success": False, "error": f"Invalid response from SketchUp: {text}"}
            )

        if not pieces:
            return json.dumps(
                {
                    "success": True,
                    "cut_list": [],
                    "message": "No groups or components found in model",
                    "region": region,
                }
            )

        # Group similar pieces
        grouped = {}
        for piece in pieces:
            key = (piece["length"], piece["width"], piece["thickness"])
            if key in grouped:
                grouped[key]["quantity"] += 1
                grouped[key]["names"].append(piece["name"])
            else:
                grouped[key] = {
                    "length": piece["length"],
                    "width": piece["width"],
                    "thickness": piece["thickness"],
                    "quantity": 1,
                    "names": [piece["name"]],
                }

        # Format cut list
        cut_list = []
        total_volume_mm3 = 0

        for dims, data in sorted(grouped.items(), key=lambda x: -x[0][0]):
            volume = (
                data["length"] * data["width"] * data["thickness"] * data["quantity"]
            )
            total_volume_mm3 += volume

            cut_list.append(
                {
                    "dimensions": f"{data['thickness']:.0f}x{data['width']:.0f}x{data['length']:.0f}mm",
                    "quantity": data["quantity"],
                    "parts": data["names"],
                    "notes": "",
                }
            )

        # Calculate board feet (for North America) or cubic meters
        if region == "north_america":
            # Board feet = (thickness_in × width_in × length_in) / 144
            # Convert mm³ to in³: divide by 25.4³ (mm per inch, cubed)
            # Then divide by 144 (12×12) for board feet formula
            total_board_feet = total_volume_mm3 / (25.4**3) / 144
            total_measure = f"{total_board_feet:.2f} board feet"
        else:
            # Cubic meters
            total_m3 = total_volume_mm3 / (1000**3)
            total_measure = f"{total_m3:.4f} cubic meters"

        return json.dumps(
            {
                "success": True,
                "cut_list": cut_list,
                "total_pieces": sum(item["quantity"] for item in cut_list),
                "total_volume": total_measure,
                "region": region,
                "units": units,
            }
        )

    except ConnectionError as e:
        logger.error(f"get_cut_list connection error: {e}")
        return json.dumps(
            {
                "success": False,
                "error": str(e),
                "hint": "Make sure SketchUp is running with the MCP extension started",
            }
        )

    except (ValueError, TypeError, KeyError) as e:
        logger.warning(f"get_cut_list data error: {e}")
        return json.dumps({"success": False, "error": str(e)})

    except Exception as e:
        logger.exception(f"get_cut_list unexpected error: {e}")
        raise
