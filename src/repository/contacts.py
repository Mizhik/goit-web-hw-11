from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime, timedelta
from src.entity.models import Contact, User
from src.dtos.contact import ContactSchema


async def get_contacts(limit: int, offset: int, user:User,db: AsyncSession):
    stmt = select(Contact).filter_by(user=user).offset(offset).limit(limit)
    contacts = await db.execute(stmt)
    return contacts.scalars().all()


async def get_contact(contact_id: int, user: User, db: AsyncSession):
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    contacts = await db.execute(stmt)
    return contacts.scalar_one_or_none()


async def create_contact(body: ContactSchema, user: User, db: AsyncSession):
    contact = Contact(**body.model_dump(exclude_unset=True), user=user)
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def update_contact(
    contact_id: int, user: User, body: ContactSchema, db: AsyncSession
):
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    contact = await db.execute(stmt)
    contact = contact.scalar_one_or_none()
    if contact:
        contact.first_name = body.first_name
        contact.last_name = body.last_name
        contact.email = body.email
        contact.phone = body.phone
        contact.date_of_birth = body.date_of_birth
        await db.commit()
        await db.refresh(contact)
    return contact


async def delete_contact(contact_id: int, user: User, db: AsyncSession):
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    contact = await db.execute(stmt)
    contact = contact.scalar_one_or_none()
    if contact:
        await db.delete(contact)
        await db.commit()
    return contact


async def search_contacts(
    filters: dict, limit: int, offset: int, user: User, db: AsyncSession
):
    stmt = select(Contact).filter_by(**filters, user=user).offset(offset).limit(limit)
    contacts = await db.execute(stmt)
    contacts = contacts.scalars().all()
    return contacts


async def get_upcoming_birthdays(db: AsyncSession, user: User):
    today = datetime.today().date()
    next_week = today + timedelta(days=7)

    stmt = select(Contact).where(
        func.to_char(Contact.date_of_birth, "MM-DD").between(
            today.strftime("%m-%d"), next_week.strftime("%m-%d")
        ),
        Contact.user_id == user.id,
    )
    result = await db.execute(stmt)
    contacts = result.scalars().all()
    return contacts


