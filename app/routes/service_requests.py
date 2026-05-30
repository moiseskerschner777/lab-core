from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.service_request import ServiceRequest
from schemas.service_request import ServiceRequestResponse

router = APIRouter()


@router.get("/{id}", response_model=ServiceRequestResponse)
def get_service_request(id: str, db: Session = Depends(get_db)):
    service_request = db.get(ServiceRequest, id)
    if service_request is None:
        raise HTTPException(status_code=404, detail="ServiceRequest not found")

    return service_request
