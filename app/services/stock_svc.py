from sqlalchemy.orm import Session
from app import models

def deduct_stock_for_print(db: Session, pages: int, is_color: bool):
    """
    The 'Recipe' Logic:
    1. Find 'A4 Paper' -> Deduct X sheets.
    2. Find 'Ink' -> Deduct Y percent.
    """
    
    # 1. Deduct Paper (Assuming 1 page = 1 sheet for simplicity)
    # In real life, handle double-sided logic here (pages / 2)
    paper_stock = db.query(models.RawMaterial).filter(models.RawMaterial.type == "PAPER").first()
    
    if paper_stock:
        # Check if we have enough
        if paper_stock.current_level >= pages:
            paper_stock.current_level -= pages
            print(f"Deducted {pages} sheets. Remaining: {paper_stock.current_level}")
        else:
            print("ALERT: Low Paper Stock!")
    
    # 2. Deduct Ink (Estimation)
    # Assume 1 page uses 0.05 units of Ink
    ink_stock = db.query(models.RawMaterial).filter(models.RawMaterial.type == "INK").first()
    
    if ink_stock:
        usage = pages * 0.05 # 5% coverage
        ink_stock.current_level -= usage
    
    db.commit()
    return True

from sqlalchemy.orm import Session
from app import models

def deduct_stock_for_print(db: Session, pages: int, is_color: bool):
    """
    The 'Recipe' Logic:
    1. Find 'A4 Paper' -> Deduct X sheets.
    2. Find 'Ink' -> Deduct Y percent.
    """
    
    # 1. Deduct Paper (Assuming 1 page = 1 sheet for simplicity)
    # In real life, handle double-sided logic here (pages / 2)
    paper_stock = db.query(models.RawMaterial).filter(models.RawMaterial.type == "PAPER").first()
    
    if paper_stock:
        # Check if we have enough
        if paper_stock.current_level >= pages:
            paper_stock.current_level -= pages
            print(f"Deducted {pages} sheets. Remaining: {paper_stock.current_level}")
        else:
            print("ALERT: Low Paper Stock!")
    
    # 2. Deduct Ink (Estimation)
    # Assume 1 page uses 0.05 units of Ink
    ink_stock = db.query(models.RawMaterial).filter(models.RawMaterial.type == "INK").first()
    
    if ink_stock:
        usage = pages * 0.05 # 5% coverage
        ink_stock.current_level -= usage
    
    db.commit()
    return True

# New function:
def deduct_stock_dynamic(db: Session, service_type: str, count: int):
    """
    Looks up the Recipe table to find what to deduct.
    """
    # 1. Find all rules for this service (e.g., "PRINT_COLOR_A4")
    rules = db.query(models.ProductionRecipe).filter(models.ProductionRecipe.service_type == service_type).all()
    
    results = []
    
    for rule in rules:
        # Calculate total needed (e.g., 50 pages * 1 sheet = 50 sheets)
        total_deduction = rule.quantity_required * count
        
        # Deduct from Raw Material
        material = db.query(models.RawMaterial).filter(models.RawMaterial.id == rule.raw_material_id).first()
        
        if material:
            material.current_level -= total_deduction
            results.append(f"Deducted {total_deduction} of {material.name}")
            
            # Check Low Stock
            if material.current_level < 50: 
                print(f"ALERT: Low Stock for {material.name}")

    db.commit()
    return results