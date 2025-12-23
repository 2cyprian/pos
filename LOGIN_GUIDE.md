# Login & Authentication Guide

## Quick Start

### Step 1: Register Owner Account (First Time Only)

**Endpoint:** `POST /api/v1/auth/register-owner`

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register-owner \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "admin123"
  }'
```

**Note:** Don't pass `"role"` - it's automatically set to OWNER.

**Response:**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "role": "OWNER",
  "is_active": true,
  "branch_id": null,
  "created_at": "2025-12-21T10:00:00"
}
```

---

### Step 2: Login as Owner

**Endpoint:** `POST /api/v1/auth/login`

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

**Response:**
```json
{
  "user_id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "role": "OWNER",
  "branch_id": null,
  "message": "Welcome back, admin! Role: OWNER"
}
```

**IMPORTANT:** Save the `user_id` - you'll use it in subsequent requests!

---

### Step 3: Create a Branch (As Owner)

**Endpoint:** `POST /api/v1/staff/branches/`

```bash
curl -X POST http://127.0.0.1:8000/api/v1/staff/branches/ \
  -H "Content-Type: application/json" \
  -H "user_id: 1" \
  -d '{
    "name": "Main Store",
    "location": "123 Downtown Avenue",
    "phone": "555-0100"
  }'
```

---

### Step 4: Create Staff Account (As Owner)

**Endpoint:** `POST /api/v1/staff/`

```bash
curl -X POST http://127.0.0.1:8000/api/v1/staff/ \
  -H "Content-Type: application/json" \
  -H "user_id: 1" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "staff123",
    "role": "STAFF"
  }'
```

**Response:**
```json
{
  "id": 2,
  "username": "john_doe",
  "email": "john@example.com",
  "role": "STAFF",
  "is_active": true,
  "branch_id": null,
  "created_at": "2025-12-21T10:05:00"
}
```

---

### Step 5: Assign Staff to Branch (As Owner)

**Endpoint:** `POST /api/v1/staff/{staff_id}/assign-branch`

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/staff/2/assign-branch?branch_id=1" \
  -H "user_id: 1"
```

---

### Step 6: Grant Permissions to Staff (As Owner)

**Endpoint:** `POST /api/v1/staff/{staff_id}/permissions/`

```bash
# Grant create product permission
curl -X POST "http://127.0.0.1:8000/api/v1/staff/2/permissions/?permission_name=create_product" \
  -H "user_id: 1"

# Grant view reports permission
curl -X POST "http://127.0.0.1:8000/api/v1/staff/2/permissions/?permission_name=view_reports" \
  -H "user_id: 1"
```

---

### Step 7: Login as Staff

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "staff123"
  }'
```

**Response:**
```json
{
  "user_id": 2,
  "username": "john_doe",
  "email": "john@example.com",
  "role": "STAFF",
  "branch_id": 1,
  "message": "Welcome back, john_doe! Role: STAFF"
}
```

---

## How to Use Authentication

After login, include the `user_id` from the login response in your request headers:

```bash
# As Owner
curl http://127.0.0.1:8000/api/v1/staff/branches/ \
  -H "user_id: 1"

# As Staff
curl http://127.0.0.1:8000/api/v1/queue/ \
  -H "user_id: 2"
```

---

## Available Endpoints

### Authentication (`/api/v1/auth`)
- `POST /login` - Login
- `POST /register-owner` - Register owner (first time only)
- `GET /me?user_id={id}` - Get current user info
- `POST /logout` - Logout

### Owner Management (`/api/v1/staff`) - Requires Owner Role
- `POST /branches/` - Create branch
- `GET /branches/` - List branches
- `POST /staff/` - Create staff
- `GET /staff/` - List all staff
- `POST /staff/{id}/assign-branch` - Assign staff to branch
- `POST /staff/{id}/permissions/` - Grant permission

### Staff Operations (`/api/v1`) - Requires Staff Role
- `GET /queue/` - View print queue
- `GET /queue/{job_code}/download/` - Download print job
- `POST /queue/{job_code}/print/` - Print document

---

## Common Permissions

Grant these to staff as needed:
- `create_product` - Can add products
- `view_reports` - Can view reports
- `refund_order` - Can process refunds
- `manage_settings` - Can change settings
- `print_document` - Can print jobs

---

## Testing Flow

1. **Register owner** → Get owner user_id
2. **Login as owner** → Verify credentials
3. **Create branch** → Get branch_id
4. **Create staff** → Get staff user_id
5. **Assign staff to branch** → Link staff to location
6. **Grant permissions** → Give staff access rights
7. **Login as staff** → Test staff access
8. **Access protected endpoints** → Verify roles work

---

## Security Notes

⚠️ **Current Implementation (Demo):**
- Passwords stored as plain text
- Authentication via simple user_id header
- No token expiration

✅ **Production Requirements:**
- Use bcrypt for password hashing
- Implement JWT tokens
- Add rate limiting on login
- Use HTTPS only
- Add session management
- Implement refresh tokens
