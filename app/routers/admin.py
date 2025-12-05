from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from pydantic import BaseModel

router = APIRouter()

# --- 1. DYNAMIC PRICING INPUTS ---
class SettingInput(BaseModel):
    key: str
    value: str
    description: str

@router.post("/settings/")
def update_setting(setting: SettingInput, db: Session = Depends(get_db)):
    # Check if exists, update or create
    existing = db.query(models.SystemSetting).filter(models.SystemSetting.key == setting.key).first()
    if existing:
        existing.value = setting.value
    else:
        new_setting = models.SystemSetting(**setting.dict())
        db.add(new_setting)
    
    db.commit()
    return {"message": f"Setting {setting.key} updated to {setting.value}"}

# --- 2. DYNAMIC PRINTER INPUTS ---
class PrinterInput(BaseModel):
    name: str
    ip_address: str

@router.post("/printers/")
def register_printer(printer: PrinterInput, db: Session = Depends(get_db)):
    new_printer = models.Printer(name=printer.name, ip_address=printer.ip_address)
    db.add(new_printer)
    db.commit()
    return {"message": "Printer Registered", "id": new_printer.ip_address}

# --- 3. DYNAMIC RECIPE INPUTS ---
class RecipeInput(BaseModel):
    service_type: str        # "PRINT_BW_A4"
    raw_material_id: int     # ID of the Paper
    amount: float            # 1.0

@router.post("/recipes/")
def add_recipe_rule(recipe: RecipeInput, db: Session = Depends(get_db)):
    new_rule = models.ProductionRecipe(
        service_type=recipe.service_type,
        raw_material_id=recipe.raw_material_id,
        quantity_required=recipe.amount
    )
    db.add(new_rule)
    db.commit()
    return {"message": "Recipe Rule Added"}