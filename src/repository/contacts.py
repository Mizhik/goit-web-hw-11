from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from datetime import date, datetime, timedelta
from src.entity.models import Contact
from src.dtos.dto import ContactSchema


async def get_contacts(limit: int, offset: int, db: AsyncSession):
    stmt = select(Contact).offset(offset).limit(limit)
    contacts = await db.execute(stmt)
    return contacts.scalars().all()


async def get_contact(contact_id: int, db: AsyncSession):
    stmt = select(Contact).filter_by(id=contact_id)
    contacts = await db.execute(stmt)
    return contacts.scalar_one_or_none()


async def create_contact(body: ContactSchema, db: AsyncSession):
    contact = Contact(**body.model_dump(exclude_unset=True))
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def update_contact(contact_id: int, body: ContactSchema, db: AsyncSession):
    stmt = select(Contact).filter_by(id=contact_id)
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


async def delete_contact(contact_id: int, db: AsyncSession):
    stmt = select(Contact).filter_by(id=contact_id)
    contact = await db.execute(stmt)
    contact = contact.scalar_one_or_none()
    if contact:
        await db.delete(contact)
        await db.commit()
    return contact


async def search_contacts(filters: dict, limit: int, offset: int, db: AsyncSession):
    stmt = select(Contact).filter_by(**filters).offset(offset).limit(limit)
    contacts = await db.execute(stmt)
    contacts = contacts.scalars().all()
    return contacts


async def get_upcoming_birthdays(db: AsyncSession):
    today = datetime.today().date()
    next_week = today + timedelta(days=7)

    stmt = select(Contact).where(
        and_(
            func.to_char(Contact.date_of_birth, "MM-DD").between(
                today.strftime("%m-%d"), next_week.strftime("%m-%d")
            )
        )
    )

    result = await db.execute(stmt)
    contacts = result.scalars().all()
    return contacts
