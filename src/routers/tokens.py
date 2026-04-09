from datetime import timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import APIKeyHeader, HTTPBearer
from loguru import logger

from core.config import settings
from src import models
from src.auth.auth import create_token
from src.auth.security_guards import get_current_user, verify_api_key
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
        data={**base_data, "token_type": "refresh"},
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
    user: Annotated[models.User, Depends(verify_api_key)],
):
    logger.info("--- [ START CREATE SESSION ] ---")
    logger.info("event: SESSION")
    logger.info(f"payload: {user}")

    tokens = create_user_tokens(user)

    logger.info("event: SESSION")
    logger.info("--- [ END CREATE SESSION ] ---")
    return TokenResponse(token=tokens)


@router.patch("/tokens")
async def refresh(
    current_session: Annotated[dict[str, Any], Depends(get_current_user)],
):
    logger.info("--- [ START REFRESH TOKEN ] ---")
    logger.info(f"payload: {current_session.keys()}")
    if current_session.get("token_type") != "refresh":
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "code": "ERR_INVALID_TOKEN_TYPE",
                    "message": "Not a refresh token",
                }
            },
        )
    user = current_session.get("user")
    if not user:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "ERR_USER_NOT_FOUND",
                    "message": "User context missing",
                }
            },
        )
    logger.info("--- [ END REFRESH TOKEN ] ---")
    return TokenResponse(token=create_user_tokens(user))
