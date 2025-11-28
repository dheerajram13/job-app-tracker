"""
Custom Exception Hierarchy

Provides specific exception types for better error handling
"""


class ApplicationException(Exception):
    """Base exception for all application-specific exceptions"""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


# Authentication Exceptions
class AuthenticationError(ApplicationException):
    """Raised when authentication fails"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class TokenExpiredError(AuthenticationError):
    """Raised when token has expired"""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message)


class InvalidTokenError(AuthenticationError):
    """Raised when token is invalid"""

    def __init__(self, message: str = "Invalid token"):
        super().__init__(message)


# Authorization Exceptions
class AuthorizationError(ApplicationException):
    """Raised when user lacks permissions"""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status_code=403)


# Job Scraping Exceptions
class JobScraperError(ApplicationException):
    """Base exception for job scraping errors"""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message, status_code)


class SiteNotSupportedError(JobScraperError):
    """Raised when trying to scrape an unsupported site"""

    def __init__(self, site_name: str):
        super().__init__(f"Site '{site_name}' is not supported", status_code=400)


class ScrapingFailedError(JobScraperError):
    """Raised when scraping fails"""

    def __init__(self, site_name: str, reason: str):
        super().__init__(
            f"Failed to scrape {site_name}: {reason}",
            status_code=500
        )


class RateLimitExceededError(JobScraperError):
    """Raised when rate limit is hit"""

    def __init__(self, site_name: str):
        super().__init__(
            f"Rate limit exceeded for {site_name}",
            status_code=429
        )


# Job Parsing Exceptions
class JobParsingError(ApplicationException):
    """Base exception for job parsing errors"""

    def __init__(self, message: str, url: str = None):
        self.url = url
        super().__init__(message, status_code=400)


class InvalidURLError(JobParsingError):
    """Raised when URL is invalid"""

    def __init__(self, url: str):
        super().__init__(f"Invalid URL: {url}", url=url)


class ParseFailedError(JobParsingError):
    """Raised when parsing fails"""

    def __init__(self, url: str, reason: str):
        super().__init__(
            f"Failed to parse job from {url}: {reason}",
            url=url
        )


# Database Exceptions
class DatabaseError(ApplicationException):
    """Base exception for database errors"""

    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class EntityNotFoundError(DatabaseError):
    """Raised when entity is not found"""

    def __init__(self, entity_type: str, entity_id: any):
        super().__init__(f"{entity_type} with ID {entity_id} not found")
        self.status_code = 404


class EntityAlreadyExistsError(DatabaseError):
    """Raised when trying to create duplicate entity"""

    def __init__(self, entity_type: str, identifier: str):
        super().__init__(f"{entity_type} with {identifier} already exists")
        self.status_code = 409


# Validation Exceptions
class ValidationError(ApplicationException):
    """Raised when validation fails"""

    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message, status_code=422)


class InvalidParameterError(ValidationError):
    """Raised when parameter is invalid"""

    def __init__(self, parameter: str, reason: str):
        super().__init__(f"Invalid parameter '{parameter}': {reason}", field=parameter)


# External Service Exceptions
class ExternalServiceError(ApplicationException):
    """Raised when external service call fails"""

    def __init__(self, service_name: str, reason: str):
        super().__init__(
            f"External service '{service_name}' error: {reason}",
            status_code=503
        )


class NetworkError(ApplicationException):
    """Raised when network request fails"""

    def __init__(self, message: str):
        super().__init__(f"Network error: {message}", status_code=503)
