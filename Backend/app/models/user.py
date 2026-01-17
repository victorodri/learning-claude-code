from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel


class User(BaseModel):
    """
    User model for authentication.

    Fields:
    - email: Unique user email (used for login)
    - hashed_password: Bcrypt hashed password
    - full_name: User's display name
    - is_active: Whether user can login

    Relationships:
    - ratings: One-to-many with CourseRating
    """
    __tablename__ = 'users'

    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    hashed_password = Column(
        String(255),
        nullable=False
    )
    full_name = Column(
        String(255),
        nullable=False
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False
    )

    # Relationships
    ratings = relationship(
        "CourseRating",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<User("
            f"id={self.id}, "
            f"email={self.email}, "
            f"full_name={self.full_name}, "
            f"is_active={self.is_active}"
            f")>"
        )

    def to_dict(self):
        """
        Convert model to dictionary for API responses.
        Excludes sensitive fields like hashed_password.
        """
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
