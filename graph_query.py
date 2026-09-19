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

def find_script_variables(graph, script_path):
    script_path = normalize_path(script_path)

    with open("project_index.json", "r", encoding="utf-8") as f:
        index = json.load(f)

    for script in index["scripts"]:
        if normalize_path(script["file"]) == script_path:
            return {
                "script": script_path,
                "variables": script["variables"]
            }

    return {
        "script": script_path,
        "variables": []
    }

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

        # Node IDs have the format:
        # node:<scene_path>:<node_name>
        parts = node_id.split(":", 2)

        if len(parts) != 3:
            continue

        node_name = parts[2]

        node_info = {
            "node": node_name,
            "scripts": []
        }

        for node_edge in graph["edges"]:
            if (
                node_edge["from"] == node_id
                and node_edge["type"] == "attaches"
            ):
                script_id = node_edge["to"]

                # Script IDs have the format:
                # script:<script_path>
                script_path = script_id.replace("script:", "", 1)

                node_info["scripts"].append(
                    "res://" + script_path.replace("\\", "/")
                )

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

def find_resource(graph, resource_path):
    resource_path = normalize_path(resource_path)
    resource_id = f"resource:{resource_path}"

    result = {
        "resource": resource_path,
        "used_by": []
    }

    for edge in graph["edges"]:
        if edge["to"] == resource_id and edge["type"] == "preload":
            result["used_by"].append(edge["from"])

    return result

def query(query_type, value):
    graph = load_graph()

    if query_type == "class":
        return find_class(graph, value)

    if query_type == "resource":
        return find_resource(graph, value)
    
    if query_type == "script":
        return find_script(graph, value)
    
    if query_type == "variables":
        return find_script_variables(graph, value)

    if query_type == "scene":
        return find_scene(graph, value)

    if query_type == "context":
        return find_scene_context(graph, value)

    raise ValueError(f"Unknown query type: {query_type}")

def find_class_definition(graph, class_name):
    class_id = f"class:{class_name}"

    for edge in graph["edges"]:
        if (
            edge["from"] == class_id
            and edge["type"] == "defined_by"
        ):
            return edge["to"]


    return None

def find_script_usage(graph, script_path):
    script_path = normalize_path(script_path)
    script_id = f"script:{script_path}"

    usages = []

    for edge in graph["edges"]:
        if (
            edge["to"] != script_id
            or edge["type"] != "attaches"
        ):
            continue

        node_id = edge["from"]

        # Node IDs have the format:
        # node:<scene_path>:<node_name>
        parts = node_id.split(":", 2)

        if len(parts) != 3:
            continue

        scene_path = parts[1]
        node_name = parts[2]

        usages.append({
            "scene": scene_path,
            "node": node_name
        })

    return usages