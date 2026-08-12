# python_backend/app/editor/repositories/draft_version_repository.py
"""Repository for DraftVersion CRUD operations."""

from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.editor.models.editor import DraftVersion


class DraftVersionRepository:
    """Database operations for DraftVersion records (immutable history)."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_latest_version_number(self, draft_id: int) -> int:
        """Return the highest version_number for the given draft, or 0 if none exist."""
        result = (
            self.db.query(DraftVersion.version_number)
            .filter(DraftVersion.draft_id == draft_id)
            .order_by(DraftVersion.version_number.desc())
            .first()
        )
        return result[0] if result else 0

    def get_by_id(self, version_id: int) -> Optional[DraftVersion]:
        return self.db.query(DraftVersion).filter(DraftVersion.id == version_id).first()

    def get_latest(self, draft_id: int) -> Optional[DraftVersion]:
        """Return the most recent DraftVersion for the draft."""
        return (
            self.db.query(DraftVersion)
            .filter(DraftVersion.draft_id == draft_id)
            .order_by(DraftVersion.version_number.desc())
            .first()
        )

    def list_versions(
        self,
        draft_id: int,
        *,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[int, List[DraftVersion]]:
        """Return paginated list of versions for a draft (metadata only – no code)."""
        page = max(page, 1)
        size = min(max(size, 1), 100)
        skip = (page - 1) * size

        query = (
            self.db.query(DraftVersion)
            .filter(DraftVersion.draft_id == draft_id)
            .order_by(DraftVersion.version_number.desc())
        )
        total = query.count()
        items = query.offset(skip).limit(size).all()
        return total, items

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create_version(
        self,
        *,
        draft_id: int,
        code: str,
        language: str,
    ) -> DraftVersion:
        """Atomically append a new immutable version row.

        The version_number is the current maximum + 1 for this draft.
        The UNIQUE(draft_id, version_number) constraint in the database
        guarantees safety even for concurrent requests.
        """
        next_number = self.get_latest_version_number(draft_id) + 1
        version = DraftVersion(
            draft_id=draft_id,
            version_number=next_number,
            code=code,
            language=language.lower(),
            created_at=datetime.utcnow(),
        )
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)
        return version
