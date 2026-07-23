from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey, func, Text
from typing import List, Optional
from datetime import datetime

from .base import Base

class Errors (Base):
    __tablename__='errors'
    tid: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    error_text: Mapped[str] = mapped_column(Text)
    endpont: Mapped[str] = mapped_column(String(100))
    method: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())