import hashlib
from dataclasses import dataclass
from pathlib import Path

import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Tree

PY_LANGUAGE = Language(tspython.language())


def parse_file(path: Path) -> Tree:
    parser = Parser(PY_LANGUAGE)
    source = path.read_bytes()
    return parser.parse(source)

@dataclass
class Chunk:
    id: str
    file: str
    type: str        # "function" | "class" | "module" | "imports"
    name: str
    start_line: int
    end_line: int
    text: str
    module: str

def chunk_id(file: str, type: str, name: str) -> str:
    return hashlib.sha1(f"{file}::{type}::{name}".encode()).hexdigest()


def _walk_collect(node, node_type):
    result = []

    def walk(n):
        if n.type == node_type:
            result.append(n)
        for child in n.children:
            walk(child)

    walk(node)
    return result


def chunk_file(path: Path, root: Path) -> list:
    source_bytes = path.read_bytes()
    tree = parse_file(path)
    rel_path = str(path.relative_to(root))
    module_name = rel_path.replace("/", ".").replace("\\", ".").removesuffix(".py")

    chunks: list = []

    for node in _walk_collect(tree.root_node, "function_definition"):
        name_node = node.child_by_field_name("name")
        name = name_node.text.decode() if name_node else "<unknown>"
        text = source_bytes[node.start_byte : node.end_byte].decode()
        chunks.append(Chunk(
            id=chunk_id(rel_path, "function", name),
            file=rel_path,
            type="function",
            name=name,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            text=text,
            module=module_name,
        ))

    return chunks
