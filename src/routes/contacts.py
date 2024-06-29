from fastapi import APIRouter, HTTPException, Depends, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.repository import contacts as repositories_contacts
from src.dtos.contact import ContactResponse, ContactSchema

from fastapi_limiter.depends import RateLimiter

from src.entity.models import User
from src.services.auth import auth_service

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/upcoming_birthdays", response_model=list[ContactResponse])
async def upcoming_birthdays(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """
    Retrieves upcoming birthdays of contacts for the authenticated user.

    :param db: The asynchronous database session.
    :type db: AsyncSession
    :param user: The authenticated user.
    :type user: User
    :return: A list of ContactResponse objects representing contacts with upcoming birthdays.
    :rtype: list[ContactResponse]
    """

    contacts = await repositories_contacts.get_upcoming_birthdays(db, user)
    return contacts


@router.get("/search", response_model=list[ContactResponse])
async def search_contacts(
    first_name: str = None,
    last_name: str = None,
    email: str = None,
    limit: int = Query(10, ge=10, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """
    Searches contacts based on optional filters such as first name, last name, and email.

    :param first_name: First name of the contact to search.
    :type first_name: str
    :param last_name: Last name of the contact to search.
    :type last_name: str
    :param email: Email address of the contact to search.
    :type email: str
    :param limit: Maximum number of contacts to return (default 10, minimum 10, maximum 500).
    :type limit: int
    :param offset: Number of contacts to skip before starting to return results (default 0).
    :type offset: int
    :param db: The asynchronous database session.
    :type db: AsyncSession
    :param user: The authenticated user.
    :type user: User
    :return: A list of ContactResponse objects matching the search criteria.
    :rtype: list[ContactResponse]
    """

    filters = {}
    if first_name:
        filters["first_name"] = first_name
    if last_name:
        filters["last_name"] = last_name
    if email:
        filters["email"] = email

    contacts = await repositories_contacts.search_contacts(filters, limit, offset,user, db)
    if contacts is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return contacts


@router.get(
    "/",
    response_model=list[ContactResponse],
)
async def get_contacts(
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user)
):
    """
    Retrieves a list of contacts with pagination.

    :param limit: Maximum number of contacts to return.
    :type limit: int
    :param offset: Number of contacts to skip before starting to return results.
    :type offset: int
    :param db: The asynchronous database session.
    :type db: AsyncSession
    :param user: The authenticated user.
    :type user: User
    :return: A list of ContactResponse objects.
    :rtype: list[ContactResponse]
    """

    contacts = await repositories_contacts.get_contacts(limit, offset, user, db)
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(contact_id: int = Path(ge=1), db: AsyncSession = Depends(get_db),user: User = Depends(auth_service.get_current_user)):
    """
    Retrieves details of a specific contact by ID.

    :param contact_id: The ID of the contact to retrieve.
    :type contact_id: int
    :param db: The asynchronous database session.
    :type db: AsyncSession
    :param user: The authenticated user.
    :type user: User
    :return: Details of the requested contact.
    :rtype: ContactResponse
    """

    contact = await repositories_contacts.get_contact(contact_id, user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return contact


@router.post(
    "/",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=1, seconds=20))],
)
async def create_contact(
    body: ContactSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """
    Creates a new contact.

    :param body: The contact data to create.
    :type body: ContactSchema
    :param db: The asynchronous database session.
    :type db: AsyncSession
    :param user: The authenticated user.
    :type user: User
    :return: Details of the created contact.
    :rtype: ContactResponse
    """

    contact = await repositories_contacts.create_contact(body, user, db)
    return contact


@router.put("/{contact_id}")
async def update_contact(
    contact_id: int,
    body: ContactSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """
    Updates an existing contact.

    :param contact_id: The ID of the contact to update.
    :type contact_id: int
    :param body: The updated contact data.
    :type body: ContactSchema
    :param db: The asynchronous database session.
    :type db: AsyncSession
    :param user: The authenticated user.
    :type user: User
    :return: Details of the updated contact.
    :rtype: ContactResponse
    """
    contact = await repositories_contacts.update_contact(contact_id, user, body, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """
    Deletes a contact by ID.

    :param contact_id: The ID of the contact to delete.
    :type contact_id: int
    :param db: The asynchronous database session.
    :type db: AsyncSession
    :param user: The authenticated user.
    :type user: User
    """

    contact = await repositories_contacts.delete_contact(contact_id, user, db)
    return contact
