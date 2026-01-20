# Woody MCP 🪵

AI-powered woodworking assistant for SketchUp Make 2017.

Woody connects your AI assistant of choice to SketchUp through MCP, letting you design furniture and woodworking projects with natural language.

## Attribution

Built on [sketchup-mcp](https://github.com/pturczyk/sketchup-mcp).
Inspired by [Blender MCP](https://github.com/ahujasid/blender-mcp).

## Features

- **Two-way TCP communication** with SketchUp
- **Model inspection** and scene info
- **Export** to SKP, PNG, JPG
- **Execute Ruby code** for full SketchUp API access
- **Bundled SketchUp 2017 API reference** so your assistant knows the API
- **Regional lumber standards** (Currently includes: Australia, North America, UK, Europe)

## Roadmap

**Coming Soon:**
- Project templates ("make me a bookshelf")
- Cut list generation for shopping trips
- More furniture templates (tables, cabinets, workbenches)

## Tools

| Tool | Description |
|------|-------------|
| `describe_model` | Get model info, entities, selection |
| `export_scene` | Export to .skp/.png/.jpg |
| `eval_ruby` | Run Ruby code in SketchUp |

## Two-Layer Design

Woody works at two levels:

- **Templates** (coming soon): High-level commands like "make me a bookshelf with 3 shelves" that generate complete projects
- **eval_ruby**: Direct access to the SketchUp Ruby API for advanced users. Bundled API docs as reference to write SketchUp Ruby code.

## Installation

### Requirements

- SketchUp Make 2017 (free version works great)
- Python 3.10+
- uv (`brew install uv` on macOS)

### SketchUp Extension

1. Download the latest `.rbz` file from releases
2. In SketchUp: Window > Extension Manager
3. Click "Install Extension" and select the `.rbz` file
4. Restart SketchUp

### Claude Desktop Configuration

Add to your Claude Desktop config:

```json
{
    "mcpServers": {
        "woody": {
            "command": "uvx",
            "args": ["woody-mcp"]
        }
    }
}
```

### Starting the Connection

1. In SketchUp: Extensions > SketchupMCP > Start Server
2. The server starts on port 9876
3. AI assistant will connect automatically when you chat

## Example Prompts

Try asking:

- "What components are in my model?"
- "Export my design as a PNG"
- "Create a simple box joint box" (uses eval_ruby)
- "Show me the model dimensions"
- "Make the selected component 2 inches taller"

**Coming in Phase 2:**
- "Make me a bookshelf with 3 shelves"
- "Generate a cut list for this project"

## Troubleshooting

- **Connection issues**: Make sure the SketchUp extension server is running (Extensions > SketchupMCP > Start Server)
- **Command failures**: Check the Ruby Console in SketchUp (Window > Ruby Console) for error messages
- **Timeout errors**: Try simplifying your requests or breaking them into smaller steps
