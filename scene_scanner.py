from pathlib import Path
import re
import json

GODOT_PROJECT = Path(r"C:\Users\berke\OneDrive\Desktop\silicon_frontier")

OUTPUT_FILE = Path("scene_index.json")


def scan_scene(path: Path):
    content = path.read_text(
        encoding="utf-8",
        errors="ignore"
    )

        # ---------------------------------------------------------
    # External resources
    # ---------------------------------------------------------

    ext_resources = {}

    for match in re.finditer(
        r'\[ext_resource[^\]]*path="([^"]+)"\s+id="([^"]+)"\]',
        content
    ):
        resource_path = match.group(1)
        resource_id = match.group(2)

        ext_resources[resource_id] = resource_path

    # ---------------------------------------------------------
    # Nodes
    # ---------------------------------------------------------

    nodes = []

    node_blocks = re.split(
        r'(?=\[node[^\]]*\])',
        content
    )

    for block in node_blocks:

        if not block.startswith("[node"):
            continue

        header_match = re.search(
            r'\[node([^\]]*)\]',
            block
        )

        if not header_match:
            continue

        header = header_match.group(1)

        name_match = re.search(
            r'name="([^"]+)"',
            header
        )

        type_match = re.search(
            r'type="([^"]+)"',
            header
        )

        parent_match = re.search(
            r'parent="([^"]*)"',
            header
        )

        script_match = re.search(
            r'^\s*script\s*=\s*ExtResource\("([^"]+)"\)',
            block,
            re.MULTILINE
        )

        script_path = None

        if script_match:
            resource_id = script_match.group(1)
            script_path = ext_resources.get(resource_id)

        node = {
            "name": name_match.group(1)
                if name_match else None,

            "type": type_match.group(1)
                if type_match else None,

            "parent": parent_match.group(1)
                if parent_match else None,

            "script": script_path
        }

        nodes.append(node)

    return {
        "file": str(path.relative_to(GODOT_PROJECT)),
        "resources": list(ext_resources.values()),
        "nodes": nodes
    }


def main():
    scene_files = list(GODOT_PROJECT.rglob("*.tscn"))

    scenes = []

    for path in scene_files:
        scenes.append(scan_scene(path))

    index = {
        "project": GODOT_PROJECT.name,
        "scenes": scenes
    }

    OUTPUT_FILE.write_text(
        json.dumps(index, indent=4),
        encoding="utf-8"
    )

    print(f"Indexed {len(scenes)} scenes.")
    print(f"Scene index saved to: {OUTPUT_FILE.absolute()}")


if __name__ == "__main__":
    main()