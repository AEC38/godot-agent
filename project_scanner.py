from pathlib import Path


GODOT_PROJECT = Path(r"C:\Users\berke\OneDrive\Desktop\silicon_frontier")


FILE_TYPES = {
    ".gd": "GDScript",
    ".tscn": "Scene",
    ".tres": "Resource",
    ".godot": "Godot project",
    ".svg": "SVG",
    ".png": "Image",
    ".jpg": "Image",
    ".jpeg": "Image",
}


def scan_project(project_path: Path):
    print(f"Project: {project_path}")
    print()

    if not project_path.exists():
        print("ERROR: Project directory does not exist.")
        return

    project_file = project_path / "project.godot"

    if project_file.exists():
        print("✓ Godot project detected")
    else:
        print("WARNING: project.godot not found")

    print()
    print("File summary:")
    print("-" * 40)

    counts = {}

    for path in project_path.rglob("*"):
        if not path.is_file():
            continue

        extension = path.suffix.lower()

        file_type = FILE_TYPES.get(extension, "Other")

        counts[file_type] = counts.get(file_type, 0) + 1

    for file_type, count in sorted(counts.items()):
        print(f"{file_type:20} {count}")

    print()
    print(f"Total files: {sum(counts.values())}")


if __name__ == "__main__":
    scan_project(GODOT_PROJECT)