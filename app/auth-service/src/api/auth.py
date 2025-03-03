from argon2 import PasswordHasher
from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel, EmailStr
from src.api.dependencies import get_email_verifier
from src.db.models.user import User
from src.api.dependencies import get_user_repository
from src.db.repositories.user_repository import UserRepository
from src.services.email_verification import EmailVerifier

router = APIRouter(prefix="/auth", tags=["auth"])
ph = PasswordHasher()


class UserRegisterSchema(BaseModel):
    username: str
    email: EmailStr
    password: str


class ConfirmEmailSchema(BaseModel):
    token: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def user_register(
        user_data: UserRegisterSchema = Body(...),
        user_repo: UserRepository = Depends(get_user_repository),
        email_verifier: EmailVerifier = Depends(get_email_verifier)
):
    existing_user = await user_repo.get_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    existing_email = await user_repo.get_by_email(user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )

    hashed_password = ph.hash(user_data.password)

    user = User(
        username=user_data.username,
        email=user_data.email,
        password=hashed_password,
        is_active=False,
    )

    await user_repo.create(user)
    await email_verifier.send_verification_email(user.email)

    return {"message": "User registered successfully"}


@router.post("/confirm-email")
async def confirm_email(
        data: ConfirmEmailSchema,
        user_repo: UserRepository = Depends(get_user_repository),
        email_verifier: EmailVerifier = Depends(get_email_verifier),
):
    email = await email_verifier.verify_token(data.token)

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token",
        )

    user = await user_repo.get_by_email(email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.is_active = True
    await user_repo.update(user)

    return {"message": "Email confirmed successfully"}
