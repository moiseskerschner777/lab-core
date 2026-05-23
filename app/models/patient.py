from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, String

from database import Base


class Patient(Base):
    __tablename__ = "labcore_patient"

    id = Column(String, primary_key=True)
    name_family = Column(String, nullable=False)
    name_given = Column(String, nullable=False)
    birth_date = Column(Date, nullable=False)
    gender = Column(String, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
