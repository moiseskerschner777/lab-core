from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import health

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("python-code-rag started")
    yield

app = FastAPI(title="python-code-rag", lifespan=lifespan)
app.include_router(health.router)
