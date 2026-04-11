import uuid
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import APIKeyHeader, HTTPBearer, OAuth2PasswordRequestForm
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from core.config import settings
from db.database import get_db
from src import models
from src.auth.auth import create_token, hash_password, verify_password
from src.auth.security_guards import require_guest_client
from src.schemas.tokens import Token
from src.schemas.users import LoginResponse, UserCreate, UserResponse

router = APIRouter(prefix="/v1", tags=["Users"])

api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)
bearer_scheme = HTTPBearer()


@router.post(
    "/register",
    response_model=UserResponse,
    dependencies=[Depends(require_guest_client)],
)
async def register(
    user: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logger.info("--- [ START REGISTER ] ---")
    logger.info(f"payload: {user}")
    result = await db.execute(
        select(models.User).where(func.lower(models.User.email) == user.email.lower())
    )

    existing_email = result.scalar_one_or_none()
    if existing_email is not None:
        logger.warning(f"Email {existing_email} already exists.")
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "ERR_EMAIL_ALREADY_EXISTS",
                    "message": "Email already exists. Please try again!",
                }
            },
        )

    new_user = models.User(
        uid=str(uuid.uuid4()),
        firstName=user.firstName,
        lastName=user.lastName,
        email=user.email.lower(),
        password=hash_password(user.password),
    )
    if user.role:
        new_user.role = user.role
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    logger.info(f"response: {new_user}")
    logger.info("--- [ END REGISTER ] ---")
    return new_user


@router.post(
    "/authenticate",
    response_model=LoginResponse,
    dependencies=[Depends(require_guest_client)],
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    logger.info("--- [ START USER LOGIN ] ---")
    result = await db.execute(
        select(models.User).where(
            func.lower(models.User.email) == form_data.username.lower()
        )
    )
    user = result.scalars().first()
    # Verify user exists and password is correct
    # Don't reveal which one failed (security best practice)
    if not user or not verify_password(form_data.password, user.password):
        logger.warning(
            f"event: LOGIN_FAILED | payload: {{'email': '{form_data.username}'}}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_ttl = settings.ACCESS_TOKEN_TTL
    refresh_token_ttl = settings.REFRESH_TOKEN_TTL
    if not refresh_token_ttl:
        try:
            refresh_token_ttl = int(refresh_token_ttl)
        except ValueError:
            logger.error(
                f"Invalid REFRESH TOKEN TTL value: {refresh_token_ttl}. Using default of {refresh_token_ttl}."
            )
            refresh_token_ttl = settings.REFRESH_TOKEN_TTL

    base_data = {
        "id": user.uid,
        "email": user.email,
    }

    access_token_expires = timedelta(seconds=access_token_ttl)
    # Create access token (for simplicity, we are not creating a separate refresh token here)
    access_token = create_token(
        data={**base_data, "token_type": "access"},
        expires_delta=access_token_expires,
    )

    # Refresh Token (optional, can be implemented similarly to access token with a longer expiration)
    refresh_token = create_token(
        data={**base_data, "token_type": "refresh"},
        expires_delta=timedelta(days=int(refresh_token_ttl)),
    )

    # ID Token (contains user info, can be used by frontend)
    id_token = create_token(
        data={
            **base_data,
            "firstName": user.firstName,
            "lastName": user.lastName,
            "email": user.email,
            "role": user.role,
            "token_type": "id",
        },
        expires_delta=timedelta(seconds=access_token_ttl),
    )
    logger.info("--- [ END USER LOGIN ] ---")
    return LoginResponse(
        token=Token(
            access_token=access_token,
            refresh_token=refresh_token,
            id_token=id_token,
            expires_in=access_token_ttl,  # seconds
        )
    )
