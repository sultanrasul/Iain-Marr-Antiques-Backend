from typing import ClassVar, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from schemas.product import Product

class SoldProduct(Product):
    customer_name: Optional[str] = Field(None, example="Marion Morrison-Boyd")
    total_price: float = Field(0.0, example=1350.0)

    SHEET_HEADERS: ClassVar[list[str]] = [
        "SKU NO.",
        "IM SKU",
        "Customers Name",
        "ITEM DESCRIPTION",
        "SELLING PRICE",
        "Quantity",
        "TOTAL PRICE",
        "DATE BOUGHT",
        "NAME/ADDRESS SELLER",
        "PURCHASE PRICE",
        "Commission £",
        "DATE SOLD",
        "INVOICE NO. XERO",
        "ON WEBSITE",
        "location",
        "SOLD",
    ]

    @classmethod
    def from_sheet_row(cls, row: dict) -> "SoldProduct":
        """
        Build SoldProduct from a sheet row (dict). Includes customer_name.
        """
        product = Product.from_sheet_row(row)
        return cls(
            **product.model_dump(),  # copy all Product fields
            customer_name=row.get("Customers Name")
        )

    @classmethod
    def from_product( cls, product: Product, *, customer_name: str, date_sold: Optional[str] = None, quantity: Optional[int] = None, total_price: Optional[float] = None) -> "SoldProduct":
        """
        Factory method to create a SoldProduct from a Product.
        Only specify SoldProduct-specific fields here.
        """
        data = product.model_dump(exclude={"date_sold", "quantity", "sold", "total_price"})
        return cls(
            **data,
            customer_name=customer_name,
            date_sold=date_sold or datetime.now().strftime("%-d.%-m.%y %H:%M"),
            total_price = total_price if total_price is not None else product.quantity * product.selling_price,
            quantity=quantity if quantity is not None else product.quantity,
            sold=True
        )


    def to_sheet_row(self) -> list:
        """
        Convert SoldProduct instance into a row for the sold_items sheet.
        """
        mapping = {
            "SKU NO.": self.sku_no,
            "IM SKU": self.im_sku,
            "Customers Name": self.customer_name,
            "ITEM DESCRIPTION": self.item_description,
            "SELLING PRICE": self.selling_price,
            "Quantity": self.quantity,
            "TOTAL PRICE": self.total_price,
            "DATE BOUGHT": self.date_bought,
            "NAME/ADDRESS SELLER": self.seller_name_address,
            "PURCHASE PRICE": self.purchase_price,
            "Commission £": self.commission,
            "DATE SOLD": self.date_sold,
            "INVOICE NO. XERO": self.invoice_no_xero,
            "ON WEBSITE": "TRUE" if self.on_website else "",
            "location": self.location,
            "SOLD": True,
        }
        return [mapping.get(h, "") for h in self.SHEET_HEADERS]
