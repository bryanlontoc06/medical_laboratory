from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from src.models.user_role import UserRole
from src.schemas.tokens import Token


class UserBase(BaseModel):
    firstName: str = Field(min_length=1, max_length=20)
    lastName: str = Field(min_length=1, max_length=20)
    email: EmailStr = Field(max_length=100)
    role: Optional[UserRole] = Field(
        default=None,
        description="User's role. If not provided, it will default to 'guest' in the database.",
    )

    @field_validator("firstName", "lastName")
    @classmethod
    def capitalize_name(cls, v: str) -> str:
        # We use .title() in order to be "Juan Dela Cruz" (sample)
        return v.strip().title()


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=20)


class UserResponse(BaseModel):
    firstName: str
    lastName: str
    email: str
    role: str


class LoginResponse(BaseModel):
    token: Token
