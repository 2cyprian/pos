"""
╔════════════════════════════════════════════════════════════════════════════╗
║                    FASTAPI LEARNING GUIDE                                  ║
║          A Beginner's Guide to Understanding This Project                  ║
╚════════════════════════════════════════════════════════════════════════════╝

TABLE OF CONTENTS:
──────────────────────────────────────────────────────────────────────────────
1. FastAPI Basics
2. Project Architecture
3. Running the Application
4. API Endpoints Explained
5. Database Concepts
6. Common Patterns Used
7. How to Add New Features


════════════════════════════════════════════════════════════════════════════════
1. FASTAPI BASICS
════════════════════════════════════════════════════════════════════════════════

What is FastAPI?
─────────────────
FastAPI is a modern Python framework for building web APIs.
- Modern: Uses Python 3.7+ features
- Fast: One of the fastest Python frameworks
- Easy: Great for beginners
- Documented: Auto-generates API documentation


HTTP Methods:
─────────────
GET    = Retrieve data (safe, no changes)
POST   = Send data / Create something
PUT    = Update existing data
DELETE = Remove data

Example:
    @app.get("/items/")           # Retrieve all items
    @app.post("/items/")          # Create new item
    @app.get("/items/{item_id}")  # Retrieve specific item
    @app.put("/items/{item_id}")  # Update specific item
    @app.delete("/items/{item_id}") # Delete specific item


Decorators (The @ Symbol):
──────────────────────────
Decorators modify how functions work.

    @app.get("/")  # This decorator tells FastAPI:
    async def read_root():  # "When GET request comes to /, call this function"
        return {"message": "Hello"}

Common decorators:
- @app.get()    - Handle GET requests
- @app.post()   - Handle POST requests
- @app.put()    - Handle PUT requests
- @app.delete() - Handle DELETE requests


Async & Await:
──────────────
async def = Can handle multiple requests at the same time
This is important for performance!

    # Without async - handles one request, waits for it to finish
    def read_root():
        return {"message": "Hello"}
    
    # With async - can handle many requests concurrently
    async def read_root():
        return {"message": "Hello"}


════════════════════════════════════════════════════════════════════════════════
2. PROJECT ARCHITECTURE
════════════════════════════════════════════════════════════════════════════════

PrintSync Backend Structure:
────────────────────────────
app/
├── main.py              <- Application entry point
├── database.py          <- Database connection setup
├── models.py            <- Database table definitions (ORM)
├── schemas.py           <- Request/Response validation (Pydantic)
├── routers/             <- API endpoints organized by feature
│   ├── upload.py
│   ├── inventory.py
│   └── pos.py
└── services/            <- Business logic (heavy operations)
    ├── file_analysis.py
    ├── printer_svc.py
    └── stock_svc.py


Architecture Pattern: MVC-like Structure
─────────────────────────────────────────
    CLIENT (Frontend)
        ↓
    ROUTER (Endpoint)           <- Receives request
        ↓
    SERVICE (Business Logic)    <- Does the work
        ↓
    DATABASE (Models)           <- Stores data


Flow Example: Upload a File
────────────────────────────
1. Customer sends file → POST /api/v1/upload/
2. Router (upload.py) receives request
3. Service (file_analysis.py) analyzes PDF
4. Database (models.PrintJob) stores record
5. Response returned to customer


════════════════════════════════════════════════════════════════════════════════
3. RUNNING THE APPLICATION
════════════════════════════════════════════════════════════════════════════════

Start the Server:
─────────────────
cd /path/to/print_sync_backend
source venv/bin/activate              # Activate virtual environment
uvicorn app.main:app --reload


What Each Part Means:
──────────────────────
uvicorn           = Web server (runs FastAPI apps)
app.main:app      = Look in app/main.py for variable named 'app'
--reload          = Auto-restart when files change (development only)


Access the API:
────────────────
Web Browser:
    http://localhost:8000/          <- Main API
    http://localhost:8000/docs      <- Interactive API docs (Swagger UI) ⭐
    http://localhost:8000/redoc     <- Alternative docs format

Command Line:
    curl http://localhost:8000/


════════════════════════════════════════════════════════════════════════════════
4. API ENDPOINTS EXPLAINED
════════════════════════════════════════════════════════════════════════════════

Root Endpoint:
───────────────
GET /
Returns: {"message": "PrintSync System Online", ...}
Purpose: Check if API is running


Health Check:
──────────────
GET /health
Returns: {"status": "healthy", ...}
Purpose: Used by monitoring tools


File Upload:
─────────────
POST /api/v1/upload/
Parameters: file (PDF document)
Returns: {
    "job_code": "4492",
    "pages": 3,
    "filename": "resume.pdf",
    "message": "✓ Upload successful!"
}
Purpose: Customer uploads document, gets job code


════════════════════════════════════════════════════════════════════════════════
5. DATABASE CONCEPTS
════════════════════════════════════════════════════════════════════════════════

ORM (Object-Relational Mapping):
─────────────────────────────────
ORM lets you work with databases using Python classes instead of SQL.

Without ORM (Raw SQL):
    SELECT * FROM print_jobs WHERE status = 'PENDING'

With ORM (SQLAlchemy):
    db.query(PrintJob).filter(PrintJob.status == "PENDING").all()

Benefits:
- More Pythonic
- Safer (prevents SQL injection)
- Easier to understand


Models vs Schemas:
──────────────────
MODELS (database.py):        <- What's in the DATABASE
class PrintJob:
    __tablename__ = "print_jobs"
    id = Column(Integer, primary_key=True)
    job_code = Column(String, unique=True)

SCHEMAS (schemas.py):        <- What's in API REQUESTS/RESPONSES
class PrintJobSchema(BaseModel):
    job_code: str
    filename: str


Sessions:
─────────
A "session" is a conversation with the database.

    def get_db():
        db = SessionLocal()  # Create connection
        try:
            yield db         # Use it
        finally:
            db.close()       # Close it


════════════════════════════════════════════════════════════════════════════════
6. COMMON PATTERNS USED IN THIS PROJECT
════════════════════════════════════════════════════════════════════════════════

Pattern 1: Dependency Injection
────────────────────────────────
Instead of creating database connection inside endpoint:
    BAD:
    @app.get("/")
    def read_root():
        db = SessionLocal()  # Creates connection every time
        ...

Use Depends() to inject it:
    GOOD:
    @app.get("/")
    def read_root(db: Session = Depends(get_db)):
        ...  # FastAPI provides db automatically


Pattern 2: Router Organization
──────────────────────────────
Instead of 100 endpoints in main.py:
    BAD:
    app.py (1000 lines - hard to maintain)

Organize by feature:
    GOOD:
    upload.py   (upload endpoints)
    inventory.py (inventory endpoints)
    pos.py      (sales endpoints)


Pattern 3: Service Layer
────────────────────────
Instead of business logic in endpoints:
    BAD:
    @app.post("/upload/")
    def upload(file):
        # Count pages, save file, analyze... (50 lines of logic)

Use services:
    GOOD:
    @app.post("/upload/")
    def upload(file):
        result = analyze_pdf(file)  # Clean, reusable


════════════════════════════════════════════════════════════════════════════════
7. HOW TO ADD NEW FEATURES
════════════════════════════════════════════════════════════════════════════════

Example: Add "Get All Print Jobs" Endpoint

Step 1: Create the Endpoint
────────────────────────────
File: app/routers/upload.py

    @router.get("/jobs/")
    async def get_all_jobs(db: Session = Depends(get_db)):
        \"\"\"Get all print jobs\"\"\"
        jobs = db.query(models.PrintJob).all()
        return jobs


Step 2: Register the Router
───────────────────────────
File: app/main.py (already done!)
    app.include_router(upload.router, prefix="/api/v1")


Step 3: Test the Endpoint
─────────────────────────
Start server:
    uvicorn app.main:app --reload

Visit in browser:
    http://localhost:8000/docs

Or with curl:
    curl http://localhost:8000/api/v1/jobs/


════════════════════════════════════════════════════════════════════════════════
8. DEBUGGING TIPS
════════════════════════════════════════════════════════════════════════════════

1. Check the Swagger UI:
   http://localhost:8000/docs
   - Shows all endpoints
   - Try requests directly
   - See request/response examples

2. Use print() for debugging:
   @app.get("/debug")
   def debug():
       print("This appears in terminal")
       return {"status": "ok"}

3. Check database file (if using SQLite):
   - Located at: test.db in project root
   - Can open with SQLite browser tools

4. Check error messages in terminal:
   The terminal running uvicorn shows detailed error messages


════════════════════════════════════════════════════════════════════════════════
9. NEXT STEPS TO LEARN
════════════════════════════════════════════════════════════════════════════════

1. ✓ Run the server and explore /docs
2. ✓ Add a simple GET endpoint
3. ✓ Add a simple POST endpoint
4. ✓ Query the database
5. Error handling with HTTPException
6. Input validation with Pydantic
7. Authentication (JWT tokens)
8. Environment variables (.env)
9. Testing with pytest
10. Deployment (Heroku, DigitalOcean, AWS)


════════════════════════════════════════════════════════════════════════════════

Questions? Check the docstrings in each file!
Every function has detailed comments explaining the FastAPI concepts used.

"""
