from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey, func, Text
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import ARRAY
# from models.category import Category

class Base(DeclarativeBase):
    pass

class Product(Base):
    __tablename__='products'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[float] = mapped_column(nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    image_url: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    category: Mapped["Category"] = relationship(back_populates="products")



class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)

    products: Mapped[List["Product"]] = relationship(back_populates="category")

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"
    # slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    # products: Mapped["Product"] = relationship(back_populates='category', uselist=False)

