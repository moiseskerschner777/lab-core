# design.md — python-code-rag

## File Structure

```
python_code_rag/
├── .ai/
│   └── specs/
│       ├── spec.md
│       ├── design.md
│       └── tasks/
│           ├── 1.md  →  6.md
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, router registration, lifespan
│   ├── config.py            # env-overridable constants
│   ├── chunker.py           # tree-sitter AST walker → List[Chunk]
│   ├── embedder.py          # Ollama embedding wrapper
│   ├── store.py             # IRIS vector store wrapper
│   ├── retriever.py         # embed query + search + map to response
│   └── routers/
│       ├── __init__.py
│       ├── index.py         # POST /index
│       ├── search.py        # POST /search
│       ├── collections.py   # GET /collections
│       └── health.py        # GET /health
├── docker-compose.yml       # standalone: app + ollama, IRIS via external network
├── Dockerfile
├── pyproject.toml
└── README.md
```

---

## Docker Compose Architecture

```
Host machine
├── ollama (native, nohup, 0.0.0.0:11434, GPU RTX 5080)
│
├── docker-compose (root / lab-core)
│   └── iris  (:1972, :52773)  →  lab-core_default network
│
└── python_code_rag/docker-compose.yml
    └── app (:8001)
        ├── → host.docker.internal:11434  (Ollama, via extra_hosts)
        └── → iris:1972                  (IRIS, via lab-core_default)

External MCP / Cursor → http://localhost:8001
```

### `docker-compose.yml`

```yaml
services:
  app:
    build: .
    ports:
      - "8001:8001"
    extra_hosts:
      - "host.docker.internal:host-gateway"
    environment:
      IRIS_HOST: iris
      IRIS_PORT: 1972
      IRIS_NAMESPACE: USER
      IRIS_USERNAME: _SYSTEM
      IRIS_PASSWORD: SYS
      OLLAMA_URL: http://host.docker.internal:11434
      EMBED_PROVIDER: ollama
      EMBED_MODEL: snowflake-arctic-embed2
      EMBED_DIM: 1024
      EMBED_PARALLELISM: 16
      OLLAMA_NUM_CTX: 8192
    volumes:
      - ../projectA:/workspace/projectA:ro
      - ../projectB:/workspace/projectB:ro
      - ../projectC:/workspace/projectC:ro
    networks:
      - default
      - lab-core_default

networks:
  lab-core_default:
    external: true
```

### `Dockerfile`

```dockerfile
FROM python:3.12-slim
WORKDIR /python-code-rag
COPY pyproject.toml .
RUN pip install -e .
COPY app/ app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
```

---

## IRIS Vector Search Design

### Table per collection

Each indexed directory gets its own SQL table in IRIS. Table name: `RAG_<collection>` (e.g. directory `projectA` → table `RAG_projectA`).

Table schema — `ensure_table` runs both statements on every call (idempotent):
```sql
CREATE TABLE IF NOT EXISTS RAG_<collection> (
    chunk_id    VARCHAR(40)   NOT NULL,
    file        VARCHAR(500),
    type        VARCHAR(20),
    name        VARCHAR(255),
    start_line  INTEGER,
    end_line    INTEGER,
    module      VARCHAR(500),
    text        LONGVARCHAR,
    embedding   VECTOR(DOUBLE, 1024)
)
```

Immediately after table creation, create the HNSW ANN index (idempotent — IRIS silently ignores if it already exists):
```sql
CREATE INDEX IF NOT EXISTS HNSWIdx_<collection>
ON RAG_<collection> (embedding)
AS HNSW(Distance='Cosine')
```

The HNSW index activates automatically on queries that combine `TOP`, `ORDER BY ... DESC`, and `VECTOR_COSINE` — no query changes needed. Without it, every search does a full table scan.

Vector similarity search — uses `VECTOR_COSINE` (implicitly normalizes vectors, correct for text embeddings):
```sql
SELECT TOP ? chunk_id, file, type, name, start_line, end_line, module, text,
       VECTOR_COSINE(embedding, TO_VECTOR(?)) AS score
FROM RAG_<collection>
ORDER BY score DESC
```

Note: `TO_VECTOR(?)` expects the vector passed as a Python `str(list)` — e.g. `"[0.1, 0.2, ...]"`. `str(vector_list)` in Python produces exactly this format.

### Collection naming

`collection_name(path: str) -> str`: `Path(path).name` lowercased, non-alphanumeric replaced with `_`.
Examples: `projectA` → `projecta`, `my-service` → `my_service`.

