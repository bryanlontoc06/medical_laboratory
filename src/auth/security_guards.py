from typing import Annotated, Any, Optional

import jwt
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from db.database import get_db
from src import models

# 1. Configuration & Schemes
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)

SECRET_KEY = settings.secret_key.get_secret_value()
ALGORITHM = settings.ALGORITHM


# 2. GUARD 1: API Key Check (The Entry Gate)
async def verify_api_key(
    api_key: str = Security(api_key_header), db: AsyncSession = Depends(get_db)
):
    logger.info("START VERIFY API KEY")
    logger.info(f"API Key: {api_key}")

    result = await db.execute(select(models.User).where(models.User.uid == api_key))
    user = result.scalar_one_or_none()

    if user is None:
        logger.warning(f"User not found for the given API key: {api_key}")
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "ERR_UNAUTHORIZED", "message": "Unauthorized"}},
        )
    logger.info("END VERIFY API KEY")
    return user


# 3. GUARD 2: JWT Check (The Session Guard)
def get_current_user(
    token: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
    api_user: models.User = Depends(verify_api_key),
) -> dict[str, Any]:
    if token is None:
        logger.warning("Invalid Token")
        raise HTTPException(
            status_code=401,
            detail={"error": {"code": "ERR_UNAUTHORIZED", "message": "Unauthorized"}},
        )
    try:
        payload = jwt.decode(
            token.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        return {**payload, "user": api_user}

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {"code": "ERR_TOKEN_EXPIRED", "message": "Token has expired"}
            },
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail={"error": {"code": "ERR_INVALID_TOKEN", "message": "Invalid token"}},
        )


# 4. GUARD 3: Member Check (The Anti-Guest Guard)
def require_member_role(
    api_user: models.User = Depends(verify_api_key),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    if str(api_user.uid) == str(settings.GUEST_UID):
        raise HTTPException(
            status_code=403,
            detail={
                "error": {
                    "code": "ERR_UNAUTHORIZED",
                    "message": "Unauthorized: This action requires a registered member account.",
                }
            },
        )
    return current_user
