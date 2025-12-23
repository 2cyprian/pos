"""
Authentication Router
Handles login, registration, and session management
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from pydantic import BaseModel
from app.utils.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, hash_password, verify_password

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class UserData(BaseModel):
    user_id: int
    username: str
    email: str
    role: str
    branch_id: int | None


class LoginResponse(BaseModel):
    user: UserData
    token: str
    message: str


@router.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """
    Login endpoint for Owner and Staff.
    Returns user information if credentials are valid.
    
    In production, this should:
    - Hash passwords with bcrypt
    - Return JWT tokens
    - Implement rate limiting
    """
    # Find user by username
    user = db.query(models.User).filter(
        models.User.username == credentials.username
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Contact administrator."
        )
    
    # Verify hashed password (supports long passwords)
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Create JWT access token
    token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token({"sub": str(user.id), "role": user.role}, expires_delta=token_expires)

    # Return user info
    return LoginResponse(
        user=UserData(
            user_id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            branch_id=user.branch_id
        ),
        token=token,
        message=f"Welcome back, {user.username}! Role: {user.role}"
    )


@router.post("/register-owner", response_model=schemas.UserResponse)
def register_owner(user: schemas.OwnerRegister, db: Session = Depends(get_db)):
    """
    Register a new OWNER account.
    Each owner can manage their own branches and staff independently.
    Multiple owners are allowed - each runs their own business.
    
    NOTE: Role is automatically set to OWNER - don't pass it in request.
    """
    # Check if username exists
    existing_user = db.query(models.User).filter(
        models.User.username == user.username
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Check if email exists
    existing_email = db.query(models.User).filter(
        models.User.email == user.email
    ).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create owner account
    new_owner = models.User(
        username=user.username,
        email=user.email,
        password_hash=hash_password(user.password),
        role="OWNER",
        is_active=True
    )
    
    db.add(new_owner)
    db.commit()
    db.refresh(new_owner)
    
    return new_owner


@router.get("/me")
def get_current_user_info(user_id: int, db: Session = Depends(get_db)):
    """
    Get current logged-in user information.
    Pass user_id from login response.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "branch_id": user.branch_id,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat()
    }


@router.post("/logout")
def logout():
    """
    Logout endpoint.
    In production with JWT, this would invalidate the token.
    """
    return {"message": "Logged out successfully"}
