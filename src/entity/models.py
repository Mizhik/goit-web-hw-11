from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column,relationship
from sqlalchemy import Integer,ForeignKey,String, Date, DateTime, func

from datetime import date

class Base(DeclarativeBase):
    pass


class Contact(Base):
    __tablename__ = "contacts"
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(25), index=True)
    last_name: Mapped[str] = mapped_column(String(50), index=True)
    email: Mapped[str] = mapped_column(String(100),unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(13),unique=True)
    date_of_birth: Mapped[Date] = mapped_column(Date)
    create_at:Mapped[date] = mapped_column('created_at', DateTime, default=func.now())
    update_at: Mapped[date] = mapped_column("update_at", DateTime, default=func.now(), onupdate=func.now())

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship("User", backref="contacts", lazy="joined")

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username:Mapped[str] = mapped_column(String(50))
    email:Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    password:Mapped[str] = mapped_column(String(255), nullable=False)
    avatar:Mapped[str] = mapped_column(String(255), nullable=True)
    refresh_token:Mapped[str] = mapped_column(String(255), nullable=True)
    create_at:Mapped[date] = mapped_column('created_at', DateTime, default=func.now())
    update_at: Mapped[date] = mapped_column("update_at", DateTime, default=func.now(), onupdate=func.now())
