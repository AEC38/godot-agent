from mcp.server.mcpserver import MCPServer

from graph_query import (
    query,
    load_graph,
    find_class_definition,
    find_script_usage,
)
from pathlib import Path

GODOT_PROJECT = Path(r"C:\Users\berke\OneDrive\Desktop\silicon_frontier")

server = MCPServer("godot-project")


@server.tool()
def query_project(query_type: str, value: str) -> dict:
    """
    Query the Godot project graph.

    query_type:
        class    - information about a class
        script   - dependencies and relationships of a script
        scene    - nodes and attached scripts in a scene
        context  - detailed scene context

    value:
        Class name or Godot project path.
    """

    return query(query_type, value)


@server.tool()
def read_project_file(path: str) -> str:
    """
    Read a text file from the Godot project.

    path:
        Godot project path such as:
        res://Machines/Scripts/wafer_slicer.gd
    """

    relative_path = path.replace("res://", "").replace("/", "\\")

    project_root = GODOT_PROJECT.resolve()
    file_path = (project_root / relative_path).resolve()

    # Prevent access outside the Godot project
    try:
        file_path.relative_to(project_root)
    except ValueError:
        raise PermissionError(
            f"Access outside the Godot project is not allowed: {path}"
        )

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    return file_path.read_text(encoding="utf-8")

@server.tool()
def search_project(text: str) -> list:
    """
    Search the Godot project source files for text.

    Searches:
    - GDScript (.gd)
    - Scenes (.tscn)
    - Resources (.tres)
    - Project configuration (.godot)

    Returns matching files and line numbers.
    """

    results = []

    searchable_extensions = {
        ".gd",
        ".tscn",
        ".tres",
        ".godot",
    }

    search_text = text.lower()

    for path in GODOT_PROJECT.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in searchable_extensions:
            continue

        try:
            lines = path.read_text(
                encoding="utf-8",
                errors="ignore"
            ).splitlines()

        except Exception:
            continue

        matches = []

        for line_number, line in enumerate(lines, start=1):
            if search_text in line.lower():
                matches.append({
                    "line": line_number,
                    "text": line.strip(),
                })

        if matches:
            relative_path = path.relative_to(GODOT_PROJECT)

            results.append({
                "file": "res://" + str(relative_path).replace("\\", "/"),
                "matches": matches,
            })

    return results

@server.tool()
def get_context(path: str) -> dict:
    """
    Get useful coding context for a Godot script.

    Includes:
    - source code
    - inheritance
    - used classes
    - source code of directly related classes
    """

    graph = load_graph()
    graph_context = query("script", path)
    source = read_project_file(path)

    script_usages = find_script_usage(graph, path)
    scene_context = []

    for usage in script_usages:
        scene_path = usage["scene"]

        scene_info = query(
            "scene",
            "res://" + scene_path.replace("\\", "/")
        )

    scene_context.append(scene_info)

    related_classes = {}

    class_ids = (
        graph_context["extends"]
        + graph_context["uses"]
    )

    for class_id in class_ids:
        class_name = class_id.replace("class:", "")

        definition = find_class_definition(
            graph,
            class_name
        )

        if definition:
            # definition is like:
            # script:Scripts\machine.gd
            definition_path = definition.replace("script:", "")
            definition_path = (
                "res://" + definition_path.replace("\\", "/")
            )

            related_classes[class_name] = {
                "script": definition_path,
                "source": read_project_file(definition_path)
            }

    return {
            "script": path,
            "source": source,
            "extends": graph_context["extends"],
            "uses": graph_context["uses"],
            "related_classes": related_classes,
            "used_by": script_usages,
            "scene_context": scene_context,
    }

 
if __name__ == "__main__":
    server.run()