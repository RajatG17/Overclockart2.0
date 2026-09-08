import uuid

import jwt
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPAuthorizationCredentials

from .database import get_db
from .models import User
from .security import decode_access_token, bearer_scheme

async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    token = credentials.credentials
    
    try:
        payload = decode_access_token(token)

        subject = payload.get("sub")

        if subject is None:
            raise credentials_exception

        user_id = uuid.UUID(subject)

    except (
        jwt.InvalidTokenError,
        ValueError
    ):
        raise credentials_exception

    user = await db.get(
        User, 
        user_id,
    )

    if user is None:
        raise credentials_exception

    return user
