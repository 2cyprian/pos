from sqlalchemy.orm import Session
from app import models

def get_dynamic_price(db: Session, key: str, default: float):
    """
    Fetches a dynamic price (or any setting) from the SystemSettings table.
    If the setting is not found, returns a default value.
    """
    setting = db.query(models.SystemSetting).filter(models.SystemSetting.key == key).first()
    if setting:
        try:
            return float(setting.value)
        except ValueError:
            # Handle cases where value in DB is not a valid float
            print(f"Warning: SystemSetting key '{key}' has non-float value: {setting.value}. Using default: {default}")
            return default
    return default
