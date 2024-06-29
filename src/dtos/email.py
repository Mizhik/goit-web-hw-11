from pydantic import BaseModel, EmailStr


class RequestEmail(BaseModel):
    email: EmailStr


class ResetForegetPassword(BaseModel):
    new_password: str
    confirm_password: str

