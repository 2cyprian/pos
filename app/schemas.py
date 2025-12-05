from pydantic import BaseModel
from typing import List, Optional



# --- ADMIN SETTINGS SCHEMAS ---
class SettingBase(BaseModel):
    key: str
    value: str
    description: Optional[str] = None

class SettingCreate(SettingBase):
    pass

class SettingResponse(SettingBase):
    class Config:
        from_attributes = True

# --- PRINTER CONFIG SCHEMAS ---
class PrinterBase(BaseModel):
    name: str
    ip_address: str

class PrinterCreate(PrinterBase):
    pass

class PrinterResponse(PrinterBase):
    id: int
    total_page_counter: int
    class Config:
        from_attributes = True

# --- RECIPE SCHEMAS (For Dynamic Inventory) ---
class RecipeCreate(BaseModel):
    service_type: str        # e.g. "PRINT_COLOR_A4"
    raw_material_id: int     # e.g. 1 (Paper)
    quantity_required: float # e.g. 1.0
# --- INVENTORY SCHEMAS ---
class ProductBase(BaseModel):
    name: str
    barcode: str
    price: float
    stock_quantity: int

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    class Config:
        from_attributes = True

# --- CHECKOUT SCHEMAS ---
class CartItem(BaseModel):
    type: str  # "PRODUCT" or "PRINT_JOB"
    id: str    # Product Barcode OR Job Code (e.g., "#4492")
    quantity: int = 1

class CheckoutRequest(BaseModel):
    payment_method: str = "CASH"
    items: List[CartItem]