import hashlib
from dataclasses import dataclass

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
