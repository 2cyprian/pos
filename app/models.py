"""
╔════════════════════════════════════════════════════════════════════════════╗
║           DATABASE MODELS - ORM DEFINITIONS                                ║
║                                                                            ║
║  These classes define the structure of database tables.                    ║
║  Each class = one database table                                           ║
║  Each Column = one column in that table                                    ║
╚════════════════════════════════════════════════════════════════════════════╝
"""

from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class SystemSetting(Base):
    __tablename__ = "system_settings"

    key = Column(String, primary_key=True, index=True) # e.g., "price_bw_a4", "tax_rate"
    value = Column(String) # e.g., "0.50", "18.0"
    description = Column(String) # "Price for B&W A4 Print"
# ────────────────────────────────────────────────────────────────────────────
# MODEL 1: PRINT JOB - Customer's Document
# ────────────────────────────────────────────────────────────────────────────
# This represents a document uploaded by a customer.
# When someone uploads a PDF, a new PrintJob record is created.

class PrintJob(Base):
    """
    Represents a print job from a customer.
    
    Example record:
    ┌──────────────┬──────────────────────┐
    │ job_code     │ #4492                │  <- Customer-facing code
    │ filename     │ resume.pdf           │  <- Original file name
    │ total_pages  │ 3                    │  <- Analysis result
    │ status       │ PENDING              │  <- Current state
    │ created_at   │ 2025-12-02...        │  <- Timestamp
    └──────────────┴──────────────────────┘
    """
    __tablename__ = "print_jobs"
    
    # PRIMARY KEY - Unique identifier for this record
    id = Column(Integer, primary_key=True, index=True)
    
    # BUSINESS DATA
    # Unique 4-digit code shown to customer (e.g., #4492)
    job_code = Column(String, unique=True, index=True)
    
    # Original filename (e.g., "resume.pdf")
    filename = Column(String)
    
    # Path where file is stored on disk
    file_path = Column(String)
    
    # ANALYSIS DATA
    # Number of pages (calculated by file_analysis service)
    total_pages = Column(Integer, default=0)
    
    # Whether document contains color (for pricing)
    is_color = Column(Boolean, default=False)
    
    # WORKFLOW STATUS
    # Possible values: "PENDING", "PRINTING", "PRINTED", "COLLECTED"
    status = Column(String, default="PENDING")
    
    # When this record was created
    created_at = Column(DateTime, default=datetime.now)


# ────────────────────────────────────────────────────────────────────────────
# MODEL 2: PRODUCT - Retail Items (Pens, Staplers, etc.)
# ────────────────────────────────────────────────────────────────────────────
# For the POS system - items you sell in the shop.

class Product(Base):
    """
    Represents a retail product (inventory item).
    
    Example record:
    ┌──────────────┬─────────────────────────────────┐
    │ name         │ BIC Ballpoint Pen               │
    │ barcode      │ 3086123456789                   │
    │ price        │ 1.50                            │
    │ stock_qty    │ 250                             │
    └──────────────┴─────────────────────────────────┘
    """
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Product name
    name = Column(String, index=True)
    
    # Barcode for quick lookup/scanning
    barcode = Column(String, unique=True, index=True)
    
    # Selling price
    price = Column(Float)
    
    # Current quantity in stock
    stock_quantity = Column(Integer, default=0)


# ────────────────────────────────────────────────────────────────────────────
# MODEL 3: RAW MATERIAL - Paper, Ink, etc. (For Recipes)
# ────────────────────────────────────────────────────────────────────────────
# Materials used to fulfill print jobs.
# Example: "A4 Paper 80gsm", "Cyan Toner"

class RawMaterial(Base):
    """
    Represents raw materials used for printing.
    
    Example records:
    ┌──────────────────────┬────────┬──────────┐
    │ name                 │ type   │ level    │
    ├──────────────────────┼────────┼──────────┤
    │ A4 Paper 80gsm       │ PAPER  │ 500      │  (sheets)
    │ Cyan Toner           │ INK    │ 95       │  (percentage)
    │ Black Ink Bottle     │ INK    │ 3        │  (bottles)
    └──────────────────────┴────────┴──────────┘
    """
    __tablename__ = "raw_materials"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Material name (e.g., "A4 Paper 80gsm")
    name = Column(String)
    
    # Type: "PAPER" or "INK"
    type = Column(String)
    
    # Current quantity/level (sheets, percentage, bottles, etc.)
    current_level = Column(Float, default=0)

# Links a Service (like "Color Print") to Raw Materials
class ProductionRecipe(Base):
    __tablename__ = "production_recipes"
    
    id = Column(Integer, primary_key=True)
    service_type = Column(String) # e.g., "PRINT_BW_A4", "PRINT_COLOR_A4", "BINDING_SPIRAL"
    
    # Material to Deduct
    raw_material_id = Column(Integer, ForeignKey("raw_materials.id"))
    quantity_required = Column(Float) # e.g., 1.0 (Sheet) or 0.05 (Ink)
    
    material = relationship("RawMaterial")

# ────────────────────────────────────────────────────────────────────────────
# MODEL 4: PRINTER - Hardware Devices
# ────────────────────────────────────────────────────────────────────────────
# Physical printer machines connected to the network.

