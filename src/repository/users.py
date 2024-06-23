from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libgravatar import Gravatar

from src.database.db import get_db
from src.entity.models import User
from src.dtos.user import UserSchema

async def get_user_by_email(email:str, db:AsyncSession = Depends(get_db)):
    stmt = select(User).filter_by(email = email)
    user = await db.execute(stmt)
    return user.scalar_one_or_none()

async def create_user(body: UserSchema, db: AsyncSession = Depends(get_db)):
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

async def update_token(user:User, token:str|None, db: AsyncSession):
    user.refresh_token = token
    await db.commit()

async def update_avatar(email, url: str, db: AsyncSession) -> User:
    user = await get_user_by_email(email, db)
    user.avatar = url
    await db.commit()
    await db.refresh(user)
    return user
