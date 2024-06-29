from datetime import datetime, date
from typing import Any
from pydantic import BaseModel, EmailStr, Field, field_validator

from src.dtos.user import UserResponse


class ContactSchema(BaseModel):
    first_name: str = Field(min_length=3, max_length=25)
    last_name: str = Field(min_length=3, max_length=50)
    email: EmailStr
    phone: str
    date_of_birth: date

    @field_validator("date_of_birth")
    def validate_date(cls, v: Any) -> date:
        if isinstance(v, date):
            return v
        try:
            return datetime.strptime(v, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD.")

    @field_validator("phone")
    def validate_phone(cls, p):
        try:
            if p.isdigit() and len(p) == 10:
                return f"+38{p}"
        except ValueError:
            raise ValueError("Invalid phone  format. Phone must be 10 digits.")


class ContactResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    date_of_birth: date
    user: UserResponse | None

    class Config:
        from_attributes = True
