from fastapi import FastAPI

from database import Base, engine
from models import exam_catalog, patient, practitioner, service_request, service_request_item
from routes.health import router as health_router

app = FastAPI(title="LabCore API", version="0.1.0")
app.include_router(health_router)


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
