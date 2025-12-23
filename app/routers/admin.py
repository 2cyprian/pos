from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from pydantic import BaseModel
from app.services.watchdog_svc import start_watchdog, stop_watchdog, is_watchdog_running

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
    modal:str

@router.post("/printers/")
def register_printer(printer: PrinterInput, db: Session = Depends(get_db)):
    new_printer = models.Printer(name=printer.name, ip_address=printer.ip_address)
    db.add(new_printer)
    db.commit()
    db.refresh(new_printer)
    
    # Create initial log entry for the new printer
    initial_log = models.PrinterLog(
        printer_id=new_printer.id,
        page_count=0,
        notes="Printer registered - Initial entry"
    )
    db.add(initial_log)
    db.commit()
    
    return {
        "message": "Printer Registered", 
        "id": new_printer.id,
        "ip_address": new_printer.ip_address,
        "initial_log": "Entry created"
    }

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


# --- 4. PRINTER LOGS ENDPOINT ---
@router.get("/printer/logs/{printer_id}")
def get_printer_logs(printer_id: int, limit: int = 50, db: Session = Depends(get_db)):
    """
    Get activity logs for a specific printer.
    Shows page counter history and when changes occurred.
    
    Parameters:
    - printer_id: ID of the printer
    - limit: Maximum number of logs to return (default: 50)
    """
    printer = db.query(models.Printer).filter(models.Printer.id == printer_id).first()
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    logs = db.query(models.PrinterLog).filter(
        models.PrinterLog.printer_id == printer_id
    ).order_by(models.PrinterLog.recorded_at.desc()).limit(limit).all()
    
    return {
        "printer_name": printer.name,
        "printer_ip": printer.ip_address,
        "current_page_count": printer.total_page_counter,
        "total_logs": len(logs),
        "logs": [
            {
                "timestamp": log.recorded_at.isoformat(),
                "page_count": log.page_count,
                "notes": log.notes
            }
            for log in logs
        ]
    }


@router.get("/printer/logs")
def list_all_printer_logs(db: Session = Depends(get_db)):
    """
    Get all registered printers with their latest log information.
    """
    printers = db.query(models.Printer).all()
    
    result = []
    for printer in printers:
        latest_log = db.query(models.PrinterLog).filter(
            models.PrinterLog.printer_id == printer.id
        ).order_by(models.PrinterLog.recorded_at.desc()).first()
        
        result.append({
            "id": printer.id,
            "name": printer.name,
            "ip_address": printer.ip_address,
            "current_page_count": printer.total_page_counter,
            "last_logged": latest_log.recorded_at.isoformat() if latest_log else None,
            "last_notes": latest_log.notes if latest_log else None
        })
    
    return {"printers": result, "total_count": len(result)}


class PrinterControlInput(BaseModel):
    action: str  # "start", "stop", or "status"

@router.post("/printer/control")
async def control_printer_watchdog(request: PrinterControlInput, db: Session = Depends(get_db)):
    """
    Unified endpoint to control printer watchdog.
    
    Actions:
    - "start": Start the printer monitoring watchdog
    - "stop": Stop the printer monitoring watchdog
    - "status": Check if the watchdog is running
    
    Example:
    {
        "action": "start"
    }
    """
    action = request.action.lower().strip()
    
    if action == "start":
        state = start_watchdog()
        if state == "already_running":
            return {"status": state, "message": "Printer watchdog is already active"}
        return {
            "status": state,
            "message": "Printer watchdog started successfully" if state == "started" else "No change",
            "description": "Watchdog will check printer counters every 60 seconds"
        }
    
    elif action == "stop":
        state = await stop_watchdog()
        if state == "not_running":
            return {"status": state, "message": "Printer watchdog is not currently running"}
        return {"status": state, "message": "Printer watchdog stopped successfully"}
    
    elif action == "status":
        is_running = is_watchdog_running()
        return {
            "is_running": is_running,
            "status": "active" if is_running else "inactive",
            "message": "Printer watchdog is " + ("active" if is_running else "inactive")
        }
    
    else:
        return {
            "status": "error",
            "message": f"Invalid action: {action}",
            "valid_actions": ["start", "stop", "status"]
        }