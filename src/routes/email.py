from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.email import send_email, send_email_for_reset_password
from src.dtos.email import RequestEmail
from src.database.db import get_db
from src.services.auth import auth_service
from src.repository import users as repository_users
from src.repository import email as repository_email
from src.services.auth import Auth

router = APIRouter(prefix="/email", tags=["email"])
templates = Jinja2Templates(directory="src/templates")


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    Confirms the email address associated with the provided token.

    :param token: The verification token received via email.
    :type token: str
    :param db: The asynchronous database session.
    :type db: AsyncSession
    :return: Confirmation message upon successful email verification.
    :rtype: dict
    """

    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repository_email.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.get("/reset-password/{token}", response_class=HTMLResponse)
async def reset_password_form(request: Request, token: str):
    """
    Renders a form for resetting the user's password.

    :param request: The incoming request object.
    :type request: Request
    :param token: The password reset token received via email.
    :type token: str
    :return: HTMLResponse containing the password reset form.
    :rtype: HTMLResponse
    """

    return templates.TemplateResponse(
        "reset_password_form.html", {"request": request, "token": token}
    )


@router.post("/reset-password/{token}")
async def reset_password(
        token: str,
        new_password_1: str = Form(),
        new_password_2: str = Form(),
        db: AsyncSession = Depends(get_db),
):
    """
    Resets the user's password using the provided token and new password.

    :param request: The incoming request object.
    :type request: Request
    :param token: The password reset token received via email.
    :type token: str
    :param new_password_1: The new password to set.
    :type new_password_1: str
    :param new_password_2: The confirmation of the new password.
    :type new_password_2: str
    :param db: The asynchronous database session.
    :type db: AsyncSession
    :return: Confirmation message upon successful password reset.
    :rtype: dict
    """

    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Password Reset Payload or Reset Link Expired",
        )
    if new_password_1 != new_password_2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirm password do not match",
        )
    hashed_password = Auth.pwd_context.hash(new_password_1)
    await repository_email.create_new_password(user, hashed_password, db)
    return {"message": "Your password change"}


@router.post("/request_email")
async def request_email(
        body: RequestEmail,
        background_tasks: BackgroundTasks,
        request: Request,
        db: AsyncSession = Depends(get_db),
):
    """
    Initiates a request to verify an email address.

    :param body: The email address to be verified.
    :type body: RequestEmail
    :param background_tasks: BackgroundTasks instance to handle asynchronous tasks.
    :type background_tasks: BackgroundTasks
    :param request: The incoming request object.
    :type request: Request
    :param db: The asynchronous database session.
    :type db: AsyncSession
    :return: Confirmation message indicating that an email has been sent for verification.
    :rtype: dict
    """

    user = await repository_users.get_user_by_email(body.email, db)

    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(
            send_email, user.email, user.username, str(request.base_url), "verify_email.html"
        )
    return {"message": "Check your email for confirmation."}


@router.post("/forget-password")
async def forget_password(
        background_tasks: BackgroundTasks,
        body: RequestEmail,
        request: Request,
        db: AsyncSession = Depends(get_db),

):
    """
    Initiates a request to reset the user's forgotten password.

    :param background_tasks: BackgroundTasks instance to handle asynchronous tasks.
    :type background_tasks: BackgroundTasks
    :param body: The email address for which the password reset is requested.
    :type body: RequestEmail
    :param request: The incoming request object.
    :type request: Request
    :param db: The asynchronous database session.
    :type db: AsyncSession
    :return: Confirmation message indicating that an email has been sent for password reset.
    :rtype: dict
    """

    user = await repository_users.get_user_by_email(body.email, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NOT FOUND",
        )
    background_tasks.add_task(
        send_email_for_reset_password,
        user.email,
        user.username,
        str(request.base_url),
        "reset_password.html",
    )
    return {"message": "Check your email for reset."}
