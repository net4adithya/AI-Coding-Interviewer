from datetime import datetime
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Tuple
from ..models.static_analysis import StaticAnalysis, AnalysisStatusEnum

class StaticAnalysisRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, db_obj: StaticAnalysis) -> StaticAnalysis:
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_by_id(self, analysis_id: int) -> Optional[StaticAnalysis]:
        return self.db.query(StaticAnalysis).filter(StaticAnalysis.id == analysis_id, StaticAnalysis.is_deleted == False).first()

    def get_by_submission_id(self, submission_id: int) -> Optional[StaticAnalysis]:
        return self.db.query(StaticAnalysis).filter(StaticAnalysis.submission_id == submission_id, StaticAnalysis.is_deleted == False).first()

    def list(self, *, skip: int = 0, limit: int = 20, filters: Optional[Dict[str, Any]] = None, sort_by: str = "created_at", order: str = "desc") -> Tuple[int, List[StaticAnalysis]]:
        query = self.db.query(StaticAnalysis).filter(StaticAnalysis.is_deleted == False)
        if filters:
            for attr, value in filters.items():
                if hasattr(StaticAnalysis, attr) and value is not None:
                    query = query.filter(getattr(StaticAnalysis, attr) == value)
        total = query.count()
        if hasattr(StaticAnalysis, sort_by):
            sort_col = getattr(StaticAnalysis, sort_by)
            if order.lower() == "desc":
                sort_col = sort_col.desc()
            else:
                sort_col = sort_col.asc()
            query = query.order_by(sort_col)
        items = query.offset(skip).limit(limit).all()
        return total, items

    def soft_delete(self, analysis_id: int) -> bool:
        obj = self.db.query(StaticAnalysis).filter(StaticAnalysis.id == analysis_id, StaticAnalysis.is_deleted == False).first()
        if obj:
            obj.is_deleted = True
            obj.deleted_at = datetime.utcnow()
            self.db.commit()
            return True
        return False
