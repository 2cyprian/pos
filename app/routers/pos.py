from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.services.stock_svc import deduct_stock_for_print

router = APIRouter()

@router.post("/checkout/")
def process_checkout(cart: schemas.CheckoutRequest, db: Session = Depends(get_db)):
    total_bill = 0.0
    order_items = []
    
    # --- PHASE 1: VALIDATE & CALCULATE ---
    for item in cart.items:
        
        # A. If it's a Retail Product (Pen, Folder)
        if item.type == "PRODUCT":
            product = db.query(models.Product).filter(models.Product.barcode == item.id).first()
            if not product:
                raise HTTPException(status_code=404, detail=f"Product {item.id} not found")
            
            if product.stock_quantity < item.quantity:
                raise HTTPException(status_code=400, detail=f"Not enough stock for {product.name}")
            
            # Add to bill
            line_total = product.price * item.quantity
            total_bill += line_total
            
            # Deduct Retail Stock Immediately
            product.stock_quantity -= item.quantity
            
            # Prepare Log
            order_items.append(models.OrderItem(
                product_name=product.name,
                quantity=item.quantity,
                unit_price=product.price,
                item_type="RETAIL"
            ))

        # B. If it's a Print Job (PDF)
        elif item.type == "PRINT_JOB":
            job = db.query(models.PrintJob).filter(models.PrintJob.job_code == item.id).first()
            if not job:
                raise HTTPException(status_code=404, detail=f"Job {item.id} not found")
            
            # Calculate Print Price (Simple Logic: $0.10 per page)
            # In real app, fetch price from settings
            price_per_page = 0.50 if job.is_color else 0.10
            line_total = (job.total_pages * price_per_page) * item.quantity
            total_bill += line_total
            
            # Mark Job as Paid/Collected
            job.status = "COLLECTED"
            
            # Trigger 'Recipe' Deduction (Paper/Ink)
            deduct_stock_for_print(db, job.total_pages * item.quantity, job.is_color)
            
            # Prepare Log
            order_items.append(models.OrderItem(
                product_name=f"Print: {job.filename}",
                quantity=item.quantity, # Copies
                unit_price=line_total / item.quantity,
                item_type="SERVICE"
            ))

    # --- PHASE 2: SAVE ORDER ---
    new_order = models.Order(
        total_amount=total_bill,
        payment_method=cart.payment_method
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    
    # Save Items
    for log_item in order_items:
        log_item.order_id = new_order.id
        db.add(log_item)
    
    db.commit()

    return {
        "status": "success",
        "order_id": new_order.id,
        "total_paid": total_bill,
        "message": "Transaction Completed"
    }