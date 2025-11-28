"""
Authentication Interface - Contract for authentication services
Follows Interface Segregation Principle
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional


class IAuthService(ABC):
    """
    Authentication Service Interface

    Defines contract for token verification and user authentication
    """

    @abstractmethod
    async def verify_token(self, token: str) -> Dict:
        """
        Verify JWT token and return payload

        Args:
            token: JWT token string

        Returns:
            Token payload dictionary

        Raises:
            AuthenticationError: If token is invalid
        """
        pass

    @abstractmethod
    async def get_user_info(self, token: str) -> Dict:
        """
        Get user information from token

        Args:
            token: JWT token string

        Returns:
            User information dictionary
        """
        pass


class IJWKSProvider(ABC):
    """
    JWKS Provider Interface

    Handles retrieval and caching of JSON Web Key Sets
    Separated from auth service for better testability
    """

    @abstractmethod
    async def get_public_key(self, kid: str) -> bytes:
        """
        Get public key for token verification

        Args:
            kid: Key ID from token header

        Returns:
            Public key in PEM format
        """
        pass

    @abstractmethod
    def clear_cache(self) -> None:
        """Clear the JWKS cache"""
        pass
