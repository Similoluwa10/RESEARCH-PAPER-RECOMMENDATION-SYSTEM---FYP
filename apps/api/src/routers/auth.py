"""
auth.py - Authentication Router

Handles user authentication including registration, login,
and JWT token management.
"""

from datetime import datetime, timedelta
import secrets
import importlib
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.dependencies import get_current_user, get_db
from src.schemas.user import GoogleAuthRequest, Token, UserCreate, UserResponse
from src.services.user_service import UserService

router = APIRouter(prefix="/auth")


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
