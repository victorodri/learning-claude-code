"""
Pydantic schemas for authentication requests and responses.
"""
from pydantic import BaseModel, Field, EmailStr


class UserRegister(BaseModel):
    """
    Schema for user registration request.
    """
    email: EmailStr = Field(
        ...,
        description="User's email address"
    )
    password: str = Field(
        ...,
        min_length=8,
        description="User's password (minimum 8 characters)"
    )
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="User's full name"
    )


class UserLogin(BaseModel):
    """
    Schema for user login request.
    """
    email: EmailStr = Field(
        ...,
        description="User's email address"
    )
    password: str = Field(
        ...,
        description="User's password"
    )


class Token(BaseModel):
    """
    Schema for JWT token response.
    """
    access_token: str = Field(
        ...,
        description="JWT access token"
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')"
    )


class UserResponse(BaseModel):
    """
    Schema for user information response.
    Excludes sensitive fields like password.
    """
    id: int
    email: str
    full_name: str
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
