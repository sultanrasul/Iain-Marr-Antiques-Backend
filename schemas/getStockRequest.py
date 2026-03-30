# schemas/stock.py
from typing import Literal, Optional
from pydantic import BaseModel, Field

class GetStockRequest(BaseModel):
    """
    Schema for filtering stock/products with optional sorting
    """

    sku_text: Optional[str] = Field(None, example="12345", description="The SKU number or IM SKU to search for")

    description: Optional[str] = Field(None, example="Blue Widget", description="Partial or full item description")
    
    min_selling_price: Optional[float] = Field(None, example=10.50, description="Minimum selling price")

    min_purchase_price: Optional[float] = Field(None, example=5.25, description="Minimum purchase price")

    page: Optional[int] = Field(None, example=1, description="Which page you want to fetch")
    items_per_page: Optional[int] = Field(None, example=50, description="How many items per page")

    # --- Sorting parameters ---
    sort_field: Optional[Literal[
        'sku_no', 'im_sku', 'description', 'quantity', 'selling_price', 'purchase_price'
    ]] = Field(
        None,
        description="Field to sort by: sku_no, im_sku, description, quantity, selling_price, or purchase_price"
    )

    sort_order: Optional[Literal['asc', 'desc']] = Field('asc', description="Sort order: 'asc' for ascending, 'desc' for descending"
)