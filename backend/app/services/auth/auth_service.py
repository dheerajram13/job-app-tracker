"""
Authentication Service
Handles JWT token verification using Auth0
"""
import logging
import jwt
from typing import Dict
from app.interfaces.auth_interface import IAuthService, IJWKSProvider
from app.exceptions import (
    AuthenticationError,
    TokenExpiredError,
    InvalidTokenError
)

logger = logging.getLogger(__name__)


class Auth0Service(IAuthService):
    """
    Auth0-based authentication service

    Handles JWT token verification using Auth0's JWKS
    Follows Single Responsibility Principle - only handles auth
    """

    def __init__(
        self,
        domain: str,
        api_audience: str,
        jwks_provider: IJWKSProvider
    ):
        """
        Initialize Auth0 service

        Args:
            domain: Auth0 domain
            api_audience: Auth0 API audience
            jwks_provider: JWKS provider for public key retrieval
        """
        self.domain = domain
        self.api_audience = api_audience
        self.jwks_provider = jwks_provider
        self.issuer = f'https://{domain}/'

    async def verify_token(self, token: str) -> Dict:
        """
        Verify JWT token and return payload

        Args:
            token: JWT token string

        Returns:
            Token payload dictionary

        Raises:
            TokenExpiredError: If token has expired
            InvalidTokenError: If token is invalid
            AuthenticationError: For other auth failures
        """
        try:
            logger.debug(f"Verifying token (length: {len(token)})")

            # Get token header to extract kid
            token_header = jwt.get_unverified_header(token)
            kid = token_header.get('kid')

            if not kid:
                raise InvalidTokenError("Token missing 'kid' in header")

            logger.debug(f"Token kid: {kid}")

            # Get public key from JWKS provider
            public_key = await self.jwks_provider.get_public_key(kid)

            # Decode and verify token
            payload = jwt.decode(
                token,
                key=public_key,
                algorithms=["RS256"],
                audience=self.api_audience,
                issuer=self.issuer
            )

            logger.info("Token verified successfully")
            logger.debug(f"Token payload: {payload}")

            return payload

        except jwt.ExpiredSignatureError as e:
            logger.error(f"Token expired: {str(e)}")
            raise TokenExpiredError()

        except jwt.InvalidAudienceError as e:
            logger.error(f"Invalid audience: {str(e)}")
            raise InvalidTokenError("Invalid audience")

        except jwt.InvalidIssuerError as e:
            logger.error(f"Invalid issuer: {str(e)}")
            raise InvalidTokenError("Invalid issuer")

        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {str(e)}")
            raise InvalidTokenError(str(e))

        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}", exc_info=True)
            raise AuthenticationError(f"Token verification failed: {str(e)}")

    async def get_user_info(self, token: str) -> Dict:
        """
        Get user information from token

        Args:
            token: JWT token string

        Returns:
            User information dictionary
        """
        payload = await self.verify_token(token)

        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "name": payload.get("name"),
            "email_verified": payload.get("email_verified", False),
            "permissions": payload.get("permissions", [])
        }
