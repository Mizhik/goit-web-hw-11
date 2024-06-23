from urllib import request
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi_mail import MessageSchema, MessageType
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User
from src.services.email import send_email, send_email_for_reset_password
from src.dtos.email import RequestEmail,ResetForegetPassword
from src.database.db import get_db
from src.services.auth import auth_service
from src.repository import users as repository_users
from src.repository import email as repository_email
from src.services.auth import Auth

router = APIRouter(prefix="/email", tags=["email"])
templates = Jinja2Templates(directory="src/templates")

@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
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
    return templates.TemplateResponse(
        "reset_password_form.html", {"request": request, "token": token}
    )


@router.post("/reset-password/{token}")
async def reset_password(
    request: Request,
    token: str,
    new_password_1: str = Form(),
    new_password_2: str = Form(),
    db: AsyncSession = Depends(get_db),
):
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
    user = await repository_users.get_user_by_email(body.email, db)

    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(
            send_email, user.email, user.username, str(request.base_url),"verify_email.html"
        )
    return {"message": "Check your email for confirmation."}


@router.post("/forget-password")
async def forget_password(
    background_tasks: BackgroundTasks,
    body: RequestEmail,
    request: Request,
    db: AsyncSession = Depends(get_db),

):
    user = await repository_users.get_user_by_email(body.email,db)
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
