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
