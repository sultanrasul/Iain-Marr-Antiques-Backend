from typing import ClassVar, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class Product(BaseModel):
    row_number: Optional[int] = Field(None, example=3297)
    sku_no: str = Field(example="IMA9000000")
    im_sku: Optional[str] = Field(None, example="529-308")
    item_description: Optional[str] = Field(None, example="Fast API Testing")
    selling_price: float = Field(0.0, example=1350.0)
    quantity: int = Field(1, example=1)
    date_bought: Optional[str] = Field(None, example="28.11.22")
    seller_name_address: Optional[str] = Field(None, example="Fast-APi")
    purchase_price: float = Field(0.0, example=100.0)
    commission: float = Field(0.0, example=0.0)
    date_sold: Optional[str] = Field(None, example="30.11.22")
    invoice_no_xero: Optional[str] = Field(None, example="FASTAPI-1234")
    on_website: bool = Field(False, example=True)
    location: Optional[str] = Field(None, example="Showroom 1")
    sold: bool = Field(False, example=False)
    photograph: Optional[str] = Field(None, example="")

    # The canonical sheet headers
    SHEET_HEADERS: ClassVar[list[str]] = [
        "SKU NO.",
        "IM SKU",
        "ITEM DESCRIPTION",
        "SELLING PRICE",
        "Quantity",
        "DATE BOUGHT",
        "NAME/ADDRESS SELLER",
        "PURCHASE PRICE",
        "Commission £",
        "DATE SOLD",
        "INVOICE NO. XERO",
        "ON WEBSITE",
        "location",
        "SOLD",
        "PHOTOGRAPH",
    ]

    @classmethod
    def from_sheet_row(cls, row: dict) -> "Product":
        def safe_int(value, default=0):
            try:
                return int(value)
            except (ValueError, TypeError):
                return default

        def safe_float(value, default=0.0):
            try:
                return float(value)
            except (ValueError, TypeError):
                return default

        def safe_str(value, default=""):
            if value is None:
                return default
            return str(value)

        return cls(
            row_number=safe_int(row.get("row_number")),
            sku_no=safe_str(row.get("SKU NO.")),
            im_sku=safe_str(row.get("IM SKU")),
            item_description=safe_str(row.get("ITEM DESCRIPTION")),
            quantity=safe_int(row.get("Quantity")),
            selling_price=safe_float(row.get("SELLING PRICE")),
            date_bought=safe_str(row.get("DATE BOUGHT")),
            seller_name_address=safe_str(row.get("NAME/ADDRESS SELLER")),
            purchase_price=safe_float(row.get("PURCHASE PRICE")),
            commission=safe_float(row.get("Commission £")),
            date_sold=safe_str(row.get("DATE SOLD")),
            invoice_no_xero=safe_str(row.get("INVOICE NO. XERO")),
            on_website=row.get("ON WEBSITE") in ["TRUE", True],
            location=safe_str(row.get("location")),
            sold=row.get("SOLD") in ["TRUE", True],
            photograph=safe_str(row.get("PHOTOGRAPH")),
        )
    
    def to_sheet_row(self) -> list:
        """Convert this Product instance into a list of values in sheet order"""
        mapping = {
            "SKU NO.": self.sku_no,
            "IM SKU": self.im_sku,
            "ITEM DESCRIPTION": self.item_description,
            "SELLING PRICE": self.selling_price,
            "Quantity": self.quantity,
            "DATE BOUGHT": self.date_bought,
            "NAME/ADDRESS SELLER": self.seller_name_address,
            "PURCHASE PRICE": self.purchase_price,
            "Commission £": self.commission,
            "DATE SOLD": self.date_sold,
            "INVOICE NO. XERO": self.invoice_no_xero,
            "ON WEBSITE": "TRUE" if self.on_website else "",
            "location": self.location,
            "SOLD": True if self.sold else False,
            "PHOTOGRAPH": self.photograph,
        }
        return [mapping.get(h, "") for h in self.SHEET_HEADERS]
