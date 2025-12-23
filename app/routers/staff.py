from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
import os
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.services.printer_svc import send_to_printer
from app.services.stock_svc import deduct_stock_for_print
from app.utils.auth import require_owner, require_staff, hash_password

router = APIRouter()

# ────────────────────────────────────────────────────────────────────────────
# OWNER MANAGEMENT ENDPOINTS (Manage Staff & Branches)
# ────────────────────────────────────────────────────────────────────────────

@router.get("/owner/dashboard", tags=["Owner Management"])
async def get_owner_dashboard(
    owner: models.User = Depends(require_owner),
    db: Session = Depends(get_db)
):
    """
    OWNER ONLY: Get dashboard summary with branches and staff count
    """
    total_branches = db.query(models.Branch).filter(
        models.Branch.owner_id == owner.id
    ).count()
    
    total_staff = db.query(models.User).filter(
        models.User.role == "STAFF",
        models.User.branch_id.in_(
            db.query(models.Branch.id).filter(models.Branch.owner_id == owner.id)
        )
    ).count()
    
    branches = db.query(models.Branch).filter(models.Branch.owner_id == owner.id).all()
    
    return {
        "owner_name": owner.username,
        "owner_email": owner.email,
        "total_branches": total_branches,
        "total_staff": total_staff,
        "branches": [
            {
                "id": b.id,
                "name": b.name,
                "location": b.location,
                "is_active": b.is_active
            }
            for b in branches
        ]
    }


@router.post("/branches/", response_model=schemas.BranchResponse, tags=["Owner Management"])
async def create_branch(
    branch: schemas.BranchCreate,
    owner: models.User = Depends(require_owner),
    db: Session = Depends(get_db)
):
    """
    OWNER ONLY: Create a new branch
    """
    new_branch = models.Branch(
        name=branch.name,
        location=branch.location,
        phone=branch.phone,
        owner_id=owner.id
    )
    db.add(new_branch)
    db.commit()
    db.refresh(new_branch)
    return new_branch


@router.get("/branches/", response_model=list[schemas.BranchResponse], tags=["Owner Management"])
async def list_branches(
    owner: models.User = Depends(require_owner),
    db: Session = Depends(get_db)
):
    """
    OWNER ONLY: List all branches owned by this owner
    """
    branches = db.query(models.Branch).filter(models.Branch.owner_id == owner.id).all()
    return branches


