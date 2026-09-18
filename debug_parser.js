const fs = require("fs");
const Parser = require("tree-sitter");
const GDScript = require("tree-sitter-gdscript");

const parser = new Parser();
parser.setLanguage(GDScript);

const file =
    "C:/Users/berke/OneDrive/Desktop/silicon_frontier/Machines/Scripts/wafer_slicer.gd";

const source = fs.readFileSync(file, "utf8");

const tree = parser.parse(
    source,
    undefined,
    { bufferSize: 1024 * 1024 }
);

console.log(tree.rootNode.toString());