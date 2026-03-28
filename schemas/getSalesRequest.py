from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class GetSalesRequest(BaseModel):
    # Query parameters for filtering sales
    order_id: Optional[int] = Field(None, example=123)
    customer_id: Optional[int] = Field(None, example=456)
    date_from: Optional[datetime] = Field(None, example="2023-01-01T00:00:00")
    date_to: Optional[datetime] = Field(None, example="2023-12-31T23:59:59")
    min_items: Optional[int] = Field(None, example=5)
    min_price: Optional[float] = Field(None, example=100.0)

    # Optional customer-related information
    customer_name: Optional[str] = Field(default="", example="Sultan Rasul")
    email_address: Optional[str] = Field(default="", example="example@email.com")


    # --- Sorting parameters ---
    sort_field: Optional[Literal[
        'date_sold', 'order_id', 'customer_name', 'items_purchased', 'total_amount'
    ]] = Field(
        None,
        description="Field to sort by: date_sold, order_id, customer_name, items_purchased, total_amount"
    )

    sort_order: Optional[Literal['asc', 'desc']] = Field('asc', description="Sort order: 'asc' for ascending, 'desc' for descending")