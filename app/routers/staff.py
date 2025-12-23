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


@router.delete("/branches/{branch_id}/", tags=["Owner Management"])
async def delete_branch(
    branch_id: int,
    owner: models.User = Depends(require_owner),
    db: Session = Depends(get_db)
):
    """
    OWNER ONLY: Delete a branch
    - Verifies the branch belongs to the owner
    - Automatically reassigns all staff in the branch to unassigned (branch_id = NULL)
    - Deletes the branch record
    """
    # Get the branch
    branch = db.query(models.Branch).filter(
        models.Branch.id == branch_id,
        models.Branch.owner_id == owner.id
    ).first()
    
    if not branch:
        raise HTTPException(
            status_code=404,
            detail="Branch not found or you don't have permission to delete it"
        )
    
    # Reassign all staff in this branch to unassigned
    db.query(models.User).filter(models.User.branch_id == branch_id).update(
        {models.User.branch_id: None}
    )
    
    # Delete the branch
    db.delete(branch)
    db.commit()
    
    return {"message": f"Branch '{branch.name}' has been deleted successfully. All staff have been unassigned."}


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
        phone=staff.phone,
        password_hash=password_hash,
        role="STAFF"
    )
    # If branch_id provided, validate ownership and assign
    if staff.branch_id is not None:
        branch = db.query(models.Branch).filter(
            models.Branch.id == staff.branch_id,
            models.Branch.owner_id == owner.id
        ).first()
        if not branch:
            raise HTTPException(
                status_code=403,
                detail="You can only assign staff to your own branches"
            )
        new_staff.branch_id = staff.branch_id
    db.add(new_staff)
    db.commit()
    db.refresh(new_staff)
    
    return new_staff


@router.put("/staff/{staff_id}/", response_model=schemas.UserResponse, tags=["Owner Management"])
async def update_staff(
    staff_id: int,
    payload: schemas.UserUpdate,
    owner: models.User = Depends(require_owner),
    db: Session = Depends(get_db)
):
    """
    OWNER ONLY: Update a staff member's details.
    Supports updating branch assignment and contact info.
    """
    staff = db.query(models.User).filter(models.User.id == staff_id, models.User.role == "STAFF").first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")

    # Update branch assignment if provided (validate ownership)
    if payload.branch_id is not None:
        branch = db.query(models.Branch).filter(
            models.Branch.id == payload.branch_id,
            models.Branch.owner_id == owner.id
        ).first()
        if not branch:
            raise HTTPException(status_code=403, detail="You can only assign staff to your own branches")
        staff.branch_id = payload.branch_id

    # Optional contact updates
    if payload.phone is not None:
        staff.phone = payload.phone
    if payload.email is not None:
        # Ensure email uniqueness
        existing_email = db.query(models.User).filter(
            models.User.email == payload.email,
            models.User.id != staff_id
        ).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already in use")
        staff.email = payload.email

    db.commit()
    db.refresh(staff)
    return staff


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
    branch_id: int | None = None,
    db: Session = Depends(get_db)
):
    """
    OWNER ONLY: List staff members assigned to this owner's branches
    
    Query Parameters:
    - branch_id (optional): Filter staff by specific branch. If not provided, returns all staff.
    """
    from sqlalchemy import or_
    
    # Get all branch IDs owned by this owner
    owner_branch_ids = db.query(models.Branch.id).filter(
        models.Branch.owner_id == owner.id
    ).all()
    branch_ids = [b[0] for b in owner_branch_ids]
    
    # Build filter conditions
    filters = [
        models.User.role == "STAFF",
        or_(
            models.User.branch_id.in_(branch_ids),
            models.User.branch_id.is_(None)
        )
    ]
    
    # If branch_id filter is provided, ensure it belongs to this owner
    if branch_id is not None:
        if branch_id not in branch_ids:
            raise HTTPException(
                status_code=403, 
                detail="You can only view staff in your own branches"
            )
        # Filter by the specific branch (only assigned staff, exclude unassigned)
        filters = [
            models.User.role == "STAFF",
            models.User.branch_id == branch_id
        ]
    
    # Get staff
    staff_list = db.query(models.User).filter(*filters).all()
    
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


@router.delete("/staff/{staff_id}/", tags=["Owner Management"])
async def delete_staff(
    staff_id: int,
    owner: models.User = Depends(require_owner),
    db: Session = Depends(get_db)
):
    """
    OWNER ONLY: Delete a staff member
    - Verifies the staff member belongs to one of the owner's branches
    - Deletes all associated permissions
    - Deletes the staff member record
    """
    # Get the staff member
    staff = db.query(models.User).filter(
        models.User.id == staff_id,
        models.User.role == "STAFF"
    ).first()
    
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")
    
    # If staff is assigned to a branch, verify ownership
    if staff.branch_id:
        branch = db.query(models.Branch).filter(
            models.Branch.id == staff.branch_id,
            models.Branch.owner_id == owner.id
        ).first()
        if not branch:
            raise HTTPException(
                status_code=403,
                detail="You can only delete staff in your own branches"
            )
    
    # Delete associated permissions
    db.query(models.Permission).filter(models.Permission.user_id == staff_id).delete()
    
    # Delete the staff member
    db.delete(staff)
    db.commit()
    
    return {"message": f"Staff member '{staff.username}' has been deleted successfully"}


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