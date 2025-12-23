from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime



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

# --- USER / AUTHENTICATION SCHEMAS ---
class UserBase(BaseModel):
    username: str
    email: str
    phone: Optional[str] = None
    role: str = "STAFF"  # OWNER or STAFF

class UserCreate(UserBase):
    password: str
    # Optional branch assignment at creation
    branch_id: Optional[int] = None

class UserUpdate(BaseModel):
    # Fields allowed to update for a staff member
    branch_id: Optional[int] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class OwnerRegister(BaseModel):
    """Schema for owner registration - role is auto-set"""
    username: str
    email: str
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    phone: Optional[str] = None
    branch_id: Optional[int] = None
    created_at: datetime
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class PasswordUpdate(BaseModel):
    new_password: str

# --- BRANCH SCHEMAS ---
class BranchBase(BaseModel):
    name: str
    location: str
    phone: Optional[str] = None

class BranchCreate(BranchBase):
    pass

class BranchResponse(BranchBase):
    id: int
    owner_id: int
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

# --- PERMISSION SCHEMAS ---
class PermissionBase(BaseModel):
    permission_name: str

class PermissionResponse(PermissionBase):
    id: int
    user_id: int
    granted_at: datetime
    class Config:
        from_attributes = True