from pathlib import Path
import re
import json

GODOT_PROJECT = Path(r"C:\Users\berke\OneDrive\Desktop\silicon_frontier")

OUTPUT_FILE = Path("index.json")


def scan_gdscript(path: Path):
    content = path.read_text(encoding="utf-8", errors="ignore")

    class_match = re.search(
        r"^\s*class_name\s+(\w+)",
        content,
        re.MULTILINE
    )

    extends_match = re.search(
        r"^\s*extends\s+(.+)",
        content,
        re.MULTILINE
    )

    signals = re.findall(
        r"^\s*signal\s+(\w+)",
        content,
        re.MULTILINE
    )

    functions = re.findall(
        r"^\s*func\s+(\w+)",
        content,
        re.MULTILINE
    )

    # Detect preload/load references
    preloads = re.findall(
        r"(?:preload|load)\s*\(\s*[\"']([^\"']+)[\"']\s*\)",
        content
    )

    # Detect likely class references.
    # We look for classes used as constructors or static access.
    class_references = set()

    # Constructor-style usage:
    # Example: Inventory.new()
    #          Vector3(...)
    #          Label3D.new()
    for match in re.finditer(
        r"\b([A-Z][A-Za-z0-9_]*)\s*\.",
        content
    ):
        class_references.add(match.group(1))

    # Constructor/function-call usage:
    # Example: Vector3(...)
    #          Transform3D(...)
    for match in re.finditer(
        r"\b([A-Z][A-Za-z0-9_]*)\s*\(",
        content
    ):
        class_references.add(match.group(1))

    # Remove the script's own class name
    if class_match:
        class_references.discard(class_match.group(1))

    class_references = sorted(class_references)

    return {
        "file": str(path.relative_to(GODOT_PROJECT)),
        "class": class_match.group(1) if class_match else None,
        "extends": extends_match.group(1).strip() if extends_match else None,
        "signals": signals,
        "functions": functions,
        "preloads": preloads,
        "class_references": class_references,
    }


def main():
    gd_files = list(GODOT_PROJECT.rglob("*.gd"))

    scripts = []

    for path in gd_files:
        scripts.append(scan_gdscript(path))

    # ---------------------------------------------------------
    # Build class -> file lookup
    # ---------------------------------------------------------

    class_to_file = {}

    for script in scripts:
        class_name = script["class"]

        if class_name:
            class_to_file[class_name] = script["file"]

    # ---------------------------------------------------------
    # Resolve class relationships
    # ---------------------------------------------------------

    for script in scripts:
        relationships = []

        # Inheritance relationship
        parent_class = script["extends"]

        if parent_class in class_to_file:
            relationships.append({
                "type": "extends",
                "class": parent_class,
                "file": class_to_file[parent_class]
            })

        # Usage relationships
        for reference in script["class_references"]:
            if reference in class_to_file:
                relationships.append({
                    "type": "uses",
                    "class": reference,
                    "file": class_to_file[reference]
                })

        script["relationships"] = relationships

    # ---------------------------------------------------------
    # Save index
    # ---------------------------------------------------------

    index = {
        "project": GODOT_PROJECT.name,
        "scripts": scripts,
        "class_to_file": class_to_file
    }

    OUTPUT_FILE.write_text(
        json.dumps(index, indent=4),
        encoding="utf-8"
    )

    print(f"Indexed {len(scripts)} GDScript files.")
    print(f"Found {len(class_to_file)} named classes.")
    print(f"Index saved to: {OUTPUT_FILE.absolute()}")


if __name__ == "__main__":
    main()