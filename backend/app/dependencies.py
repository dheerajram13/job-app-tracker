"""
Dependency Injection Container
Centralizes dependency management and follows Dependency Inversion Principle
"""
import logging
import os
from typing import Optional, Generator
from functools import lru_cache
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.repositories.job_repository import JobRepository
from app.repositories.user_repository import UserRepository
from app.services.auth.auth_service import Auth0Service
from app.services.auth.jwks_provider import Auth0JWKSProvider
from app.services.job_search_service import JobSearchService
from app.services.scrapers.scraper_factory import ScraperFactory
from app.services.job_result_processor import JobResultProcessor
from app.services.job_description_fetcher import JobDescriptionFetcher

logger = logging.getLogger(__name__)


class DependencyContainer:
    """
    Dependency Injection Container

    Manages creation and lifecycle of application dependencies
    Implements Singleton pattern for shared services
    """

    _instance: Optional['DependencyContainer'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize container (only once due to singleton)"""
        if self._initialized:
            return

        # Configuration
        self.auth0_domain = os.getenv("AUTH0_DOMAIN")
        self.auth0_api_audience = os.getenv("AUTH0_API_AUDIENCE")

        # Validate required config
        if not self.auth0_domain or not self.auth0_api_audience:
            logger.warning("Auth0 configuration missing. Authentication may not work.")

        # Initialize singletons
        self._jwks_provider: Optional[Auth0JWKSProvider] = None
        self._auth_service: Optional[Auth0Service] = None
        self._scraper_factory: Optional[ScraperFactory] = None
        self._result_processor: Optional[JobResultProcessor] = None
        self._description_fetcher: Optional[JobDescriptionFetcher] = None
        self._job_search_service: Optional[JobSearchService] = None

        self._initialized = True
        logger.info("Dependency container initialized")

    # Database Dependencies

    def get_db(self) -> Session:
        """
        Get database session

        Returns:
            SQLAlchemy database session

        Note: Caller is responsible for closing the session
        """
        db = SessionLocal()
        try:
            return db
        except Exception as e:
            logger.error(f"Error creating database session: {str(e)}")
            db.close()
            raise

    # Repository Dependencies

    def get_job_repository(self, db: Session) -> JobRepository:
        """Get job repository instance"""
        return JobRepository(db)

    def get_user_repository(self, db: Session) -> UserRepository:
        """Get user repository instance"""
        return UserRepository(db)

    # Authentication Dependencies

    def get_jwks_provider(self) -> Auth0JWKSProvider:
        """Get JWKS provider (singleton)"""
        if self._jwks_provider is None:
            self._jwks_provider = Auth0JWKSProvider(self.auth0_domain)
            logger.info("JWKS provider created")
        return self._jwks_provider

    def get_auth_service(self) -> Auth0Service:
        """Get authentication service (singleton)"""
        if self._auth_service is None:
            jwks_provider = self.get_jwks_provider()
            self._auth_service = Auth0Service(
                domain=self.auth0_domain,
                api_audience=self.auth0_api_audience,
                jwks_provider=jwks_provider
            )
            logger.info("Auth service created")
        return self._auth_service

    # Job Scraping Dependencies

    def get_scraper_factory(self) -> ScraperFactory:
        """Get scraper factory (singleton)"""
        if self._scraper_factory is None:
            self._scraper_factory = ScraperFactory()
            logger.info("Scraper factory created")
        return self._scraper_factory

    def get_result_processor(self) -> JobResultProcessor:
        """Get job result processor (singleton)"""
        if self._result_processor is None:
            self._result_processor = JobResultProcessor()
            logger.info("Result processor created")
        return self._result_processor

    def get_description_fetcher(self) -> JobDescriptionFetcher:
        """Get job description fetcher (singleton)"""
        if self._description_fetcher is None:
            self._description_fetcher = JobDescriptionFetcher()
            logger.info("Description fetcher created")
        return self._description_fetcher

    def get_job_search_service(self) -> JobSearchService:
        """Get job search service (singleton)"""
        if self._job_search_service is None:
            self._job_search_service = JobSearchService(
                scraper_factory=self.get_scraper_factory(),
                result_processor=self.get_result_processor(),
                description_fetcher=self.get_description_fetcher()
            )
            logger.info("Job search service created with injected dependencies")
        return self._job_search_service


# Global container instance
container = DependencyContainer()


# FastAPI dependency functions

def get_db() -> Generator:
    """
    FastAPI dependency for database session

    Yields database session and ensures it's closed after use
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(token: str):
    """
    FastAPI dependency for current user from token

    Args:
        token: JWT token

    Returns:
        User payload from token
    """
    auth_service = container.get_auth_service()
    return await auth_service.verify_token(token)


@lru_cache()
def get_dependency_container() -> DependencyContainer:
    """
    Get dependency container instance (cached)

    Returns:
        DependencyContainer singleton
    """
    return container