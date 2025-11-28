"""
Job Repository Implementation
Implements Repository Pattern for Job entity data access
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func
from app.interfaces.repository_interface import IJobRepository
from app.models.job import Job
from app.exceptions import EntityNotFoundError, DatabaseError
import logging

logger = logging.getLogger(__name__)


class JobRepository(IJobRepository):
    """
    Concrete implementation of Job Repository

    Handles all database operations for Job entities
    Follows Single Responsibility Principle - only concerned with data access
    """

    def __init__(self, db: Session):
        """
        Initialize repository with database session

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_by_id(self, entity_id: int) -> Optional[Job]:
        """
        Get job by ID

        Args:
            entity_id: Job ID

        Returns:
            Job object or None if not found
        """
        try:
            return self.db.query(Job).filter(Job.id == entity_id).first()
        except Exception as e:
            logger.error(f"Error getting job by ID {entity_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve job: {str(e)}")

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Job]:
        """
        Get all jobs with pagination

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Job objects
        """
        try:
            return self.db.query(Job).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting all jobs: {str(e)}")
            raise DatabaseError(f"Failed to retrieve jobs: {str(e)}")

    def get_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Job]:
        """
        Get jobs by user ID

        Args:
            user_id: User's Auth0 ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Job objects for the user
        """
        try:
            return (
                self.db.query(Job)
                .filter(Job.user_id == user_id)
                .order_by(desc(Job.date_applied))
                .offset(skip)
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(f"Error getting jobs for user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve user jobs: {str(e)}")

    def create(self, entity: Dict[str, Any]) -> Job:
        """
        Create new job

        Args:
            entity: Dictionary containing job data

        Returns:
            Created Job object
        """
        try:
            db_job = Job(**entity)
            self.db.add(db_job)
            self.db.commit()
            self.db.refresh(db_job)
            logger.info(f"Created job: {db_job.title} at {db_job.company}")
            return db_job
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating job: {str(e)}")
            raise DatabaseError(f"Failed to create job: {str(e)}")

    def update(self, entity_id: int, data: Dict[str, Any]) -> Optional[Job]:
        """
        Update job

        Args:
            entity_id: Job ID
            data: Dictionary containing updated fields

        Returns:
            Updated Job object or None if not found
        """
        try:
            db_job = self.get_by_id(entity_id)
            if not db_job:
                return None

            for key, value in data.items():
                if hasattr(db_job, key) and value is not None:
                    setattr(db_job, key, value)

            self.db.commit()
            self.db.refresh(db_job)
            logger.info(f"Updated job ID {entity_id}")
            return db_job
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating job {entity_id}: {str(e)}")
            raise DatabaseError(f"Failed to update job: {str(e)}")

    def delete(self, entity_id: int) -> bool:
        """
        Delete job

        Args:
            entity_id: Job ID

        Returns:
            True if deleted, False if not found
        """
        try:
            db_job = self.get_by_id(entity_id)
            if not db_job:
                return False

            self.db.delete(db_job)
            self.db.commit()
            logger.info(f"Deleted job ID {entity_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting job {entity_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete job: {str(e)}")

    def search(
        self,
        user_id: str,
        search_query: Optional[str] = None,
        status: Optional[str] = None,
        skills: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Job], int]:
        """
        Search jobs with filters

        Args:
            user_id: User's Auth0 ID
            search_query: Text to search in title, company, description
            status: Job status filter
            skills: List of skills to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (list of Job objects, total count)
        """
        try:
            query = self.db.query(Job).filter(Job.user_id == user_id)

            # Apply status filter
            if status:
                query = query.filter(Job.status == status)

            # Apply text search
            if search_query:
                search_filter = or_(
                    Job.title.ilike(f"%{search_query}%"),
                    Job.company.ilike(f"%{search_query}%"),
                    Job.description.ilike(f"%{search_query}%")
                )
                query = query.filter(search_filter)

            # Apply skills filter
            if skills:
                for skill in skills:
                    query = query.filter(Job.description.ilike(f"%{skill}%"))

            # Get total count before pagination
            total = query.count()

            # Apply pagination and ordering
            jobs = query.order_by(desc(Job.date_applied)).offset(skip).limit(limit).all()

            return jobs, total
        except Exception as e:
            logger.error(f"Error searching jobs: {str(e)}")
            raise DatabaseError(f"Failed to search jobs: {str(e)}")

    def get_skills_statistics(self, user_id: str, limit: int = 20) -> List[Dict]:
        """
        Get top skills from user's jobs

        Args:
            user_id: User's Auth0 ID
            limit: Maximum number of skills to return

        Returns:
            List of dictionaries with skill name and count
        """
        try:
            # Common tech skills to search for
            common_skills = [
                "python", "javascript", "java", "sql", "aws", "docker", "kubernetes",
                "react", "node.js", "typescript", "git", "linux", "agile", "scrum",
                "machine learning", "data analysis", "cloud computing", "devops",
                "go", "rust", "c++", "c#", "ruby", "php", "swift", "kotlin",
                "angular", "vue.js", "django", "flask", "spring", "microservices",
                "postgresql", "mongodb", "redis", "elasticsearch", "kafka",
                "terraform", "ansible", "jenkins", "ci/cd", "restful api", "graphql"
            ]

            skill_counts = []
            for skill in common_skills:
                count = (
                    self.db.query(Job)
                    .filter(
                        Job.user_id == user_id,
                        Job.description.ilike(f"%{skill}%")
                    )
                    .count()
                )
                if count > 0:
                    skill_counts.append({"skill": skill, "count": count})

            # Sort by count and limit results
            skill_counts.sort(key=lambda x: x["count"], reverse=True)
            return skill_counts[:limit]
        except Exception as e:
            logger.error(f"Error getting skills statistics: {str(e)}")
            raise DatabaseError(f"Failed to get skills statistics: {str(e)}")

    def bulk_create(self, jobs: List[Dict], user_id: str) -> List[Job]:
        """
        Bulk create jobs (useful for scraped jobs)

        Args:
            jobs: List of job dictionaries
            user_id: User's Auth0 ID

        Returns:
            List of created Job objects
        """
        try:
            created_jobs = []
            for job_data in jobs:
                job_data["user_id"] = user_id
                db_job = Job(**job_data)
                self.db.add(db_job)
                created_jobs.append(db_job)

            self.db.commit()
            for job in created_jobs:
                self.db.refresh(job)

            logger.info(f"Bulk created {len(created_jobs)} jobs for user {user_id}")
            return created_jobs
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error bulk creating jobs: {str(e)}")
            raise DatabaseError(f"Failed to bulk create jobs: {str(e)}")

    def get_by_url(self, user_id: str, url: str) -> Optional[Job]:
        """
        Get job by URL (useful for checking duplicates)

        Args:
            user_id: User's Auth0 ID
            url: Job URL

        Returns:
            Job object or None if not found
        """
        try:
            return (
                self.db.query(Job)
                .filter(Job.user_id == user_id, Job.url == url)
                .first()
            )
        except Exception as e:
            logger.error(f"Error getting job by URL: {str(e)}")
            raise DatabaseError(f"Failed to get job by URL: {str(e)}")
