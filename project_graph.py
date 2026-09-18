import json
import argparse
from pathlib import Path

from graph_query import ( # type: ignore
    find_class,
    find_script,
    find_scene,
    find_scene_context,
)

INDEX_FILE = Path("project_index.json")
GRAPH_FILE = Path("project_graph.json")


def normalize_path(path):
    return path.replace("res://", "").replace("/", "\\")


def load_index():
    with INDEX_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_graph(index):
    nodes = []
    edges = []

    # ---------------------------------------------------------
    # Scripts
    # ---------------------------------------------------------

    for script in index["scripts"]:
        script_path = normalize_path(script["file"])
        script_id = f"script:{script_path}"

        nodes.append({
            "id": script_id,
            "type": "script",
            "name": script_path,
        })

        # Script relationships
        for relationship in script["relationships"]:
            target_class = relationship["class"]

            target_id = f"class:{target_class}"

            edges.append({
                "from": script_id,
                "to": target_id,
                "type": relationship["type"],
            })

    # ---------------------------------------------------------
    # Classes
    # ---------------------------------------------------------

    for script in index["scripts"]:
        if script["class"]:
            class_id = f"class:{script['class']}"

            script_path = normalize_path(script["file"])
            script_id = f"script:{script_path}"

            nodes.append({
                "id": class_id,
                "type": "class",
                "name": script["class"],
            })

            edges.append({
                "from": class_id,
                "to": script_id,
                "type": "defined_by",
            })

    # ---------------------------------------------------------
    # Scenes and nodes
    # ---------------------------------------------------------

    for scene in index["scenes"]:
        scene_path = normalize_path(scene["file"])
        scene_id = f"scene:{scene_path}"

        nodes.append({
            "id": scene_id,
            "type": "scene",
            "name": scene_path,
        })

        for node in scene["nodes"]:
            node_id = f"node:{scene_path}:{node['name']}"

            nodes.append({
                "id": node_id,
                "type": "node",
                "name": node["name"],
            })

            # Scene contains node
            edges.append({
                "from": scene_id,
                "to": node_id,
                "type": "contains",
            })

            # Node has attached script
            if node["script"]:
                script_path = normalize_path(node["script"])
                script_id = f"script:{script_path}"

                edges.append({
                    "from": node_id,
                    "to": script_id,
                    "type": "attaches",
                })

    return {
        "nodes": nodes,
        "edges": edges,
    }


def print_class_result(result):
    print(f"\nClass: {result['class']}")

    print("Defined by:")
    for item in result["defined_by"]:
        print(f"  - {item}")

    print("Used by:")
    for item in result["used_by"]:
        print(f"  - {item}")

    print("Extended by:")
    for item in result["children"]:
        print(f"  - {item}")



def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--class",
        dest="class_name",
        help="Find information about a class"
    )

    parser.add_argument(
        "--script",
        dest="script_path",
        help="Find information about a script"
    )

    parser.add_argument(
        "--scene",
        dest="scene_path",
        help="Find information about a scene"
    )

    parser.add_argument(
        "--context",
        dest="context_path",
        help="Show the connected context of a scene"
)
    args = parser.parse_args()

    index = load_index()
    graph = build_graph(index)

    with GRAPH_FILE.open("w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)

    print(f"Graph saved to {GRAPH_FILE}")
    print(f"Nodes: {len(graph['nodes'])}")
    print(f"Edges: {len(graph['edges'])}")

    if args.class_name:
        result = find_class(graph, args.class_name)
        print_class_result(result)

    if args.script_path:
        result = find_script(graph, args.script_path)

        print(f"\nScript: {result['script']}")

        print("Extends:")
        for item in result["extends"]:
            print(f"  - {item}")

        print("Uses:")
        for item in result["uses"]:
            print(f"  - {item}")

    if args.scene_path:
        result = find_scene(graph, args.scene_path)

        print(f"\nScene: {result['scene']}")

        print("Nodes:")
        for node in result["nodes"]:
            print(f"  - {node['node']}")

            for script in node["scripts"]:
                print(f"      script → {script}")

    if args.context_path:
        result = find_scene_context(graph, args.context_path)

        print(f"\nScene context: {result['scene']}")

        for node in result["nodes"]:
            print(f"\nNode: {node['node']}")

            for script in node["scripts"]:
                print(f"  Script: {script['script']}")

                for relationship in script["relationships"]:
                    print(
                        f"    {relationship['type']} → "
                        f"{relationship['target']}"
                    )

if __name__ == "__main__":
    main()