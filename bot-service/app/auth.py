"""
JWT authentication for service-to-service communication.

The Connector Service signs a short-lived JWT with a shared secret
(`JWT_SECRET`) and attaches it as a Bearer token on every request.
This module provides the FastAPI dependency that verifies that token.

Flow:
  Connector  →  signs JWT  →  Bot Service
  Bot Service  →  verifies JWT  →  processes request (or returns 401)
"""

import os
from datetime import datetime, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# ---------------------------------------------------------------------------
# Config (read once at import time; fails loudly if missing)
# ---------------------------------------------------------------------------

JWT_SECRET: str = os.environ["JWT_SECRET"]
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

# HTTPBearer extracts the token from the `Authorization: Bearer <token>` header
_bearer_scheme = HTTPBearer()


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------


async def verify_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> dict:
    """
    FastAPI dependency that validates the incoming JWT.

    Raises HTTP 401 if:
      - The token is missing or malformed.
      - The signature doesn't match `JWT_SECRET`.
      - The token has expired (`exp` claim).
      - The `service` claim is not 'connector' (prevents token reuse from
        other potential services).

    Returns the decoded payload dict so routes can inspect claims if needed.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise credentials_exception

    # Extra claim check: only tokens issued by the connector are accepted
    if payload.get("service") != "connector":
        raise credentials_exception

    return payload
