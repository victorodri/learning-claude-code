"""
Authentication router for user registration, login, and profile endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import UserRegister, UserLogin, Token, UserResponse
from app.core.dependencies import CurrentUser, get_auth_service


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "User registered successfully"},
        400: {"description": "Email already registered"}
    }
)
def register(
    user_data: UserRegister,
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """
    Register a new user.

    Creates a new user account with the provided email, password, and name.
    Password is hashed before storage.

    Request Body:
    - email: Valid email address (must be unique)
    - password: Minimum 8 characters
    - full_name: User's display name

    Returns:
        User information (excluding password)

    Raises:
        400: Email already registered
    """
    try:
        user = auth_service.create_user(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name
        )
        return UserResponse(**user.to_dict())
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/login",
    response_model=Token,
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"}
    }
)
def login(
    user_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
) -> Token:
    """
    Login and obtain JWT access token.

    Authenticates user with email and password, returns JWT token.

    Request Body:
    - email: User's email address
    - password: User's password

    Returns:
        JWT access token

    Raises:
        401: Invalid email or password
    """
    user = auth_service.authenticate_user(
        email=user_data.email,
        password=user_data.password
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Create JWT token with user ID as subject
    access_token = auth_service.create_access_token(
        data={"sub": str(user.id)}
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserResponse,
    responses={
        200: {"description": "Current user information"},
        401: {"description": "Not authenticated"}
    }
)
def get_current_user_info(current_user: CurrentUser) -> UserResponse:
    """
    Get current authenticated user's information.

    Requires valid JWT token in Authorization header.

    Returns:
        Current user information (excluding password)

    Raises:
        401: Invalid or missing token
    """
    return UserResponse(**current_user.to_dict())
