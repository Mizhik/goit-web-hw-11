from fastapi import APIRouter, File, HTTPException, Depends, UploadFile, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

import cloudinary
import cloudinary.uploader

from src.conf.config import config
from src.entity.models import User
from src.services.email import send_email
from src.database.db import get_db
from src.repository import users as repository_users
from src.dtos.user import UserResponse, UserSchema, TokenSchema
from src.services.auth import auth_service

router = APIRouter(prefix='/auth', tags=['auth'])
get_refresh_token = HTTPBearer()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserSchema, btask: BackgroundTasks, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Registers a new user with the provided user data.

    :param body: User registration data including email and password.
    :type body: UserSchema
    :param btask: BackgroundTasks instance to handle asynchronous tasks.
    :type btask: BackgroundTasks
    :param request: The incoming request object.
    :type request: Request
    :param db: The asynchronous database session.
    :type db: AsyncSession
    :return: Details of the newly created user.
    :rtype: UserResponse
    """

    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)
    btask.add_task(
        send_email,
        new_user.email,
        new_user.username,
        str(request.base_url),
        "verify_email.html",
    )
    return new_user


@router.post("/login", response_model=TokenSchema)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """
    Logs in a user and returns an access token and a refresh token.

    :param body: OAuth2PasswordRequestForm containing user credentials (username and password).
    :type body: OAuth2PasswordRequestForm
    :param db: The asynchronous database session.
    :type db: AsyncSession
    :return: Access token and refresh token for the logged-in user.
    :rtype: TokenSchema
    """

    user = await repository_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email")
    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed")
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/refresh_token", response_model=TokenSchema)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(get_refresh_token),
                        db: AsyncSession = Depends(get_db)):
    """
    Refreshes the access token using the provided refresh token.

    :param credentials: HTTPAuthorizationCredentials containing the refresh token.
    :type credentials: HTTPAuthorizationCredentials
    :param db: The asynchronous database session.
    :type db: AsyncSession
    :return: Refreshed access token and new refresh token.
    :rtype: TokenSchema
    """

    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repository_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.patch("/avatar", response_model=UserResponse)
async def update_avatar_user(
        file: UploadFile = File(),
        current_user: User = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """
    Updates the avatar (profile picture) of the current user.

    :param file: UploadFile containing the image file for the new avatar.
    :type file: UploadFile
    :param current_user: The authenticated user whose avatar is being updated.
    :type current_user: User
    :param db: The asynchronous database session.
    :type db: AsyncSession
    :return: Updated details of the user with the new avatar URL.
    :rtype: UserResponse
    """

    cloudinary.config(
        cloud_name=config.CLD_NAME,
        api_key=config.CLD_API_KEY,
        api_secret=config.CLD_API_SECRET_KEY,
        secure=True,
    )

    r = cloudinary.uploader.upload(
        file.file, public_id=f"NotesApp/{current_user.username}", overwrite=True
    )
    src_url = cloudinary.CloudinaryImage(f"NotesApp/{current_user.username}").build_url(
        width=250, height=250, crop="fill", version=r.get("version")
    )
    user = await repository_users.update_avatar(current_user.email, src_url, db)
    return user
