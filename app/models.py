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

   