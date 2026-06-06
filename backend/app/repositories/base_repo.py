"""
VendorBridge ERP – Base Repository
====================================
Generic CRUD repository that all domain repositories extend.
Implements the Repository pattern over SQLAlchemy sessions.
"""

from sqlalchemy.orm import Session


class BaseRepository:
    """
    Provides standard CRUD operations for any SQLAlchemy model.
    Subclasses set `model` to the target ORM class.

    Usage:
        class UserRepo(BaseRepository):
            model = User
    """

    model = None  # Override in subclass

    def __init__(self, db: Session):
        """
        Initialize with a SQLAlchemy session.

        Args:
            db: An active SQLAlchemy Session instance.
        """
        # TODO: Store the session reference for use by all methods.
        # self.db = db
        pass

    def get_by_id(self, entity_id: str):
        """
        Fetch a single record by its UUID primary key.

        Args:
            entity_id: UUID string of the record.

        Returns:
            Model instance or None.
        """
        # TODO: Implement query:
        #   1. Query self.model filtered by id == entity_id
        #   2. Also filter deleted_at IS NULL (soft-delete aware)
        #   3. Return .first()
        pass

    def get_all(self, page: int = 1, per_page: int = 20, filters: dict = None):
        """
        Fetch a paginated list of records.

        Args:
            page: Page number (1-indexed).
            per_page: Number of records per page.
            filters: Optional dict of column_name → value to filter by.

        Returns:
            Tuple of (list[Model], total_count).
        """
        # TODO: Implement paginated query:
        #   1. Build base query on self.model where deleted_at IS NULL
        #   2. Apply any filters from the dict (getattr on model columns)
        #   3. Get total count via .count()
        #   4. Apply .offset((page-1)*per_page).limit(per_page)
        #   5. Return (results, total_count)
        pass

    def create(self, entity):
        """
        Insert a new record.

        Args:
            entity: An instance of self.model (already populated).

        Returns:
            The persisted entity (with id set).
        """
        # TODO: Implement:
        #   1. self.db.add(entity)
        #   2. self.db.commit()
        #   3. self.db.refresh(entity)
        #   4. Return entity
        pass

    def update(self, entity):
        """
        Persist changes to an existing record.

        Args:
            entity: A detached or dirty model instance.

        Returns:
            The updated entity.
        """
        # TODO: Implement:
        #   1. self.db.merge(entity)
        #   2. self.db.commit()
        #   3. Return entity
        pass

    def soft_delete(self, entity_id: str):
        """
        Mark a record as deleted without physically removing it.

        Args:
            entity_id: UUID string of the record to soft-delete.

        Returns:
            True if the record was found and marked, False otherwise.
        """
        # TODO: Implement:
        #   1. Fetch entity via self.get_by_id(entity_id)
        #   2. If not found, return False
        #   3. Set entity.deleted_at = datetime.utcnow()
        #   4. Commit and return True
        pass

    def hard_delete(self, entity_id: str):
        """
        Permanently remove a record from the database.

        Args:
            entity_id: UUID string of the record to delete.

        Returns:
            True if found and deleted, False otherwise.
        """
        # TODO: Implement:
        #   1. Fetch entity
        #   2. self.db.delete(entity)
        #   3. self.db.commit()
        #   4. Return True / False
        pass

    def exists(self, entity_id: str) -> bool:
        """
        Check if a record with the given ID exists (and is not soft-deleted).

        Returns:
            Boolean.
        """
        # TODO: Implement with an efficient EXISTS subquery.
        pass
