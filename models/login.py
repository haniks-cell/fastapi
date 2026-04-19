import uuid

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey, func, Text
from typing import List, Optional

from .base import Base

class Users(Base):
    __tablename__='users'
    tid: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    username: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    hash_password: Mapped[str] = mapped_column(Text)
    email: Mapped[str] = mapped_column(String(40))
    lvl_access: Mapped[int] = mapped_column(index=True)

    refresh: Mapped["RefreshTokens"] = relationship(back_populates="user", uselist=False)



class RefreshTokens(Base):
    __tablename__='refresh_tokens'
    tid: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.tid"))
    uuid: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[int] = mapped_column(index=True)

    user: Mapped["Users"] = relationship(back_populates="refresh", uselist=False)
    # name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    # description: Mapped[str] = mapped_column(Text)
    # price: Mapped[float] = mapped_column(nullable=False)
    # category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    # image_url: Mapped[str] = mapped_column(Text, nullable=True)
    # created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    # # category: Mapped["Category"] = relationship(back_populates="products")