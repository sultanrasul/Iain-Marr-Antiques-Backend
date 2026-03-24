from typing import ClassVar, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from schemas.product import Product

class PrintRequest(BaseModel):
    products: List[Product]
    mark_as_sold: bool = Field(example=True)
    copies: int = Field(example=1)

    customer_name: Optional[str] = Field(example="Sultan Rasul",default="")
    email_address: Optional[str] = Field(example="example@email.com",default="")

    date_sold: Optional[str] = Field(
        default=None,
        example="2026-03-24 14:30:00",
        description="Format: %Y-%m-%d %H:%M:%S"
    )
