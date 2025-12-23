"""
╔════════════════════════════════════════════════════════════════════════════╗
║         UPLOAD ROUTER - FILE UPLOAD ENDPOINTS                              ║
║                                                                            ║
║  This module handles all file upload operations.                           ║
║  Each @router.post() = a new endpoint                                      ║
╚════════════════════════════════════════════════════════════════════════════╝
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.services.file_analysis import analyze_pdf
import shutil
import os
import random

# ────────────────────────────────────────────────────────────────────────────
# CREATE A ROUTER INSTANCE
# ────────────────────────────────────────────────────────────────────────────
# APIRouter = a container for related endpoints
# Think of it like a "chapter" in your API documentation.
# All endpoints defined with @router will be grouped together.
router = APIRouter()

# Directory where uploaded files are stored
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Create folder if it doesn't exist

# ────────────────────────────────────────────────────────────────────────────
# ENDPOINT 1: FILE UPLOAD
# ────────────────────────────────────────────────────────────────────────────

@router.post("/upload/")
async def upload_document(
    file: UploadFile = File(...),  # Required file parameter
    db: Session = Depends(get_db)  # Dependency injection for database
):
    """
    FILE UPLOAD ENDPOINT
    
    HTTP Method: POST
    URL: /api/v1/upload/  (prefix from main.py)
    
    What happens:
    1. Generate unique 4-digit code (#XXXX)
    2. Save file to disk
    3. Analyze file (count pages)
    4. Store info in database
    5. Return job code to customer
    
    PARAMETERS:
    -----------
    file : UploadFile
        The file uploaded by customer
        File(...) means this parameter is REQUIRED
    
    db : Session
        Database session (injected via Depends)
        FastAPI automatically calls get_db() and passes the session
    
    RETURN:
    -------
    dict: Job code, page count, filename, and message
    
    FASTAPI CONCEPTS USED:
    ├─ @router.post() = Handle HTTP POST requests
    ├─ async = Handle multiple uploads concurrently
    ├─ UploadFile = Special FastAPI class for file uploads
    ├─ File(...) = File parameter (required)
    └─ Depends(get_db) = Dependency injection pattern
    """
    try:
        # ────────────────────────────────────────────────────────────────────
        # STEP 1: Generate Unique Job Code
        # ────────────────────────────────────────────────────────────────────
        # This is the code the customer shows at the counter
        # Example: #4492
        job_code = str(random.randint(1000, 9999))
         
        # ────────────────────────────────────────────────────────────────────
        # STEP 2: Save File to Disk
        # ────────────────────────────────────────────────────────────────────
        # The file is saved in static/uploads/ with the job code prefix
        # Example: static/uploads/4492_document.pdf
        file_location = f"{UPLOAD_DIR}/{job_code}_{file.filename}"
        
        with open(file_location, "wb") as buffer:
            # Read file in chunks and write to disk
            # This is memory-efficient for large files
            shutil.copyfileobj(file.file, buffer)
        
        # ────────────────────────────────────────────────────────────────────
        # STEP 3: Analyze the File
        # ────────────────────────────────────────────────────────────────────
        # Count pages, detect colors, etc.
        # This is a service function (see services/file_analysis.py)
        analysis = analyze_pdf(file_location)
        
        # ────────────────────────────────────────────────────────────────────
        # STEP 4: Save to Database
        # ────────────────────────────────────────────────────────────────────
        # Create a new PrintJob record in the database
        # This is an ORM operation (SQLAlchemy)
        new_job = models.PrintJob(
            job_code=job_code,
            filename=file.filename,
            file_path=file_location,
            total_pages=analysis["pages"],
            status="PENDING"  # Job is waiting to be printed
        )
        
        # Add to session (staging area)
        db.add(new_job)
        
        # Commit = actually write to database
        db.commit()
        
        # Refresh = get the updated object from DB (gets auto-generated ID)
        db.refresh(new_job)
        
        # ────────────────────────────────────────────────────────────────────
        # STEP 5: Return Response
        # ────────────────────────────────────────────────────────────────────
        # FastAPI automatically converts dict to JSON
        return {
            "job_code": new_job.job_code,
            "pages": new_job.total_pages,
            "filename": new_job.filename,
            "message": "✓ Upload successful! Go to counter and show this code."
        }
    
    except Exception as e:
        # If something goes wrong, return an error
        raise HTTPException(
            status_code=400,
            detail=f"Upload failed: {str(e)}"
        )