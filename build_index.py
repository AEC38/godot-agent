from pathlib import Path
import json

SCRIPT_INDEX = Path("index.json")
SCENE_INDEX = Path("scene_index.json")
OUTPUT_FILE = Path("project_index.json")


def main():

    with SCRIPT_INDEX.open("r", encoding="utf-8") as f:
        script_index = json.load(f)

    with SCENE_INDEX.open("r", encoding="utf-8") as f:
        scene_index = json.load(f)

    project_index = {
        "project": script_index["project"],
        "scripts": script_index["scripts"],
        "scenes": scene_index["scenes"],
        "class_to_file": script_index["class_to_file"]
    }

    OUTPUT_FILE.write_text(
        json.dumps(project_index, indent=4),
        encoding="utf-8"
    )

    print("Project index created.")
    print(f"Scripts: {len(project_index['scripts'])}")
    print(f"Scenes: {len(project_index['scenes'])}")
    print(f"Classes: {len(project_index['class_to_file'])}")
    print(f"Saved to: {OUTPUT_FILE.absolute()}")


if __name__ == "__main__":
    main()