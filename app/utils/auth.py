"""
Authentication and Authorization utilities
Handles role-based access control (RBAC)
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from passlib.hash import pbkdf2_sha256

import jwt
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app import models

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))


# ────────────────────────────────────────────────────────────────────────────
# PASSWORD HELPERS
# ────────────────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    pwd = password or ""
    # pbkdf2_sha256 avoids bcrypt 72-byte limits and has wide support
    return pbkdf2_sha256.hash(pwd)


def verify_password(password: str, hashed: str) -> bool:
    pwd = password or ""
    return pbkdf2_sha256.verify(pwd, hashed)

# ────────────────────────────────────────────────────────────────────────────
# TOKEN HELPERS
# ────────────────────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ────────────────────────────────────────────────────────────────────────────
# ROLE-BASED DEPENDENCIES
# ────────────────────────────────────────────────────────────────────────────

async def get_current_user(
    user_id: Optional[int] = None,
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db)
) -> models.User:
    """
    Resolve the current user from Authorization: Bearer <JWT> or fallback user_id param.
    """
    resolved_user_id: Optional[int] = None

    if authorization:
        parts = authorization.split()
        token = None
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
        else:
            token = authorization.strip()

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            sub = payload.get("sub")
            resolved_user_id = int(sub) if sub is not None else None
        except Exception:
            # Backward-compatible demo tokens: demo-token-<user_id>
            if token.startswith("demo-token-"):
                try:
                    resolved_user_id = int(token.replace("demo-token-", ""))
                except ValueError:
                    resolved_user_id = None
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token"
                )

    if resolved_user_id is None:
        resolved_user_id = user_id

    if resolved_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    user = db.query(models.User).filter(models.User.id == resolved_user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user


async def require_owner(current_user: models.User = Depends(get_current_user)) -> models.User:
    """
    Dependency: Only OWNER role can access
    """
    if current_user.role != "OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can perform this action"
        )
    return current_user


async def require_staff(current_user: models.User = Depends(get_current_user)) -> models.User:
    """
    Dependency: STAFF or OWNER can access
    """
    if current_user.role not in ["STAFF", "OWNER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    return current_user


async def check_permission(
    permission_name: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> bool:
    """
    Check if user has a specific permission
    """
    # OWNER has all permissions
    if current_user.role == "OWNER":
        return True
    
    # Check if STAFF has this permission
    perm = db.query(models.Permission).filter(
        models.Permission.user_id == current_user.id,
        models.Permission.permission_name == permission_name
    ).first()
    
    return perm is not None


# ────────────────────────────────────────────────────────────────────────────
# PREDEFINED ROLE PERMISSIONS
# ────────────────────────────────────────────────────────────────────────────

OWNER_PERMISSIONS = {
    "manage_staff",
    "manage_branches",
    "view_reports",
    "create_product",
    "manage_settings",
    "view_all_orders",
    "manage_printers"
}

STAFF_PERMISSIONS = {
    "create_product",
    "view_branch_orders",
    "create_order",
    "print_document"
}
