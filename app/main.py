"""
╔════════════════════════════════════════════════════════════════════════════╗
║           FASTAPI APPLICATION - MAIN ENTRY POINT                           ║
║                                                                            ║
║  This is the HEART of your FastAPI application.                           ║
║  Think of it as the "airport" - all routes go through here.               ║
╚════════════════════════════════════════════════════════════════════════════╝
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import models
from app.database import engine
from app.routers import upload, staff, inventory, pos, admin, auth, dashboard
from fastapi.staticfiles import StaticFiles
import os

# ────────────────────────────────────────────────────────────────────────────
# STEP 1: CREATE ALL DATABASE TABLES
# ────────────────────────────────────────────────────────────────────────────
# This line looks at all your Model classes (PrintJob, Product, etc.)
# and creates corresponding tables in the database IF they don't exist.
# 
# Think of models.Base as a "blueprint registry" - SQLAlchemy tracks
# all classes that inherit from Base, and create_all() creates them.
models.Base.metadata.create_all(bind=engine)

# ────────────────────────────────────────────────────────────────────────────
# STEP 2: CREATE THE FASTAPI APP INSTANCE
# ────────────────────────────────────────────────────────────────────────────
# FastAPI() creates the main application object.
# This is what receives HTTP requests and sends responses.
# 
# The 'title' parameter appears in the auto-generated docs at /docs
app = FastAPI(
    title="PrintSync API",
    description="Point-of-Sale System with Document Printing",
    version="1.0.0"
)


# ensure static exists
os.makedirs("static/uploads", exist_ok=True)

# mount static directory
app.mount("/static", StaticFiles(directory="static"), name="static")
# ────────────────────────────────────────────────────────────────────────────
# STEP 3: ADD MIDDLEWARE (OPTIONAL BUT GOOD PRACTICE)
# ────────────────────────────────────────────────────────────────────────────
# Middleware intercepts requests/responses.
# CORS = Cross-Origin Resource Sharing
# This allows your frontend (different domain) to call your backend API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual domains
    allow_credentials=True,
    allow_methods=["*"],   # GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],   # Accept any headers
)

# ────────────────────────────────────────────────────────────────────────────
# STEP 4: INCLUDE ROUTERS
# ────────────────────────────────────────────────────────────────────────────
# Routers are like organizing code into modules.
# Instead of having 100 endpoints in main.py, split them by feature.
# 
# Example:
#   upload.py = all file upload endpoints
#   inventory.py = all inventory endpoints
#   pos.py = all sales endpoints
# 
# prefix="/api/v1" means all routes will start with /api/v1/
# So @router.post("/upload/") becomes POST /api/v1/upload/
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(upload.router, prefix="/api/v1", tags=["Customer Upload"])
app.include_router(staff.router,prefix="/api/v1",tags=["staff"])
app.include_router(inventory.router, prefix="/api/v1", tags=["Inventory"]) # New
app.include_router(pos.router, prefix="/api/v1", tags=["POS"]) # New

app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin Config"])


@app.on_event("startup")
async def startup_event():
    # Server starts without starting the watchdog
    # User must manually start it via the endpoint
    print(" [STARTUP] Server initialized. Printer watchdog is INACTIVE. Use POST /api/v1/admin/printer/control {\"action\": \"start\"} to activate.")

# ────────────────────────────────────────────────────────────────────────────
# STEP 5: DEFINE ENDPOINTS
# ────────────────────────────────────────────────────────────────────────────

@app.get("/")
async def read_root():
    """
    ROOT ENDPOINT - The Welcome Page
    
    When you visit: http://localhost:8000/
    This function is called and returns JSON.
    
    @app.get("/") = Listen for GET requests at path "/"
    async = This function can handle multiple requests concurrently
    """
    return {
        "message": "PrintSync System Online",
        "docs_url": "http://localhost:8000/docs",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """
    HEALTH CHECK ENDPOINT
    
    Used by monitoring tools to check if API is alive.
    Returns immediately with status.
    
    Usage: curl http://localhost:8000/health
    """
    return {"status": "healthy", "message": "All systems operational"}