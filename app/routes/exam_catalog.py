from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models.exam_catalog import ExamCatalog
from schemas.exam_catalog import ExamCatalogResponse

router = APIRouter()


@router.get("/{exam_code}", response_model=ExamCatalogResponse)
def get_exam_by_code(exam_code: str, db: Session = Depends(get_db)):
    exam = db.query(ExamCatalog).filter(ExamCatalog.exam_code == exam_code).first()
    if exam is None:
        raise HTTPException(status_code=404, detail="Exam not found")
    return exam
