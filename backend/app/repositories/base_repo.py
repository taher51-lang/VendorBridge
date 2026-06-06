"""
VendorBridge ERP – Base Repository
====================================
Generic CRUD repository that all domain repositories extend.
"""

from datetime import datetime
from sqlalchemy.orm import Session


class BaseRepository:
    """
    Provides standard CRUD operations for any SQLAlchemy model.
    Subclasses set `model` to the target ORM class.
    """

    model = None

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, entity_id: str):
        return (
            self.db.query(self.model)
            .filter(
                self.model.id == entity_id,
                self.model.deleted_at.is_(None),
            )
            .first()
        )

    def get_all(self, page: int = 1, per_page: int = 20, filters: dict = None):
        query = self.db.query(self.model).filter(self.model.deleted_at.is_(None))
        if filters:
            for column_name, value in filters.items():
                column = getattr(self.model, column_name, None)
                if column is not None:
                    query = query.filter(column == value)
        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        return results, total

    def create(self, entity):
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity):
        self.db.merge(entity)
        self.db.commit()
        return entity

    def soft_delete(self, entity_id: str) -> bool:
        entity = self.get_by_id(entity_id)
        if not entity:
            return False
        entity.deleted_at = datetime.utcnow()
        self.db.commit()
        return True

    def hard_delete(self, entity_id: str) -> bool:
        entity = self.get_by_id(entity_id)
        if not entity:
            return False
        self.db.delete(entity)
        self.db.commit()
        return True

    def exists(self, entity_id: str) -> bool:
        return self.get_by_id(entity_id) is not None
