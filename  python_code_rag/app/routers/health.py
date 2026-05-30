import httpx
from fastapi import APIRouter
from app import config

router = APIRouter()


@router.get("/health")
async def health():
    status = "ok"
    iris_status = "ok"
    ollama_status = "ok"

    try:
        import intersystems_irispython.intersystems.iris as iris
        conn = iris.connect(config.IRIS_HOST, config.IRIS_PORT, config.IRIS_NAMESPACE,
                            config.IRIS_USERNAME, config.IRIS_PASSWORD)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        conn.close()
    except Exception:
        iris_status = "unreachable"
        status = "degraded"

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{config.OLLAMA_URL}/api/tags", timeout=3.0)
            resp.raise_for_status()
    except Exception:
        ollama_status = "unreachable"
        status = "degraded"

    if status == "degraded":
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "iris": iris_status, "ollama": ollama_status}
        )

    return {"status": "ok", "iris": iris_status, "ollama": ollama_status}
