from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .models import User
from .schemas import RegisterRequest, UserResponse, LoginRequest, TokenResponse
from .security import hash_password, create_access_token, verify_password

from .dependencies import get_current_user


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> User:
    result = await db.execute(
        select(User).where(User.email==payload.email)
    )

    existing_user = result.scalar_one_or_none()

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password)
    )

    db.add(user)

    await db.commit()
    await db.refresh(user)

    return user

@router.post(
    "/login",
    response_model=TokenResponse
)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    result = await db.execute(
        select(User).where(User.email == payload.email)
    )

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )

    access_token= create_access_token(str(user.id))

    return TokenResponse(
        access_token=access_token
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user

