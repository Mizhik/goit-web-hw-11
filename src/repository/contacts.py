from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime, timedelta
from src.entity.models import Contact, User
from src.dtos.contact import ContactSchema


async def get_contacts(limit: int, offset: int, user: User, db: AsyncSession):
    """
    Retrieves a list of contacts for a specific user with pagination.

    :param limit: The maximum number of contacts to return.
    :type limit: int
    :param offset: The number of contacts to skip before starting to collect the return values.
    :type offset: int
    :param user: The user whose contacts are being retrieved.
    :type user: User
    :param db: The database session.
    :type db: AsyncSession
    :return: A list of contact objects.
    :rtype: List[Contact]
    """
    stmt = select(Contact).filter_by(user=user).offset(offset).limit(limit)
    contacts = await db.execute(stmt)
    return contacts.scalars().all()


async def get_contact(contact_id: int, user: User, db: AsyncSession):
    """
    Retrieves a specific contact by its ID for a specific user.

    :param contact_id: The ID of the contact to retrieve.
    :type contact_id: int
    :param user: The user whose contact is being retrieved.
    :type user: User
    :param db: The database session.
    :type db: AsyncSession
    :return: The contact object if found, else None.
    :rtype: Contact
    """
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    contacts = await db.execute(stmt)
    return contacts.scalar_one_or_none()


async def create_contact(body: ContactSchema, user: User, db: AsyncSession):
    """
    Creates a new contact for a specific user.

    :param body: The schema containing the contact information.
    :type body: ContactSchema
    :param user: The user to whom the contact belongs.
    :type user: User
    :param db: The database session.
    :type db: AsyncSession
    :return: The created contact object.
    :rtype: Contact
    """
    contact = Contact(**body.model_dump(exclude_unset=True), user=user)
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def update_contact(
        contact_id: int, user: User, body: ContactSchema, db: AsyncSession
):
    """
    Updates an existing contact for a specific user.

    :param contact_id: The ID of the contact to update.
    :type contact_id: int
    :param user: The user whose contact is being updated.
    :type user: User
    :param body: The schema containing the updated contact information.
    :type body: ContactSchema
    :param db: The database session.
    :type db: AsyncSession
    :return: The updated contact object if found, else None.
    :rtype: Contact
    """
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
    """
    Deletes a specific contact by its ID for a specific user.

    :param contact_id: The ID of the contact to delete.
    :type contact_id: int
    :param user: The user whose contact is being deleted.
    :type user: User
    :param db: The database session.
    :type db: AsyncSession
    :return: The deleted contact object if found, else None.
    :rtype: Contact
    """
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
    """
    Searches for contacts using specific filters with pagination.

    :param filters: The dictionary of filters to apply.
    :type filters: dict
    :param limit: The maximum number of contacts to return.
    :type limit: int
    :param offset: The number of contacts to skip before starting to collect the return values.
    :type offset: int
    :param user: The user whose contacts are being searched.
    :type user: User
    :param db: The database session.
    :type db: AsyncSession
    :return: A list of contact objects that match the filters.
    :rtype: List[Contact]
    """
    stmt = select(Contact).filter_by(**filters, user=user).offset(offset).limit(limit)
    contacts = await db.execute(stmt)
    contacts = contacts.scalars().all()
    return contacts


async def get_upcoming_birthdays(db: AsyncSession, user: User):
    """
    Retrieves contacts with upcoming birthdays within the next week for a specific user.

    :param db: The database session.
    :type db: AsyncSession
    :param user: The user whose contacts' birthdays are being retrieved.
    :type user: User
    :return: A list of contact objects with upcoming birthdays.
    :rtype: List[Contact]
    """
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
