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
    stem = path.stem

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

    for node in _walk_collect(tree.root_node, "class_definition"):
        name_node = node.child_by_field_name("name")
        name = name_node.text.decode() if name_node else "<unknown>"
        body = node.child_by_field_name("body")
        end_node = node
        if body and body.named_child_count > 0:
            first = body.named_children[0]
            if first.type == "expression_statement":
                end_node = first
        text = source_bytes[node.start_byte : end_node.end_byte].decode()
        chunks.append(Chunk(
            id=chunk_id(rel_path, "class", name),
            file=rel_path,
            type="class",
            name=name,
            start_line=node.start_point[0] + 1,
            end_line=end_node.end_point[0] + 1,
            text=text,
            module=module_name,
        ))

    import_texts = []
    import_end = 0
    for child in tree.root_node.named_children:
        if child.type in ("import_statement", "import_from_statement"):
            import_texts.append(source_bytes[child.start_byte : child.end_byte].decode())
            import_end = child.end_point[0] + 1
    if import_texts:
        first_import = next(c for c in tree.root_node.named_children if c.type in ("import_statement", "import_from_statement"))
        chunks.append(Chunk(
            id=chunk_id(rel_path, "imports", stem),
            file=rel_path,
            type="imports",
            name=stem,
            start_line=first_import.start_point[0] + 1,
            end_line=import_end,
            text="\n".join(import_texts),
            module=module_name,
        ))

    source_str = source_bytes.decode()
    lines = source_str.splitlines()
    module_text = "\n".join(lines[:120])
    if len(lines) > 120:
        module_text += "\n# ... truncated"
    chunks.append(Chunk(
        id=chunk_id(rel_path, "module", stem),
        file=rel_path,
        type="module",
        name=stem,
        start_line=1,
        end_line=min(len(lines), 120),
        text=module_text,
        module=module_name,
    ))

    return chunks


def chunk_codebase(root: Path) -> list:
    skip_dirs = {"__pycache__", ".venv", ".git", "node_modules"}
    all_chunks: list = []
    for py_file in sorted(root.rglob("*.py")):
        rel = py_file.relative_to(root)
        if any(p in skip_dirs for p in rel.parts[:-1]):
            continue
        all_chunks.extend(chunk_file(py_file, root))
    return all_chunks
