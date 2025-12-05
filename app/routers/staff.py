from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.services.printer_svc import send_to_printer
from app.services.stock_svc import deduct_stock_for_print

router = APIRouter()

# 1. Get the Print Queue (List of files)
@router.get("/queue/")
def get_print_queue(db: Session = Depends(get_db)):
    # Return all jobs that are PENDING
    jobs = db.query(models.PrintJob).filter(models.PrintJob.status == "PENDING").all()
    return jobs

# 2. Execute Print (The Action Button)
@router.post("/print/{job_code}")
def execute_print_job(job_code: str, printer_name: str = "Default", db: Session = Depends(get_db)):
    
    # A. Find the Job
    job = db.query(models.PrintJob).filter(models.PrintJob.job_code == job_code).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # B. Send to Physical Printer
    result = send_to_printer(job.file_path, printer_name)
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])

    # C. Deduct Inventory (The Recipe)
    deduct_stock_for_print(db, job.total_pages, job.is_color)

    # D. Update Job Status
    job.status = "PRINTED"
    db.commit()

    return {"message": "Printing started", "pages_deducted": job.total_pages}