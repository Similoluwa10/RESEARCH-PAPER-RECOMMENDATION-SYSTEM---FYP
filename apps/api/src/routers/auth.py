"""
auth.py - Authentication Router

Handles user authentication including registration, login,
and JWT token management.
"""

from datetime import datetime, timedelta
import secrets
import importlib
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.dependencies import get_current_user, get_db
from src.schemas.user import (
    ForgotPasswordRequest,
    GoogleAuthRequest,
    MessageResponse,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from src.services.user_service import UserService

router = APIRouter(prefix="/auth")

PASSWORD_RESET_EXPIRE_MINUTES = 30


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def build_user_token(user_id: str) -> Token:
    """Build JWT token response for an authenticated user."""
    access_token = create_access_token(
        data={"sub": user_id},
        expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=access_token)


def create_password_reset_token(user_id: str) -> str:
    """Create a short-lived JWT token for password reset."""
    expire = datetime.utcnow() + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "type": "password_reset",
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user account.
    
    - Validates email uniqueness
    - Hashes password with pbkdf2_sha256
    - Returns created user profile
    """
    service = UserService(db)
    
    # Check if email already exists
    existing_user = await service.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    user = await service.create_user(user_data)
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user and return access token.
    
    Uses OAuth2 password flow for compatibility with OpenAPI/Swagger.
    """
    service = UserService(db)
    user = await service.authenticate(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return build_user_token(str(user.id))


@router.post("/google/login", response_model=Token)
async def login_with_google(
    payload: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate with Google ID token and issue API JWT."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GOOGLE_CLIENT_ID is not configured",
        )

    try:
        google_transport_requests = importlib.import_module("google.auth.transport.requests")
        google_id_token = importlib.import_module("google.oauth2.id_token")
    except ModuleNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="google-auth package is not installed",
        )

    try:
        token_info = google_id_token.verify_oauth2_token(
            payload.id_token,
            google_transport_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google ID token",
        )

    issuer = token_info.get("iss")
    if issuer not in {"accounts.google.com", "https://accounts.google.com"}:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token issuer",
        )

    email = token_info.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account email is unavailable",
        )

    name = token_info.get("name") or email.split("@")[0]
    service = UserService(db)
    user = await service.get_by_email(email)

    if not user:
        user = await service.create_user(
            UserCreate(
                email=email,
                name=name,
                password=secrets.token_urlsafe(32),
            )
        )

    return build_user_token(str(user.id))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    """Get current authenticated user profile."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    payload: UserUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current authenticated user's profile."""
    service = UserService(db)

    try:
        updated = await service.update_profile(current_user.id, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return updated


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Accept password reset request.

    Always returns a generic response to avoid email enumeration.
    """
    service = UserService(db)
    user = await service.get_by_email(payload.email)

    reset_url = None
    if user and settings.APP_ENV.lower() != "production":
        token = create_password_reset_token(str(user.id))
        reset_url = f"http://localhost:3000/reset-password?token={token}"

    return MessageResponse(
        message="If an account exists for that email, reset instructions have been sent.",
        reset_url=reset_url,
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reset password using a valid password reset JWT token."""
    try:
        token_payload = jwt.decode(
            payload.token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    if token_payload.get("type") != "password_reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )

    user_id = token_payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )

    service = UserService(db)

    try:
        parsed_user_id = UUID(str(user_id))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )

    updated = await service.update_password(parsed_user_id, payload.new_password)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return MessageResponse(message="Password has been reset successfully.")
