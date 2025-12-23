from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas

router = APIRouter()

# 0. Fetch All Products
@router.get("/products/", response_model=list[schemas.ProductResponse])
def get_all_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Fetch all products with pagination"""
    products = db.query(models.Product).offset(skip).limit(limit).all()
    return products

# 0B. Fetch Product by ID
@router.get("/products/{product_id}", response_model=schemas.ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Fetch a specific product by ID"""
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# 1. Create New Product (Staff adds "Bic Pen")
@router.post("/products/", response_model=schemas.ProductResponse)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    # Check if barcode exists
    existing = db.query(models.Product).filter(models.Product.barcode == product.barcode).first()
    if existing:
        raise HTTPException(status_code=400, detail="Barcode already exists")
    
    new_item = models.Product(**product.dict())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

# 2. Scan Barcode (Used by Camera)
@router.get("/scan/{barcode}")
def scan_product(barcode: str, db: Session = Depends(get_db)):
    item = db.query(models.Product).filter(models.Product.barcode == barcode).first()
    if not item:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {
        "status": "found",
        "name": item.name,
        "price": item.price,
        "stock": item.stock_quantity,
        "type": "PRODUCT"
    }

# 3. Stock Audit (Phone Update)
@router.post("/audit/{barcode}")
def update_stock(barcode: str, actual_qty: int, db: Session = Depends(get_db)):
    item = db.query(models.Product).filter(models.Product.barcode == barcode).first()
    if not item:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Log the discrepancy (Logic can be expanded here)
    item.stock_quantity = actual_qty
    db.commit()
    return {"message": "Stock updated", "new_qty": actual_qty}