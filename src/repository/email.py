from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from jose import jwt

from src.entity.models import User
from src.conf.config import config
from src.repository.users import get_user_by_email


async def confirmed_email(email: str, db: AsyncSession) -> None:
    """
    Confirms a user's email address.

    :param email: The email address to confirm.
    :type email: str
    :param db: The database session.
    :type db: AsyncSession
    :return: None
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    await db.commit()


async def create_reset_password_token(email: str):
    """
    Creates a reset password token for a given email.

    :param email: The email address for which to create the token.
    :type email: str
    :return: A JWT token.
    :rtype: str
    """
    data = {"sub": email, "exp": datetime.now() + timedelta(minutes=10)}
    token = jwt.encode(data, config.SECRET_KEY, config.ALGORITHM)
    return token


async def create_new_password(user: User, new_password: str, db: AsyncSession):
    """
    Creates a new password for a given user.

    :param user: The user for whom to create the new password.
    :type user: User
    :param new_password: The new password.
    :type new_password: str
    :param db: The database session.
    :type db: AsyncSession
    :return: The updated user object.
    :rtype: User
    """
    user.password = new_password
    await db.commit()
    await db.refresh(user)
    return user
