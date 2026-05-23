from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import Base, engine
from models import exam_catalog, patient, practitioner, service_request, service_request_item
from routes.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="LabCore API", version="0.1.0", lifespan=lifespan)
app.include_router(health_router)
