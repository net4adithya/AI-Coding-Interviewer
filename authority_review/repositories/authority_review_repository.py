from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from ..models.authority_review import AuthorityReview

class AuthorityReviewRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, review: AuthorityReview) -> AuthorityReview:
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review

    def get_by_id(self, review_id: int) -> Optional[AuthorityReview]:
        return (
            self.db.query(AuthorityReview)
            .filter(AuthorityReview.id == review_id, AuthorityReview.is_deleted == False)
            .first()
        )

    def get_by_submission_id(self, submission_id: int) -> Optional[AuthorityReview]:
        return (
            self.db.query(AuthorityReview)
            .filter(AuthorityReview.submission_id == submission_id, AuthorityReview.is_deleted == False)
            .first()
        )

    def update(self, review: AuthorityReview) -> AuthorityReview:
        review.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(review)
        return review

    def list(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> Tuple[int, List[AuthorityReview]]:
        query = self.db.query(AuthorityReview).filter(AuthorityReview.is_deleted == False)
        if filters:
            for attr, value in filters.items():
                if hasattr(AuthorityReview, attr) and value is not None:
                    query = query.filter(getattr(AuthorityReview, attr) == value)

        total = query.count()
        if hasattr(AuthorityReview, sort_by):
            sort_col = getattr(AuthorityReview, sort_by)
            if order.lower() == "desc":
                sort_col = sort_col.desc()
            else:
                sort_col = sort_col.asc()
            query = query.order_by(sort_col)

        items = query.offset(skip).limit(limit).all()
        return total, items

    def soft_delete(self, review_id: int) -> bool:
        obj = self.get_by_id(review_id)
        if obj:
            obj.is_deleted = True
            obj.deleted_at = datetime.utcnow()
            self.db.commit()
            return True
        return False
