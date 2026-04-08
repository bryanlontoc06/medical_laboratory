from datetime import timedelta
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError as JWTError
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from db.database import get_db
from src import models
from src.auth.auth import create_token
from src.schemas.tokens import Token, TokenResponse

router = APIRouter(prefix="/v1", tags=["Authentication"])

api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)
bearer_scheme = HTTPBearer()


def create_user_tokens(user: models.User) -> Token:
    logger.info("--- [ START CREATE USER TOKEN ] ---")
    logger.info(f"payload: {user}")
    base_data = {
        "id": user.uid,
        "email": user.email,
    }

    access_token = create_token(
        data={**base_data, "token_type": "access"},
        expires_delta=timedelta(seconds=settings.ACCESS_TOKEN_TTL),
    )

    refresh_token = create_token(
        data={**base_data, "token_type": "refresh"},  # Siguraduhin na "refresh" ito
        expires_delta=timedelta(seconds=settings.REFRESH_TOKEN_TTL),
    )

    id_token = create_token(
        data={
            **base_data,
            "firstName": user.firstName,
            "lastName": user.lastName,
            "role": user.role.value if hasattr(user.role, "value") else user.role,
            "token_type": "id",
        },
        expires_delta=timedelta(seconds=settings.ACCESS_TOKEN_TTL),
    )

    logger.info(
        f"response: {
            Token(
                access_token=access_token,
                refresh_token=refresh_token,
                id_token=id_token,
                expires_in=settings.ACCESS_TOKEN_TTL,
            )
        }"
    )
    logger.info("--- [ END CREATE USER TOKEN ] ---")
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        id_token=id_token,
        expires_in=settings.ACCESS_TOKEN_TTL,
    )


@router.post("/tokens", response_model=TokenResponse)
async def generate(
    db: Annotated[AsyncSession, Depends(get_db)],
    x_api_key: str = Security(api_key_header),
):
    logger.info("--- [ START CREATE SESSION ] ---")
    logger.info("event: SESSION")
    logger.info(f"payload: {x_api_key}")

    user_result = await db.execute(
        select(models.User).where(models.User.uid == x_api_key)
    )

    user = user_result.scalar_one_or_none()

    if user is None:
        logger.warning(f"User not found for the given API key: {x_api_key}")
        raise HTTPException(
            status_code=404,
            detail={
                "error": {"code": "ERR_USER_NOT_FOUND", "message": "User not found"}
            },
        )

    logger.info("event: SESSION")
    logger.info("--- [ END CREATE SESSION ] ---")
    return TokenResponse(token=create_user_tokens(user))


@router.patch("/tokens")
async def refresh(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
):
    refresh_token = token.credentials
    try:
        logger.info("--- [ START REFRESH TOKEN ] ---")
        logger.info(f"payload: {token}")
        # jwt.decode (Verify + Decode)
        payload = jwt.decode(
            refresh_token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.ALGORITHM],
        )

        if payload.get("token_type") != "refresh":
            raise HTTPException(
                status_code=401,
                detail={
                    "error": {
                        "code": "ERR_INVALID_TOKEN_TYPE",
                        "message": "Not a refresh token",
                    }
                },
            )

        # get User Id
        user_uid = payload.get("id")

        user_result = await db.execute(
            select(models.User).where(models.User.uid == user_uid)
        )

        user = user_result.scalar_one_or_none()

        if user is None:
            logger.warning(f"User not found for the given key: {user_uid}")
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {"code": "ERR_UNAUTHORIZED", "message": "Unauthorized"}
                },
            )

        logger.info("--- [ END REFRESH TOKEN ] ---")
        return TokenResponse(token=create_user_tokens(user))
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "code": "ERR_INVALID_TOKEN",
                    "message": "Invalid or expired token",
                }
            },
        )
