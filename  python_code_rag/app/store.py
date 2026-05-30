import iris
from app.config import IRIS_HOST, IRIS_PORT, IRIS_NAMESPACE, IRIS_USERNAME, IRIS_PASSWORD

def get_connection():
    return iris.connect(IRIS_HOST, IRIS_PORT, IRIS_NAMESPACE, IRIS_USERNAME, IRIS_PASSWORD)


def ensure_table(conn, collection: str):
    cur = conn.cursor()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS RAG_{collection} (
            chunk_id    VARCHAR(40)   NOT NULL,
            file        VARCHAR(500),
            type        VARCHAR(20),
            name        VARCHAR(255),
            start_line  INTEGER,
            end_line    INTEGER,
            "module"    VARCHAR(500),
            text        LONGVARCHAR,
            embedding   VECTOR(DOUBLE, 1024)
        )
    """)

    try:
        cur.execute(f"""
            CREATE INDEX HNSWIdx_{collection}
            ON RAG_{collection} (embedding)
            AS HNSW(Distance='Cosine')
        """)
    except Exception:
        pass

    conn.commit()


def delete_collection(conn, collection: str):
    cur = conn.cursor()
    cur.execute(f"DELETE FROM RAG_{collection}")
    conn.commit()


def collection_exists(conn, collection: str) -> bool:
    cur = conn.cursor()
    cur.execute(f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'RAG_{collection}'")
    return cur.fetchone() is not None


def insert_chunks(conn, collection: str, chunks: list, vectors: list[list[float]]):
    cur = conn.cursor()
    sql = f"""
        INSERT INTO RAG_{collection}
        (chunk_id, file, type, name, start_line, end_line, "module", text, embedding)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, TO_VECTOR(?))
    """
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i:i+batch_size]
        batch_vectors = vectors[i:i+batch_size]
        params = []
        for chunk, vec in zip(batch_chunks, batch_vectors):
            params.append([
                chunk.id,
                chunk.file,
                chunk.type,
                chunk.name,
                chunk.start_line,
                chunk.end_line,
                chunk.module,
                chunk.text,
                str(vec),
            ])
        cur.executemany(sql, params)
    conn.commit()
