from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from database import Base


class ServiceRequest(Base):
    __tablename__ = "labcore_service_request"

    id = Column(String, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    status = Column(String, default="active", nullable=False)
    priority = Column(String, default="routine", nullable=False)
    patient_id = Column(String, ForeignKey("labcore_patient.id"), nullable=False)
    practitioner_id = Column(
        String, ForeignKey("labcore_practitioner.id"), nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    cancelled_at = Column(DateTime, nullable=True)
    notes = Column(String, nullable=True)

    patient = relationship("Patient")
    practitioner = relationship("Practitioner")