### List collections

Query `INFORMATION_SCHEMA.TABLES` filtering by `TABLE_NAME LIKE 'RAG_%'`. Strip the `RAG_` prefix from each result.

### Re-index (idempotent)

`DELETE FROM RAG_<collection>` before re-inserting. Clean slate per index run — simpler than upsert-by-ID with IRIS SQL.

---

## API Contracts

### POST /index

Request:
```json
{ "path": "/workspace/projectA" }
```

Response `200`:
```json
{
  "collection": "projecta",
  "chunks_indexed": 142,
  "status": "ok"
}
```

Response `400` — path not found:
```json
{ "detail": "Path '/workspace/projectA' not found" }
```

### POST /search

Request:
```json
{
  "collection": "projecta",
  "query": "how is authentication handled",
  "top_k": 8
}
```

`top_k` optional, defaults to `config.SEARCH_TOP_K`.

Response `200`:
```json
{
  "collection": "projecta",
  "query": "how is authentication handled",
  "results": [
    {
      "score": 0.91,
      "file": "src/auth/handler.py",
      "type": "function",
      "name": "authenticate_user",
      "start_line": 14,
      "end_line": 38,
      "module": "src.auth.handler",
      "text": "def authenticate_user(token: str) -> User:\n    ..."
    }
  ]
}
```

Response `404` — collection not found:
```json
{ "detail": "Collection 'projecta' not found" }
```

### GET /collections

Response `200`:
```json
{
  "collections": ["projecta", "projectb", "projectc"]
}
```

### GET /health

Response `200`:
```json
{ "status": "ok", "iris": "ok", "ollama": "ok" }
```

Response `503`:
```json
{ "status": "degraded", "iris": "unreachable", "ollama": "ok" }
```

---

## Component Contracts

### `Chunk` (dataclass in `chunker.py`)

```python
@dataclass
class Chunk:
    id: str           # sha1(f"{relative_file}::{type}::{name}")
    file: str         # relative path from codebase root
    type: str         # "function" | "class" | "module" | "imports"
    name: str
    start_line: int
    end_line: int
    text: str
    module: str       # dot-separated module path
```

### `chunker.py`

- `chunk_file(path: Path, root: Path) -> List[Chunk]`
- `chunk_codebase(root: Path) -> List[Chunk]` — skips `__pycache__`, `.venv`, `.git`, `node_modules`

Chunk types: `function_definition`, `class_definition` (header + docstring only), imports (one per file), module (full file capped at 120 lines).

Chunk ID: `sha1(f"{relative_file}::{type}::{name}").hexdigest()`

### `embedder.py`

Public API — one function, rest of the codebase never imports anything else from this module:

```python
def embed(texts: List[str]) -> List[List[float]]: ...
```

Internally dispatches to the active provider based on `config.EMBED_PROVIDER`:

```
EMBED_PROVIDER=ollama   →  _OllamaEmbedder   (default)
EMBED_PROVIDER=openai   →  _OpenAIEmbedder   (placeholder, not implemented)
```

#### `_OllamaEmbedder`

Calls Ollama `/api/embed` (batch endpoint) via `httpx`. Splits input into batches of `config.EMBED_BATCH_SIZE` (100) and sends up to `config.EMBED_PARALLELISM` (16) concurrent requests using `asyncio.gather` + `httpx.AsyncClient`.

Default model: `snowflake-arctic-embed2` (1024 dims). Each request body:
```json
{
  "model": "snowflake-arctic-embed2",
  "input": ["text1", "text2", ...],
  "options": { "num_ctx": 8192 }
}
```

Response field is `embeddings` (list of vectors). Read timeout: 180s per batch.

#### `_OpenAIEmbedder` (placeholder)

```python
# NOT IMPLEMENTED — placeholder for future work
# Switch by setting EMBED_PROVIDER=openai + OPENAI_API_KEY=sk-...
# Expected model: text-embedding-3-small (1536 dims) or text-embedding-3-large (3072 dims)
# Remember to also update EMBED_DIM to match the chosen model
def _openai_embed(texts: List[str]) -> List[List[float]]:
    raise NotImplementedError("OpenAI provider not yet implemented")
```

#### Provider dispatch pattern

```python
# embedder.py
import os
from app import config

def embed(texts: list[str]) -> list[list[float]]:
    provider = config.EMBED_PROVIDER
    if provider == "ollama":
        return _ollama_embed(texts)
    elif provider == "openai":
        return _openai_embed(texts)
    else:
        raise ValueError(f"Unknown EMBED_PROVIDER: {provider!r}. Use 'ollama' or 'openai'.")
```

