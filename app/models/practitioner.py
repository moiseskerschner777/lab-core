from sqlalchemy import Boolean, Column, String

from database import Base


class Practitioner(Base):
    __tablename__ = "labcore_practitioner"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    specialty = Column(String, nullable=False)
    council_type = Column(String, nullable=False)
    council_number = Column(String, nullable=False)
    council_state = Column(String, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