class Printer(Base):
    """
    Represents a physical printer device.
    
    Example record:
    ┌──────────────────────┬──────────────────┐
    │ name                 │ Epson L3110      │
    │ ip_address           │ 192.168.1.50     │
    │ total_page_cnt       │ 87432            │  (lifetime pages)
    └──────────────────────┴──────────────────┘
    """
    __tablename__ = "printers"
    
    id = Column(Integer, primary_key=True)
    
    # Printer model name (e.g., "Epson L3110")
    name = Column(String)
    
    # IP address on the network (e.g., "192.168.1.50")
    # Used for SNMP queries and direct printing
    ip_address = Column(String)
    
    # Total pages printed (from printer's hardware counter)
    # Updated via SNMP queries
    total_page_counter = Column(Integer, default=0)
    
    # Relationship to logs
    logs = relationship("PrinterLog", back_populates="printer")


# MODEL 4B: PRINTER LOG - Printer Activity History
class PrinterLog(Base):
    """
    Tracks printer activity and page counter changes over time.
    Stores historical data when printer watchdog updates counters.
    
    Example records:
    ┌────────────┬──────────┬─────────────────────┐
    │ printer_id │ pages    │ timestamp           │
    ├────────────┼──────────┼─────────────────────┤
    │ 1          │ 87432    │ 2025-12-21 10:00:00 │
    │ 1          │ 87445    │ 2025-12-21 11:00:00 │
    │ 1          │ 87458    │ 2025-12-21 12:00:00 │
    └────────────┴──────────┴─────────────────────┘
    """
    __tablename__ = "printer_logs"
    
    id = Column(Integer, primary_key=True)
    
    # Reference to the printer
    printer_id = Column(Integer, ForeignKey("printers.id"))
    
    # Page counter value at this point in time
    page_count = Column(Integer)
    
    # When this log entry was recorded
    recorded_at = Column(DateTime, default=datetime.now)
    
    # Additional info: pages printed since last check, status, etc.
    notes = Column(String, nullable=True)
    
    # Relationship back to printer
    printer = relationship("Printer", back_populates="logs")


# 5. SALES ORDER (The Receipt)
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    total_amount = Column(Float, default=0.0)
    payment_method = Column(String, default="CASH") # CASH, M-PESA
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationship to items
    items = relationship("OrderItem", back_populates="order")

# 6. ORDER ITEMS (Details of what was sold)
class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    
    # What did they buy?
    product_name = Column(String) # Snapshot of name at time of sale
    quantity = Column(Integer)
    unit_price = Column(Float) # Snapshot of price
    
    # Type: "RETAIL" (Pen) or "SERVICE" (Print Job)
    item_type = Column(String) 
    
    order = relationship("Order", back_populates="items")

   
# ────────────────────────────────────────────────────────────────────────────
# MODEL 7: BRANCH - Business Locations
# ────────────────────────────────────────────────────────────────────────────
class Branch(Base):
    """
    Represents a branch or location of the business.
    Owner can create multiple branches, each managed by staff.
    """
    __tablename__ = "branches"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Branch name (e.g., "Downtown Store", "Mall Outlet")
    name = Column(String, index=True)
    
    # Location address
    location = Column(String)
    
    # Contact phone
    phone = Column(String, nullable=True)
    
    # Owner ID (who created this branch)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # When branch was created
    created_at = Column(DateTime, default=datetime.now)
    
    # Active or inactive
    is_active = Column(Boolean, default=True)
    
    # Relationship to staff assigned to this branch
    staff = relationship("User", back_populates="branch", foreign_keys="User.branch_id")
    owner = relationship("User", back_populates="owned_branches", foreign_keys=[owner_id])


# ────────────────────────────────────────────────────────────────────────────
# MODEL 8: USER / STAFF - Authentication & Roles
# ────────────────────────────────────────────────────────────────────────────
class User(Base):
    """
    Represents a staff member or owner.
    Roles: "OWNER" or "STAFF"
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Username for login
    username = Column(String, unique=True, index=True)
    
    # Email
    email = Column(String, unique=True, index=True)
    
    # Phone number (optional)
    phone = Column(String, nullable=True)
    
    # Hashed password (use bcrypt in production)
    password_hash = Column(String)
    
    # Role: "OWNER" or "STAFF"
    role = Column(String, default="STAFF")  # OWNER, STAFF
    
    # If STAFF, which branch are they assigned to?
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    
    # Active or inactive
    is_active = Column(Boolean, default=True)
    
    # When user was created
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    branch = relationship("Branch", back_populates="staff", foreign_keys=[branch_id])
    owned_branches = relationship("Branch", back_populates="owner", foreign_keys="Branch.owner_id")
    
    # Each staff can have permissions
    permissions = relationship("Permission", back_populates="user")


# ────────────────────────────────────────────────────────────────────────────
# MODEL 9: PERMISSION - Fine-grained access control
# ────────────────────────────────────────────────────────────────────────────
class Permission(Base):
    """
    Represents what actions a user can perform.
    Example: can_create_product, can_view_reports, can_refund
    """
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User who has this permission
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Permission name (e.g., "view_reports", "create_product", "refund_order")
    permission_name = Column(String, index=True)
    
    # When permission was granted
    granted_at = Column(DateTime, default=datetime.now)
    
    # Relationship
    user = relationship("User", back_populates="permissions")