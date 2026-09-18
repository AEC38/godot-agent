import json
from pathlib import Path

GRAPH_FILE = Path("project_graph.json")


def load_graph():
    with GRAPH_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_path(path):
    return path.replace("res://", "").replace("/", "\\")


def find_class(graph, class_name):
    class_id = f"class:{class_name}"

    result = {
        "class": class_name,
        "defined_by": [],
        "used_by": [],
        "children": [],
    }

    for edge in graph["edges"]:

        if (
            edge["from"] == class_id
            and edge["type"] == "defined_by"
        ):
            result["defined_by"].append(edge["to"])

        elif (
            edge["to"] == class_id
            and edge["type"] == "uses"
        ):
            result["used_by"].append(edge["from"])

        elif (
            edge["to"] == class_id
            and edge["type"] == "extends"
        ):
            result["children"].append(edge["from"])

    return result


def find_script(graph, script_path):
    script_path = normalize_path(script_path)
    script_id = f"script:{script_path}"

    result = {
        "script": script_path,
        "extends": [],
        "uses": [],
    }

    for edge in graph["edges"]:

        if edge["from"] != script_id:
            continue

        if edge["type"] == "extends":
            result["extends"].append(edge["to"])

        elif edge["type"] == "uses":
            result["uses"].append(edge["to"])

    return result


def find_scene(graph, scene_path):
    scene_path = normalize_path(scene_path)
    scene_id = f"scene:{scene_path}"

    result = {
        "scene": scene_path,
        "nodes": []
    }

    for edge in graph["edges"]:

        if edge["from"] != scene_id:
            continue

        if edge["type"] != "contains":
            continue

        node_id = edge["to"]

        node_info = {
            "node": node_id,
            "scripts": []
        }

        for node_edge in graph["edges"]:

            if (
                node_edge["from"] == node_id
                and node_edge["type"] == "attaches"
            ):
                node_info["scripts"].append(node_edge["to"])

        result["nodes"].append(node_info)

    return result


def find_scene_context(graph, scene_path):
    scene_path = normalize_path(scene_path)
    scene_id = f"scene:{scene_path}"

    result = {
        "scene": scene_path,
        "nodes": []
    }

    for edge in graph["edges"]:

        if (
            edge["from"] != scene_id
            or edge["type"] != "contains"
        ):
            continue

        node_id = edge["to"]

        node_info = {
            "node": node_id,
            "scripts": []
        }

        for node_edge in graph["edges"]:

            if (
                node_edge["from"] == node_id
                and node_edge["type"] == "attaches"
            ):
                script_id = node_edge["to"]

                script_info = {
                    "script": script_id,
                    "relationships": []
                }

                for script_edge in graph["edges"]:

                    if script_edge["from"] == script_id:
                        if script_edge["type"] in ["extends", "uses"]:
                            script_info["relationships"].append({
                                "type": script_edge["type"],
                                "target": script_edge["to"]
                            })

                node_info["scripts"].append(script_info)

        result["nodes"].append(node_info)

    return result