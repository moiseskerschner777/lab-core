from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models.service_request import ServiceRequest
from models.service_request_item import ServiceRequestItem
from schemas.service_request import ServiceRequestCreate, ServiceRequestResponse

router = APIRouter()


@router.get("/{id}", response_model=ServiceRequestResponse)
def get_service_request(id: str, db: Session = Depends(get_db)):
    service_request = db.get(ServiceRequest, id)
    if service_request is None:
        raise HTTPException(status_code=404, detail="ServiceRequest not found")

    return service_request


@router.post("", response_model=ServiceRequestResponse, status_code=status.HTTP_201_CREATED)
def create_service_request(body: ServiceRequestCreate, db: Session = Depends(get_db)):
    max_code = db.query(func.max(ServiceRequest.code)).scalar()
    if max_code:
        next_number = int(max_code.split("-")[1]) + 1
    else:
        next_number = 1
    code = f"OS-{next_number:05d}"

    sr = ServiceRequest(
        id=str(uuid4()),
        code=code,
        status="ACTIVE",
        priority=body.priority,
        patient_id=body.patient_id,
        practitioner_id=body.practitioner_id,
        created_at=datetime.utcnow(),
        notes=body.notes,
    )
    db.add(sr)

    for item_data in body.items:
        item = ServiceRequestItem(
            id=str(uuid4()),
            service_request_id=sr.id,
            exam_code=item_data["exam_code"],
            exam_name=item_data["exam_name"],
            status="PENDING",
        )
        db.add(item)

    db.commit()
    db.refresh(sr)

    return sr


@router.put("/{id}/cancel", response_model=ServiceRequestResponse)
def cancel_service_request(id: str, db: Session = Depends(get_db)):
    service_request = db.get(ServiceRequest, id)
    if service_request is None:
        raise HTTPException(status_code=404, detail="ServiceRequest not found")

    if service_request.status == "CANCELLED":
        raise HTTPException(status_code=422, detail="ServiceRequest is already cancelled")

    service_request.status = "CANCELLED"
    service_request.cancelled_at = datetime.utcnow()

    for item in service_request.items:
        item.status = "CANCELLED"

    db.commit()
    db.refresh(service_request)

    return service_request
