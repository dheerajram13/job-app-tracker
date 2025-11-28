"""
JWKS Provider
Handles fetching and caching of JSON Web Key Sets
"""
import logging
import base64
import requests
from typing import Dict, Optional
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from app.interfaces.auth_interface import IJWKSProvider
from app.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


class Auth0JWKSProvider(IJWKSProvider):
    """
    Auth0 JWKS Provider

    Fetches and caches public keys from Auth0's JWKS endpoint
    Implements Single Responsibility Principle - only handles JWKS
    """

    def __init__(self, auth0_domain: str):
        """
        Initialize JWKS provider

        Args:
            auth0_domain: Auth0 domain
        """
        self.auth0_domain = auth0_domain
        self.jwks_url = f'https://{auth0_domain}/.well-known/jwks.json'
        self._cache: Dict[str, bytes] = {}

    async def get_public_key(self, kid: str) -> bytes:
        """
        Get public key for token verification

        Args:
            kid: Key ID from token header

        Returns:
            Public key in PEM format

        Raises:
            AuthenticationError: If key cannot be retrieved
        """
        # Check cache first
        if kid in self._cache:
            logger.debug(f"Using cached public key for kid: {kid}")
            return self._cache[kid]

        # Fetch from JWKS endpoint
        try:
            logger.info(f"Fetching JWKS from Auth0 for kid: {kid}")
            jwks = requests.get(self.jwks_url, timeout=10).json()

            # Find the signing key
            signing_key = None
            for key in jwks.get('keys', []):
                if key.get('kid') == kid:
                    signing_key = key
                    break

            if not signing_key:
                raise AuthenticationError(f"Unable to find key with kid: {kid}")

            # Convert JWK to PEM
            public_key = self._jwk_to_pem(signing_key)

            # Cache the key
            self._cache[kid] = public_key

            logger.info(f"Successfully retrieved and cached public key for kid: {kid}")
            return public_key

        except requests.RequestException as e:
            logger.error(f"Error fetching JWKS: {str(e)}")
            raise AuthenticationError(f"Failed to fetch JWKS: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing JWKS: {str(e)}")
            raise AuthenticationError(f"Failed to process JWKS: {str(e)}")

    def clear_cache(self) -> None:
        """Clear the JWKS cache"""
        self._cache.clear()
        logger.info("JWKS cache cleared")

    def _jwk_to_pem(self, jwk: Dict) -> bytes:
        """
        Convert JWK to PEM format

        Args:
            jwk: JSON Web Key dictionary

        Returns:
            Public key in PEM format
        """
        try:
            # Decode the exponent and modulus
            e = self._decode_value(jwk['e'])
            n = self._decode_value(jwk['n'])

            # Create RSA public numbers
            numbers = RSAPublicNumbers(e=e, n=n)

            # Generate public key
            public_key = numbers.public_key(backend=default_backend())

            # Convert to PEM format
            pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            return pem

        except KeyError as e:
            raise AuthenticationError(f"Invalid JWK format: missing {str(e)}")
        except Exception as e:
            raise AuthenticationError(f"Failed to convert JWK to PEM: {str(e)}")

    @staticmethod
    def _ensure_bytes(key) -> bytes:
        """
        Ensure key is in bytes format

        Args:
            key: Key (string or bytes)

        Returns:
            Key as bytes
        """
        if isinstance(key, str):
            key = key.encode('utf-8')
        return key

    @classmethod
    def _decode_value(cls, val: str) -> int:
        """
        Decode base64url-encoded value to integer

        Args:
            val: Base64url-encoded string

        Returns:
            Decoded integer
        """
        # Add padding if needed
        val_bytes = cls._ensure_bytes(val)
        padding = b'=' * (4 - len(val_bytes) % 4)
        val_padded = val_bytes + padding

        # Decode base64
        decoded = base64.urlsafe_b64decode(val_padded)

        # Convert to integer
        return int.from_bytes(decoded, 'big')
