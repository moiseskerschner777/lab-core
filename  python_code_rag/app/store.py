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