@router.post("/staff/", response_model=schemas.UserResponse, tags=["Owner Management"])
async def create_staff(
    staff: schemas.UserCreate,
    owner: models.User = Depends(require_owner),
    db: Session = Depends(get_db)
):
    """
    OWNER ONLY: Create a new staff member.
    Staff must be assigned to a branch by owner.
    """
    # Check if user exists
    existing = db.query(models.User).filter(models.User.username == staff.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Hash password securely (supports long passwords)
    password_hash = hash_password(staff.password)
    
    new_staff = models.User(
        username=staff.username,
        email=staff.email,
        password_hash=password_hash,
        role="STAFF"
    )
    db.add(new_staff)
    db.commit()
    db.refresh(new_staff)
    
    return new_staff


@router.put("/staff/{staff_id}/password", tags=["Owner Management"])
async def update_staff_password(
    staff_id: int,
    payload: schemas.PasswordUpdate,
    owner: models.User = Depends(require_owner),
    db: Session = Depends(get_db)
):
    """
    OWNER ONLY: Update a staff member's password.
    If the staff is assigned to a branch, enforce that the branch belongs to this owner.
    """
    staff = db.query(models.User).filter(models.User.id == staff_id, models.User.role == "STAFF").first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")

    # If staff belongs to a branch, verify ownership
    if staff.branch_id:
        branch = db.query(models.Branch).filter(
            models.Branch.id == staff.branch_id,
            models.Branch.owner_id == owner.id
        ).first()
        if not branch:
            raise HTTPException(status_code=403, detail="You can only manage staff in your own branches")

    # Store hashed password
    staff.password_hash = hash_password(payload.new_password)
    db.commit()

    return {"message": f"Password updated for {staff.username}"}


@router.post("/staff/{staff_id}/assign-branch", tags=["Owner Management"])
async def assign_staff_to_branch(
    staff_id: int,
    branch_id: int,
    owner: models.User = Depends(require_owner),
    db: Session = Depends(get_db)
):
    """
    OWNER ONLY: Assign a staff member to a branch
    """
    staff = db.query(models.User).filter(models.User.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    branch = db.query(models.Branch).filter(
        models.Branch.id == branch_id,
        models.Branch.owner_id == owner.id
    ).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found or not owned by you")
    
    staff.branch_id = branch_id
    db.commit()
    
    return {"message": f"Staff {staff.username} assigned to branch {branch.name}"}


@router.get("/staff/", response_model=list[schemas.UserResponse], tags=["Owner Management"])
async def list_staff(
    owner: models.User = Depends(require_owner),
    db: Session = Depends(get_db)
):
    """
    OWNER ONLY: List staff members assigned to this owner's branches
    """
    # Get all branch IDs owned by this owner
    owner_branch_ids = db.query(models.Branch.id).filter(
        models.Branch.owner_id == owner.id
    ).all()
    branch_ids = [b[0] for b in owner_branch_ids]
    
    # Get staff assigned to these branches
    staff_list = db.query(models.User).filter(
        models.User.role == "STAFF",
        models.User.branch_id.in_(branch_ids)
    ).all()
    
    return staff_list


@router.post("/staff/{staff_id}/permissions/", tags=["Owner Management"])
async def grant_permission(
    staff_id: int,
    permission_name: str,
    owner: models.User = Depends(require_owner),
    db: Session = Depends(get_db)
):
    """
    OWNER ONLY: Grant a specific permission to a staff member in your branches
    Example permissions: "create_product", "view_reports", "refund_order"
    """
    staff = db.query(models.User).filter(models.User.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    # Verify staff belongs to one of this owner's branches
    if staff.branch_id:
        branch = db.query(models.Branch).filter(
            models.Branch.id == staff.branch_id,
            models.Branch.owner_id == owner.id
        ).first()
        if not branch:
            raise HTTPException(
                status_code=403, 
                detail="You can only manage staff in your own branches"
            )
    
    # Check if permission already exists
    existing_perm = db.query(models.Permission).filter(
        models.Permission.user_id == staff_id,
        models.Permission.permission_name == permission_name
    ).first()
    
    if existing_perm:
        return {"message": f"Permission '{permission_name}' already granted"}
    
    new_permission = models.Permission(
        user_id=staff_id,
        permission_name=permission_name
    )
    db.add(new_permission)
    db.commit()
    
    return {"message": f"Permission '{permission_name}' granted to {staff.username}"}


# ────────────────────────────────────────────────────────────────────────────
# STAFF PRINT QUEUE ENDPOINTS (Existing)
# ────────────────────────────────────────────────────────────────────────────

@router.get("/queue/", tags=["Print Queue"])
async def get_print_queue(
    staff: models.User = Depends(require_staff),
    db: Session = Depends(get_db)
):
    """STAFF ONLY: Get the print queue"""
    # Return all jobs that are PENDING, with download/print links
    jobs = db.query(models.PrintJob).filter(models.PrintJob.status == "PENDING").all()
    base = "/api/v1/queue"
    result = []
    for j in jobs:
        result.append({
            "id": j.id,
            "job_code": j.job_code,
            "filename": j.filename,
            "total_pages": j.total_pages,
            "is_color": j.is_color,
            "status": j.status,
            "download_url": f"{base}/{j.job_code}/download/",
            "print_url": f"{base}/{j.job_code}/print/"
        })
    return result



# Simple download endpoint for staff
@router.get("/queue/{job_code}/download/", tags=["Print Queue"])
async def download_print_job(
    job_code: str,
    staff: models.User = Depends(require_staff),
    db: Session = Depends(get_db)
):
    """STAFF ONLY: Download a print job file"""
    job = db.query(models.PrintJob).filter(models.PrintJob.job_code == job_code).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not os.path.exists(job.file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(job.file_path, filename=job.filename)

# Simplified print endpoint from queue (keeps single action per job)
@router.post("/queue/{job_code}/print/", tags=["Print Queue"])
async def print_from_queue(
    job_code: str,
    printer_name: str = "Default",
    staff: models.User = Depends(require_staff),
    db: Session = Depends(get_db)
):
    """STAFF ONLY: Print a job from queue"""
    job = db.query(models.PrintJob).filter(models.PrintJob.job_code == job_code).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    result = send_to_printer(job.file_path, printer_name)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    deduct_stock_for_print(db, job.total_pages, job.is_color)
    job.status = "PRINTED"
    db.commit()
    return {"message": "Printing started", "pages_deducted": job.total_pages}