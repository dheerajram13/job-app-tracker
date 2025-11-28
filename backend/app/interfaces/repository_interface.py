"""
Repository Interfaces - Data Access Layer Contracts
Implements Repository Pattern and Dependency Inversion Principle
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session


class IRepository(ABC):
    """
    Base Repository Interface

    Generic repository contract for CRUD operations
    """

    @abstractmethod
    def get_by_id(self, entity_id: int) -> Optional[Any]:
        """Get entity by ID"""
        pass

    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Any]:
        """Get all entities with pagination"""
        pass

    @abstractmethod
    def create(self, entity: Any) -> Any:
        """Create new entity"""
        pass

    @abstractmethod
    def update(self, entity_id: int, data: Dict) -> Optional[Any]:
        """Update entity"""
        pass

    @abstractmethod
    def delete(self, entity_id: int) -> bool:
        """Delete entity"""
        pass


class IJobRepository(IRepository):
    """
    Job Repository Interface

    Specific repository contract for Job entities
    """

    @abstractmethod
    def get_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Any]:
        """Get jobs by user ID"""
        pass

    @abstractmethod
    def search(
        self,
        user_id: str,
        search_query: Optional[str] = None,
        status: Optional[str] = None,
        skills: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Any], int]:
        """
        Search jobs with filters

        Returns:
            Tuple of (jobs list, total count)
        """
        pass

    @abstractmethod
    def get_skills_statistics(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Get top skills from user's jobs"""
        pass

    @abstractmethod
    def bulk_create(self, jobs: List[Dict], user_id: str) -> List[Any]:
        """Bulk create jobs (useful for scraped jobs)"""
        pass


class IUserRepository(IRepository):
    """
    User Repository Interface

    Specific repository contract for User entities
    """

    @abstractmethod
    def get_by_auth_id(self, auth_id: str) -> Optional[Any]:
        """Get user by Auth0 ID"""
        pass

    @abstractmethod
    def get_or_create(self, auth_id: str, email: str, full_name: str) -> Any:
        """Get existing user or create new one"""
        pass


class IResumeRepository(IRepository):
    """
    Resume Repository Interface

    Specific repository contract for Resume entities
    """

    @abstractmethod
    def get_by_user(self, user_id: str) -> List[Any]:
        """Get all resumes for a user"""
        pass

    @abstractmethod
    def get_active_resume(self, user_id: str) -> Optional[Any]:
        """Get user's active/default resume"""
        pass
