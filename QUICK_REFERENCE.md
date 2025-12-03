"""
╔════════════════════════════════════════════════════════════════════════════╗
║              FASTAPI QUICK REFERENCE - CHEAT SHEET                         ║
║                Keep this file handy for quick lookups!                     ║
╚════════════════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STARTING THE SERVER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# First time setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start server
uvicorn app.main:app --reload

# Server runs at:
- http://localhost:8000/          <- Main API
- http://localhost:8000/docs      <- Interactive docs ⭐ (VERY USEFUL!)
- http://localhost:8000/redoc     <- Alternative docs


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BASIC ENDPOINT PATTERNS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# GET - Retrieve data
@app.get("/items/")
async def get_items():
    return [{"id": 1, "name": "Item 1"}]

# GET with parameter
@app.get("/items/{item_id}")
async def get_item(item_id: int):
    return {"id": item_id, "name": f"Item {item_id}"}

# POST - Create data
@app.post("/items/")
async def create_item(item: dict):
    return {"created": True, "item": item}

# PUT - Update data
@app.put("/items/{item_id}")
async def update_item(item_id: int, item: dict):
    return {"updated": True, "id": item_id}

# DELETE - Remove data
@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    return {"deleted": True, "id": item_id}


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUEST/RESPONSE VALIDATION (Pydantic)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from pydantic import BaseModel

# Define request/response format
class Item(BaseModel):
    name: str
    price: float
    quantity: int = 0  # Default value

# Use in endpoint
@app.post("/items/")
async def create_item(item: Item):
    return item

# Request:
POST /items/
{
    "name": "Pen",
    "price": 1.50,
    "quantity": 100
}

# Response:
{
    "name": "Pen",
    "price": 1.50,
    "quantity": 100
}


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DATABASE OPERATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Create entry
user = User(name="John", email="john@example.com")
db.add(user)
db.commit()

# Read all
users = db.query(User).all()

# Read one
user = db.query(User).filter(User.id == 1).first()

# Read with condition
active_users = db.query(User).filter(User.is_active == True).all()

# Update
user = db.query(User).filter(User.id == 1).first()
user.name = "Jane"
db.commit()

# Delete
user = db.query(User).filter(User.id == 1).first()
db.delete(user)
db.commit()


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEPENDENCY INJECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Database dependency
@app.get("/users/")
async def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

# Multiple dependencies
@app.get("/items/")
async def get_items(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 10
):
    return db.query(Item).offset(skip).limit(limit).all()

# Custom dependency
def get_current_user(token: str = Header(...)):
    # Validate token
    return {"user": "john"}

@app.get("/profile/")
async def get_profile(user: dict = Depends(get_current_user)):
    return user


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ERROR HANDLING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from fastapi import HTTPException

# Raise error
@app.get("/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Common HTTP status codes:
200 - OK (success)
201 - Created
400 - Bad Request (client error)
401 - Unauthorized
404 - Not Found
500 - Server Error


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FILE UPLOADS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from fastapi import UploadFile, File

@app.post("/upload/")
async def upload(file: UploadFile = File(...)):
    # Read file contents
    contents = await file.read()
    
    # Save to disk
    with open(f"uploads/{file.filename}", "wb") as f:
        f.write(contents)
    
    return {"filename": file.filename, "size": len(contents)}


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TESTING ENDPOINTS WITH CURL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# GET request
curl http://localhost:8000/items/

# GET with parameter
curl http://localhost:8000/items/1

# POST request
curl -X POST http://localhost:8000/items/ \\
  -H "Content-Type: application/json" \\
  -d '{"name":"Pen","price":1.50}'

# POST file
curl -X POST http://localhost:8000/upload/ \\
  -F "file=@/path/to/file.pdf"

# Pretty print JSON
curl http://localhost:8000/items/ | python -m json.tool


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
USEFUL LINKS & DOCS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Official FastAPI Docs:     https://fastapi.tiangolo.com/
Pydantic Docs:             https://docs.pydantic.dev/
SQLAlchemy Docs:           https://docs.sqlalchemy.org/
HTTP Status Codes:         https://httpwg.org/specs/rfc7231.html


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMMON MISTAKES & FIXES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ Forgetting db.commit()
   db.add(user)
   # You need: db.commit()

❌ Not closing database sessions
   db = SessionLocal()  # Should use Depends(get_db) instead

❌ Mixing async and blocking operations
   async def endpoint():  # async but uses blocking I/O
       data = db.query(...).all()

✓ Use Depends() for database sessions
✓ Always commit after changes
✓ Use async for I/O operations
✓ Check http://localhost:8000/docs for endpoint documentation

"""
