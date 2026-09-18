const fs = require("fs");
const Parser = require("tree-sitter");
const GDScript = require("tree-sitter-gdscript");

const parser = new Parser();
parser.setLanguage(GDScript);

const file = String.raw`C:\Users\berke\OneDrive\Desktop\silicon_frontier\Machines\Scripts\wafer_slicer.gd`;

const source = fs.readFileSync(file, "utf8");
const tree = parser.parse(source);


function getNodeText(node) {
    return source.slice(node.startIndex, node.endIndex);
}


function inspectNode(node, depth = 0) {

    if (node.type === "call" || node.type === "attribute") {

        const indent = "  ".repeat(depth);

        console.log(
            `${indent}${node.type}: ${getNodeText(node)}`
        );

        console.log(
            `${indent}children:`
        );

        for (const child of node.namedChildren) {
            console.log(
                `${indent}  - ${child.type}: ${getNodeText(child)}`
            );
        }

        console.log();
    }

    for (const child of node.namedChildren) {
        inspectNode(child, depth + 1);
    }
}


inspectNode(tree.rootNode);