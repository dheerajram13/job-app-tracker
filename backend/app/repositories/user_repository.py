"""
User Repository Implementation
Implements Repository Pattern for User entity data access
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.interfaces.repository_interface import IUserRepository
from app.models.user import User
from app.exceptions import DatabaseError
import logging

logger = logging.getLogger(__name__)


class UserRepository(IUserRepository):
    """
    Concrete implementation of User Repository

    Handles all database operations for User entities
    """

    def __init__(self, db: Session):
        """
        Initialize repository with database session

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_by_id(self, entity_id: int) -> Optional[User]:
        """
        Get user by ID

        Args:
            entity_id: User ID

        Returns:
            User object or None if not found
        """
        try:
            return self.db.query(User).filter(User.id == entity_id).first()
        except Exception as e:
            logger.error(f"Error getting user by ID {entity_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve user: {str(e)}")

    def get_by_auth_id(self, auth_id: str) -> Optional[User]:
        """
        Get user by Auth0 ID

        Args:
            auth_id: Auth0 user ID

        Returns:
            User object or None if not found
        """
        try:
            return self.db.query(User).filter(User.id == auth_id).first()
        except Exception as e:
            logger.error(f"Error getting user by auth ID {auth_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve user: {str(e)}")

    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get all users with pagination

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of User objects
        """
        try:
            return self.db.query(User).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting all users: {str(e)}")
            raise DatabaseError(f"Failed to retrieve users: {str(e)}")

    def create(self, entity: Dict[str, Any]) -> User:
        """
        Create new user

        Args:
            entity: Dictionary containing user data

        Returns:
            Created User object
        """
        try:
            db_user = User(**entity)
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            logger.info(f"Created user: {db_user.email}")
            return db_user
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating user: {str(e)}")
            raise DatabaseError(f"Failed to create user: {str(e)}")

    def update(self, entity_id: int, data: Dict[str, Any]) -> Optional[User]:
        """
        Update user

        Args:
            entity_id: User ID
            data: Dictionary containing updated fields

        Returns:
            Updated User object or None if not found
        """
        try:
            db_user = self.get_by_id(entity_id)
            if not db_user:
                return None

            for key, value in data.items():
                if hasattr(db_user, key) and value is not None:
                    setattr(db_user, key, value)

            self.db.commit()
            self.db.refresh(db_user)
            logger.info(f"Updated user ID {entity_id}")
            return db_user
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user {entity_id}: {str(e)}")
            raise DatabaseError(f"Failed to update user: {str(e)}")

    def delete(self, entity_id: int) -> bool:
        """
        Delete user

        Args:
            entity_id: User ID

        Returns:
            True if deleted, False if not found
        """
        try:
            db_user = self.get_by_id(entity_id)
            if not db_user:
                return False

            self.db.delete(db_user)
            self.db.commit()
            logger.info(f"Deleted user ID {entity_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting user {entity_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete user: {str(e)}")

    def get_or_create(self, auth_id: str, email: str, full_name: str) -> User:
        """
        Get existing user or create new one

        Args:
            auth_id: Auth0 user ID
            email: User email
            full_name: User's full name

        Returns:
            User object
        """
        try:
            user = self.get_by_auth_id(auth_id)
            if user:
                return user

            # Create new user
            user_data = {
                "id": auth_id,
                "email": email,
                "full_name": full_name
            }
            return self.create(user_data)
        except Exception as e:
            logger.error(f"Error in get_or_create for user {auth_id}: {str(e)}")
            raise DatabaseError(f"Failed to get or create user: {str(e)}")
