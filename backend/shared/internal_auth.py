"""
Internal authentication for microservices.
These services trust the API Gateway for authentication.
They read user context from headers set by the gateway.
"""

from fastapi import HTTPException, Header
from typing import Optional
from shared.types import RoleEnum


def get_user_from_headers(
    x_user_id: Optional[str] = Header(None),
    x_username: Optional[str] = Header(None),
    x_user_role: Optional[str] = Header(None)
) -> dict:
    """
    Get user context from headers set by API Gateway.
    Gateway validates JWT and passes user info via headers.
    """
    # If no headers present, allow the request (for internal gateway calls)
    if not x_user_id:
        # This means it's an internal call from gateway (like registration)
        # Gateway will handle permissions, so we allow it
        return {"user_id": None, "username": None, "role": "admin"}
    
    return {
        "user_id": int(x_user_id) if x_user_id else None,
        "username": x_username,
        "role": x_user_role,
        "sub": x_username  # For backward compatibility
    }


def require_admin_internal(user: dict = None) -> dict:
    """
    Require admin role for internal service calls.
    Used when service needs to enforce admin-only operations.
    """
    if user and user.get("role") != RoleEnum.ADMIN.value:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return user
