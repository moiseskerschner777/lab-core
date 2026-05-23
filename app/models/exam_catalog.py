from sqlalchemy import Boolean, Column, Integer, String

from database import Base


class ExamCatalog(Base):
    __tablename__ = "labcore_exam_catalog"

    exam_code = Column(String, primary_key=True)
    exam_name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    can_perform = Column(Boolean, nullable=False)
    requires_support_lab = Column(Boolean, nullable=False)
    support_lab = Column(String, nullable=True)
    turnaround_hours = Column(Integer, nullable=False)
