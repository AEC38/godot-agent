from pathlib import Path
import json

INDEX_FILE = Path("project_index.json")


def load_index():
    with INDEX_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def find_script_usage(index, script_path):
    results = []

    for scene in index["scenes"]:
        for node in scene["nodes"]:

            if node["script"] == script_path:
                results.append({
                    "scene": scene["file"],
                    "node": node["name"]
                })

    return results


def find_scene_dependencies(index, scene_path):
    for scene in index["scenes"]:

        if scene["file"] == scene_path:

            dependencies = []

            for node in scene["nodes"]:

                if node["script"]:
                    dependencies.append({
                        "node": node["name"],
                        "script": node["script"]
                    })

            return dependencies

    return []

import sys

def find_script_dependencies(index, script_path):
    script_path = script_path.replace("res://", "").replace("/", "\\")

    for script in index["scripts"]:
        if script["file"] == script_path:
            return script["relationships"]

    return []

def find_script_inheritance(index, script_path):
    script_path = script_path.replace("res://", "").replace("/", "\\")

    for script in index["scripts"]:
        if script["file"] == script_path:
            return script["extends"]

    return None

def find_inheritance_chain(index, script_path):
    script_path = script_path.replace("res://", "").replace("/", "\\")

    class_to_file = index["class_to_file"]
    chain = []

    current_path = script_path

    while current_path:
        current_script = None

        for script in index["scripts"]:
            if script["file"] == current_path:
                current_script = script
                break

        if current_script is None:
            break

        current_class = current_script["class"]
        parent_class = current_script["extends"]

        display_class = current_class

        if display_class is None:
            display_class = Path(current_script["file"]).stem

        chain.append({
            "class": display_class,
            "extends": parent_class,
            "file": current_script["file"]
        })

        if not parent_class:
            break

        parent_path = class_to_file.get(parent_class)

        if not parent_path:
            # Godot built-in class, e.g. Node3D, Control, etc.
            chain.append({
                "class": parent_class,
                "extends": None,
                "file": None
            })
            break

        current_path = parent_path

    return chain

def find_children_of_class(index, class_name):
    results = []

    for script in index["scripts"]:
        if script["extends"] == class_name:
            results.append({
                "file": script["file"],
                "class": script["class"]
            })

    return results

def search_project(index, query):
    query = query.lower()

    results = {
        "scripts": [],
        "scenes": [],
        "nodes": []
    }

    for script in index["scripts"]:
        if query in script["file"].lower():
            results["scripts"].append(script["file"])

    for scene in index["scenes"]:
        if query in scene["file"].lower():
            results["scenes"].append(scene["file"])

        for node in scene["nodes"]:
            node_name = node["name"] or ""

            if query in node_name.lower():
                results["nodes"].append({
                    "scene": scene["file"],
                    "node": node["name"],
                    "type": node["type"],
                    "script": node["script"]
                })

    return results

def main():
    index = load_index()

    if len(sys.argv) < 3:
        print("Usage:")
        print("  python query_project.py --search <text>")
        print("  python query_project.py --usage <script_path>")
        print("  python query_project.py --dependencies <script_path>")
        print("  python query_project.py --inheritance <script_path>")
        print("  python query_project.py --children <class_name>")
        return

    command = sys.argv[1]
    target = sys.argv[2]

    if command == "--usage":

        results = find_script_usage(index, target)

        print(f"\nScenes using {target}:\n")

        if not results:
            print("No scenes found.")
            return

        for result in results:
            print(
                f"- {result['scene']} "
                f"→ node: {result['node']}"
            )

    elif command == "--dependencies":

        results = find_script_dependencies(index, target)

        print(f"\nDependencies of {target}:\n")

        if not results:
            print("No script dependencies found.")
            return

        for result in results:
            print(
                f"- {result['type']} → "
                f"{result['class']} → "
                f"{result['file']}"
            )

    elif command == "--inheritance":

        results = find_inheritance_chain(index, target)

        print(f"\nInheritance chain of {target}:\n")

        for item in results:
            if item["extends"]:
                print(
                    f"- {item['class']} "
                    f"→ extends {item['extends']}"
                )
            else:
                print(f"- {item['class']}")

    elif command == "--children":

        results = find_children_of_class(index, target)

        print(f"\nScripts extending {target}:\n")

        if not results:
            print("No scripts found.")
            return

        for result in results:
            display_name = result["class"]

            if display_name is None:
                display_name = Path(result["file"]).stem

            print(
                f"- {display_name} "
                f"→ {result['file']}"
            )
    elif command == "--search":

        results = search_project(index, target)

        print(f"\nSearch results for '{target}':\n")

        print("Scripts:")
        for script in results["scripts"]:
            print(f"- {script}")

        print("\nScenes:")
        for scene in results["scenes"]:
            print(f"- {scene}")

        print("\nNodes:")
        for node in results["nodes"]:
            print(
                f"- {node['scene']} → "
                f"{node['node']} "
                f"({node['type']})"
            )
    else:

        print(f"Unknown command: {command}")
        print("Use --usage, --dependencies, --inheritance, or --children.")


if __name__ == "__main__":
    main()