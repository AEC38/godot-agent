from pathlib import Path
import json
import subprocess

GODOT_PROJECT = Path(r"C:\Users\berke\OneDrive\Desktop\silicon_frontier")
OUTPUT_FILE = Path("index.json")


NODE_PARSER = r"""
const fs = require("fs");
const Parser = require("tree-sitter");
const GDScript = require("tree-sitter-gdscript");

const file = process.argv[2];

const source = fs.readFileSync(file, "utf8");

const parser = new Parser();
parser.setLanguage(GDScript);

const tree = parser.parse(
    source,
    undefined,
    { bufferSize: 1024 * 1024 }
);

function getText(node) {
    return source.slice(node.startIndex, node.endIndex);
}

function walk(node, result) {

    if (node.type === "extends_statement") {
        const typeNode = node.childForFieldName("type");

        if (typeNode) {
            result.extends = getText(typeNode);
        }
    }

    if (node.type === "class_definition") {
        const nameNode = node.childForFieldName("name");

        if (nameNode) {
            result.class = getText(nameNode);
        }
    }

    if (node.type === "function_definition") {
        const nameNode = node.childForFieldName("name");

        if (nameNode) {
            result.functions.push(getText(nameNode));
        }
    }

    if (node.type === "variable_statement") {
        const nameNode = node.childForFieldName("name");

        if (nameNode) {
            result.variables.push(getText(nameNode));
        }
    }

    if (node.type === "call") {
        const functionNode = node.namedChildren[0];

        if (functionNode) {
            result.calls.push({
                name: getText(functionNode),
                type: functionNode.type
            });
        }
    }

    if (
        node.type === "attribute" &&
        node.namedChildren.length >= 2
    ) {
        const objectNode = node.namedChildren[0];
        const memberNode = node.namedChildren[1];

        result.attributes.push({
            object: getText(objectNode),
            member: getText(memberNode)
        });
    }

    if (node.type === "preload" || node.type === "load") {
        result.loads.push(getText(node));
    }

    for (const child of node.namedChildren) {
        walk(child, result);
    }
}

const result = {
    class: null,
    extends: null,
    functions: [],
    variables: [],
    calls: [],
    attributes: [],
    loads: []
};

walk(tree.rootNode, result);

console.log(JSON.stringify(result));
"""


def parse_gdscript(path: Path):
    temp_file = Path("_ast_parser.js")

    temp_file.write_text(
        NODE_PARSER,
        encoding="utf-8"
    )

    try:
        completed = subprocess.run(
            ["node", str(temp_file), str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True
        )

        return json.loads(completed.stdout)

    finally:
        if temp_file.exists():
            temp_file.unlink()


def build_class_references(parsed):
    references = set()

    for attribute in parsed["attributes"]:
        receiver = attribute["object"]

        if receiver and receiver[0].isupper():
            references.add(receiver)

    for call in parsed["calls"]:
        name = call["name"]

        if name and name[0].isupper():
            references.add(name)

    return sorted(references)


def scan_gdscript(path: Path):
    parsed = parse_gdscript(path)

    class_name = parsed["class"]

    class_references = build_class_references(parsed)

    return {
        "file": str(path.relative_to(GODOT_PROJECT)),
        "class": class_name,
        "extends": parsed["extends"],
        "signals": [],
        "functions": parsed["functions"],
        "variables": parsed["variables"],
        "preloads": [],
        "class_references": class_references,
        "calls": parsed["calls"],
        "attributes": parsed["attributes"],
        "relationships": []
    }


def main():

    gd_files = list(GODOT_PROJECT.rglob("*.gd"))

    scripts = []

    for path in gd_files:

        try:
            result = scan_gdscript(path)
            scripts.append(result)

        except Exception as error:
            print(f"Failed to parse {path}: {error}")

    class_to_file = {}

    for script in scripts:

        class_name = script["class"]

        if class_name:
            class_to_file[class_name] = script["file"]

    for script in scripts:

        relationships = []

        parent_class = script["extends"]

        if parent_class in class_to_file:

            relationships.append({
                "type": "extends",
                "class": parent_class,
                "file": class_to_file[parent_class]
            })

        for reference in script["class_references"]:

            if reference in class_to_file:

                relationships.append({
                    "type": "uses",
                    "class": reference,
                    "file": class_to_file[reference]
                })

        script["relationships"] = relationships

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