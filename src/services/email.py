import os
from pathlib import Path
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from jinja2 import Template
from pydantic import EmailStr

from src.conf.config import config

from src.services.auth import auth_service
from src.repository import email as repository_email

conf = ConnectionConfig(
    MAIL_USERNAME=config.MAIL_USERNAME,
    MAIL_PASSWORD=config.MAIL_PASSWORD,
    MAIL_FROM=config.MAIL_FROM,
    MAIL_PORT=int(config.MAIL_PORT),
    MAIL_SERVER=config.MAIL_SERVER,
    MAIL_FROM_NAME="Contacts App",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent.parent/ "templates",
)

async def send_email(email: EmailStr, username: str, host: str, template_name:str):
    try:
        token_verification = auth_service.create_email_token({"sub": email})
        message = MessageSchema(
            subject="Confirm your email for Contacts App",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token_verification,
            },
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name=template_name)
    except ConnectionErrors as err:
        print(err)


async def send_email_for_reset_password(
    email: str, username: str, host: str, template_name: str
):
    try:
        token = await repository_email.create_reset_password_token(email)
        message = MessageSchema(
                subject="Reset password Contacts App",
                recipients=[email],
                template_body={
                    "host": host,
                    "username": username,
                    "token": token,
                },
                subtype=MessageType.html,
            )

        fm = FastMail(conf)
        await fm.send_message(message, template_name=template_name)
    except ConnectionErrors as err:
        print(err)

