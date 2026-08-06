from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from ai_review.models.ai_review import AIReview

class AIReviewRepository:
    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def _get_db(self, db: Optional[Session] = None) -> Session:
        session = db or self.db
        if session is None:
            raise ValueError("Database session must be provided.")
        return session

    def create(self, db_or_review: Session | AIReview, review: Optional[AIReview] = None) -> AIReview:
        if isinstance(db_or_review, Session):
            db = db_or_review
            obj = review
        else:
            db = self._get_db()
            obj = db_or_review

        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db_or_review: Session | AIReview, review: Optional[AIReview] = None) -> AIReview:
        if isinstance(db_or_review, Session):
            db = db_or_review
            obj = review
        else:
            db = self._get_db()
            obj = db_or_review

        obj.updated_at = datetime.utcnow()
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def get_by_submission_id(self, db_or_id: Session | int, submission_id: Optional[int] = None) -> Optional[AIReview]:
        if isinstance(db_or_id, Session):
            db = db_or_id
            sub_id = submission_id
        else:
            db = self._get_db()
            sub_id = db_or_id
        return db.query(AIReview).filter(AIReview.submission_id == sub_id, AIReview.is_deleted == False).first()

    def get_by_id(self, db_or_id: Session | int, review_id: Optional[int] = None) -> Optional[AIReview]:
        if isinstance(db_or_id, Session):
            db = db_or_id
            r_id = review_id
        else:
            db = self._get_db()
            r_id = db_or_id
        return db.query(AIReview).filter(AIReview.id == r_id, AIReview.is_deleted == False).first()

    def list(self, db: Optional[Session] = None, skip: int = 0, limit: int = 20, filters: dict = None, sort_by: str = 'created_at', order: str = 'desc') -> Tuple[int, List[AIReview]]:
        session = db or self._get_db()
        query = session.query(AIReview).filter(AIReview.is_deleted == False)
        if filters:
            for attr, value in filters.items():
                if hasattr(AIReview, attr) and value is not None:
                    query = query.filter(getattr(AIReview, attr) == value)
        total = query.count()
        sort_col = getattr(AIReview, sort_by, AIReview.created_at)
        if order.lower() == 'desc':
            sort_col = sort_col.desc()
        else:
            sort_col = sort_col.asc()
        items = query.order_by(sort_col).offset(skip).limit(limit).all()
        return total, items

    def soft_delete(self, db_or_id: Session | int, review_id: Optional[int] = None) -> None:
        if isinstance(db_or_id, Session):
            db = db_or_id
            r_id = review_id
        else:
            db = self._get_db()
            r_id = db_or_id

        review = self.get_by_id(db, r_id)
        if review:
            review.is_deleted = True
            review.deleted_at = datetime.utcnow()
            db.commit()
