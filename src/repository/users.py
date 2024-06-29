from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libgravatar import Gravatar

from src.database.db import get_db
from src.entity.models import User
from src.dtos.user import UserSchema


async def get_user_by_email(email: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieves a user by their email address.

    :param email: The email address to search for.
    :type email: str
    :param db: The database session.
    :type db: AsyncSession
    :return: The user object if found, else None.
    :rtype: User
    """
    stmt = select(User).filter_by(email=email)
    user = await db.execute(stmt)
    return user.scalar_one_or_none()


async def create_user(body: UserSchema, db: AsyncSession = Depends(get_db)):
    """
    Creates a new user with the provided user information.

    :param body: The schema containing the user information.
    :type body: UserSchema
    :param db: The database session.
    :type db: AsyncSession
    :return: The created user object.
    :rtype: User
    """
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as error:
        print(error)

    new_user = User(**body.model_dump(), avatar=avatar)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def update_token(user: User, token: str | None, db: AsyncSession):
    """
    Updates the refresh token for a user.

    :param user: The user whose token is being updated.
    :type user: User
    :param token: The new token to set, or None to clear the token.
    :type token: str | None
    :param db: The database session.
    :type db: AsyncSession
    :return: None
    """
    user.refresh_token = token
    await db.commit()


async def update_avatar(email, url: str, db: AsyncSession) -> User:
    """
    Updates the avatar URL for a user.

    :param email: The email address of the user whose avatar is being updated.
    :type email: str
    :param url: The new avatar URL to set.
    :type url: str
    :param db: The database session.
    :type db: AsyncSession
    :return: The updated user object.
    :rtype: User
    """
    user = await get_user_by_email(email, db)
    user.avatar = url
    await db.commit()
    await db.refresh(user)
    return user
