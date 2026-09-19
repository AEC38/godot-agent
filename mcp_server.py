from mcp.server.mcpserver import MCPServer
import subprocess
import re

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
        resource - scripts that preload a resource
        variables - variables declared in a script

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
def execute_godot_script(path: str) -> str:
    """
    Run a Godot script in headless mode and capture the console output.
    Useful for testing matrix math, MNA logic, or running test suites.
    
    path:
        Godot project path such as res://Scripts/test_script.gd
    """
    relative_path = path.replace("res://", "").replace("/", "\\")
    project_root = GODOT_PROJECT.resolve()
    file_path = (project_root / relative_path).resolve()

    try:
        file_path.relative_to(project_root)
    except ValueError:
        raise PermissionError("Access outside the Godot project is not allowed.")

    if not file_path.exists():
        raise FileNotFoundError(f"Script not found: {path}")

    try:
        # Godot 4 CLI syntax for headless script execution
        result = subprocess.run(
            ["godot", "--headless", "--script", str(file_path)],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30 # Prevent infinite loops in MNA solvers
        )
        
        output = result.stdout
        if result.stderr:
            output += "\n--- STDERR ---\n" + result.stderr
            
        return output.strip() if output.strip() else "Script executed successfully with no output."
        
    except FileNotFoundError:
        return "Error: 'godot' command not found. Ensure Godot is in your system PATH."
    except subprocess.TimeoutExpired:
        return "Error: Script execution timed out after 30 seconds."
    except Exception as e:
        return f"Execution error: {str(e)}"

@server.tool()
def read_resource_summary(path: str) -> str:
    """
    Read a .tres resource file, summarizing massive data arrays to save context window space.
    
    path:
        Godot project path such as res://Resources/my_resource.tres
    """
    relative_path = path.replace("res://", "").replace("/", "\\")
    project_root = GODOT_PROJECT.resolve()
    file_path = (project_root / relative_path).resolve()

    if not file_path.exists():
        raise FileNotFoundError(f"Resource not found: {path}")

    content = file_path.read_text(encoding="utf-8", errors="ignore")
    
    # Truncate massive Godot 4 arrays (e.g., PackedFloat32Array(1, 2, 3...))
    content = re.sub(
        r'(Packed(?:Float32|Float64|Int32|Int64|Vector2|Vector3|Color)Array)\(([^)]+)\)',
        lambda m: f"{m.group(1)}(... {len(m.group(2).split(','))} items ...)",
        content
    )
    
    return content

def get_script_summary(script_path: str) -> dict:
    import json
    
    # Normalize path to match the index format
    normalized_path = script_path.replace("res://", "").replace("/", "\\")
    
    try:
        with open("project_index.json", "r", encoding="utf-8") as f:
            index = json.load(f)
            
        for script in index["scripts"]:
            if script["file"] == normalized_path:
                return {
                    "extends": script.get("extends"),
                    "variables": script.get("variables", []),
                    "signals": script.get("signals", []),
                    "functions": script.get("functions", [])
                }
    except Exception:
        pass
        
    return {"error": "Summary not available"}

def get_scene_hierarchy(scene_path: str) -> dict:
    import json
    
    normalized_path = scene_path.replace("res://", "").replace("/", "\\")
    
    try:
        with open("project_index.json", "r", encoding="utf-8") as f:
            index = json.load(f)
            
        for scene in index.get("scenes", []):
            if scene["file"] == normalized_path:
                return {
                    "scene": scene_path,
                    "nodes": scene.get("nodes", [])
                }
    except Exception:
        pass
        
    return {"scene": scene_path, "nodes": []}

def get_inheritance_chain(script_path: str) -> list:
    import json
    
    normalized_path = script_path.replace("res://", "").replace("/", "\\")
    chain = []
    
    try:
        with open("project_index.json", "r", encoding="utf-8") as f:
            index = json.load(f)
            
        class_to_file = index.get("class_to_file", {})
        current_path = normalized_path
        
        while current_path:
            # Find the script in the index
            current_script = None
            for script in index.get("scripts", []):
                if script["file"] == current_path:
                    current_script = script
                    break
                    
            if not current_script:
                break
                
            parent_class = current_script.get("extends")
            if not parent_class:
                break
                
            chain.append(parent_class)
            
            # Move up to the parent's file for the next loop iteration
            current_path = class_to_file.get(parent_class)
            
    except Exception:
        pass
        
    return chain

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

            scene_info = get_scene_hierarchy(
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
                "summary": get_script_summary(definition_path)
            }

    return {
            "script": path,
            "source": source,
            "inheritance_chain": get_inheritance_chain(path),
            "extends": graph_context["extends"],
            "uses": graph_context["uses"],
            "related_classes": related_classes,
            "used_by": script_usages,
            "scene_context": scene_context,
    }

 
if __name__ == "__main__":
    server.run()
