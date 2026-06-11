from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class GetAccountAnotherUser(BaseModel):
    id_user: int
    new_lvl_access: int 

class GetAccountAnotherUserEmail(BaseModel):
    id_user: int
    new_email: EmailStr
class ResponseId (BaseModel):
    id_user: int

class AdminStatusResponse(BaseModel):
    ok: bool

    # product_id: int
    # name: str = Field(..., description="Product name")
    # price: float = Field(..., description="Product price")
    # quantity: int = Field(..., description="Quantity in cart")
    # subtotal: float = Field(...,
    #                     description="Total price for this item (price * quantity)")
    # image_url: Optional[str] = Field(None, description="Product image URL")