### `store.py`

```python
def get_connection() -> iris_connection          # intersystems_irispython connection
def ensure_table(conn, collection: str)          # CREATE TABLE IF NOT EXISTS + HNSW index
def delete_collection(conn, collection: str)     # DELETE FROM RAG_<collection>
def insert_chunks(conn, collection: str, chunks: List[Chunk], vectors: List[List[float]])
def search(conn, collection: str, query_vec: List[float], top_k: int) -> List[dict]
def list_collections(conn) -> List[str]          # query INFORMATION_SCHEMA
def collection_exists(conn, collection: str) -> bool
```

### `retriever.py`

`retrieve(query: str, collection: str, top_k: int) -> List[dict]`

1. `embed([query])[0]` → vector
2. `store.search(conn, collection, vector, top_k)`
3. Return list of dicts with all chunk fields + `score`

### `config.py`

```python
# ── IRIS ─────────────────────────────────────────────────────────────────────
IRIS_HOST         = os.getenv("IRIS_HOST",         "iris")
IRIS_PORT         = int(os.getenv("IRIS_PORT",     "1972"))
IRIS_NAMESPACE    = os.getenv("IRIS_NAMESPACE",    "USER")
IRIS_USERNAME     = os.getenv("IRIS_USERNAME",     "_SYSTEM")
IRIS_PASSWORD     = os.getenv("IRIS_PASSWORD",     "SYS")

# ── Embedding provider ────────────────────────────────────────────────────────
# "ollama" (default) or "openai"
EMBED_PROVIDER    = os.getenv("EMBED_PROVIDER",    "ollama")
EMBED_DIM         = int(os.getenv("EMBED_DIM",     "1024"))
SEARCH_TOP_K      = int(os.getenv("SEARCH_TOP_K",  "8"))

# ── Ollama ────────────────────────────────────────────────────────────────────
OLLAMA_URL        = os.getenv("OLLAMA_URL",        "http://host.docker.internal:11434")
EMBED_MODEL       = os.getenv("EMBED_MODEL",       "snowflake-arctic-embed2")
EMBED_BATCH_SIZE  = int(os.getenv("EMBED_BATCH_SIZE",  "100"))
EMBED_PARALLELISM = int(os.getenv("EMBED_PARALLELISM", "16"))
OLLAMA_NUM_CTX    = int(os.getenv("OLLAMA_NUM_CTX",    "8192"))

# ── OpenAI (placeholder — set EMBED_PROVIDER=openai to activate) ─────────────
# EMBED_DIM must match the chosen model:
#   text-embedding-3-small → 1536
#   text-embedding-3-large → 3072
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY",    "")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
```

---

## Key Decisions

1. **Table per collection**: each directory → its own `RAG_<name>` table. Clean isolation, easy to drop/re-index one project without touching others.
2. **Delete + re-insert on re-index**: simpler than upsert-by-ID in IRIS SQL. Re-indexing is a full replace — acceptable for a dev tool.
3. **IRIS native vector search**: uses `VECTOR(DOUBLE, 1024)` column type and `VECTOR_COSINE` for similarity — no Qdrant dependency.
4. **`VECTOR_COSINE` over `VECTOR_DOT_PRODUCT`**: cosine implicitly normalizes vectors — correct for text embeddings where magnitude is irrelevant. No need to pre-normalize before insert.
5. **HNSW index on every collection**: created immediately after `CREATE TABLE`. Activates automatically on `TOP + ORDER BY DESC + VECTOR_COSINE` queries. Without it, every search does a full table scan — unusable on large codebases.
6. **Provider strategy pattern in `embedder.py`**: `EMBED_PROVIDER=ollama|openai` dispatches to the right implementation. The rest of the codebase calls only `embed()` — zero changes needed to swap providers. OpenAI is a placeholder today; filling it in later requires touching only `embedder.py` and `config.py`.
7. **Ollama native on host (not containerized)**: runs with `nohup ollama serve`, bind `0.0.0.0:11434`. The `app` container reaches it via `host.docker.internal:11434` using `extra_hosts: host-gateway`. No Ollama container — nothing to pull or manage in compose.
8. **External network `lab-core_default`**: app reaches IRIS by its service name `iris` without touching the root compose.
9. **Port 8001**: avoids conflict with `labcore` on 8000.
10. **No chat endpoint**: retrieval only — the MCP handles LLM interaction.
