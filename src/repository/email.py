from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from jose import jwt

from src.entity.models import User
from src.conf.config import config
from src.repository.users import get_user_by_email
from src.services.auth import Auth

async def confirmed_email(email: str, db: AsyncSession) -> None:
    user = await get_user_by_email(email, db)
    user.confirmed = True
    await db.commit()


async def create_reset_password_token(email: str):
    data = {"sub": email, "exp": datetime.now() + timedelta(minutes=10)}
    token = jwt.encode(data, config.SECRET_KEY, config.ALGORITHM)
    return token


async def create_new_password(user: User, new_password: str, db: AsyncSession):
    user.password = new_password
    await db.commit()
    await db.refresh(user)
    return user
