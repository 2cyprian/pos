# Role-Based Access Control (RBAC) Implementation

## Overview
Implemented complete role-based access control system with two main roles:
- **OWNER**: Full system access, can manage branches and staff
- **STAFF**: Can access assigned branch operations

## New Models Added

### 1. User Model (`app/models.py`)
- `username` (unique)
- `email` (unique)
- `password_hash` (for authentication)
- `role`: "OWNER" or "STAFF"
- `branch_id`: Optional, STAFF assigned to a branch
- `is_active`: Boolean status

### 2. Branch Model (`app/models.py`)
- `name`: Branch name
- `location`: Address
- `phone`: Contact number
- `owner_id`: Foreign key to User (owner)
- `is_active`: Boolean status
- Relationships: staff assigned to branch

### 3. Permission Model (`app/models.py`)
- `user_id`: Foreign key to User
- `permission_name`: String (e.g., "create_product", "view_reports")
- Fine-grained access control for STAFF

## New Authentication Module

### `app/utils/auth.py`
Provides three dependency functions:

1. **`get_current_user(user_id)`**
   - Authenticates and returns current user
   - Pass `?user_id=1` in request for demo

2. **`require_owner`**
   - Only OWNER role can access
   - Raises 403 Forbidden for STAFF

3. **`require_staff`**
   - STAFF or OWNER can access
   - Raises 403 Forbidden for others

## New Endpoints

### Owner Management Endpoints
All require `require_owner` dependency:

#### Branches
- `POST /api/v1/staff/branches/` - Create branch
- `GET /api/v1/staff/branches/` - List owner's branches

#### Staff Management
- `POST /api/v1/staff/` - Create staff member
- `GET /api/v1/staff/` - List all staff
- `POST /api/v1/staff/{staff_id}/assign-branch` - Assign staff to branch
- `POST /api/v1/staff/{staff_id}/permissions/` - Grant permission to staff

### Staff Endpoints
All require `require_staff` dependency:

- `GET /api/v1/queue/` - View print queue
- `GET /api/v1/queue/{job_code}/download/` - Download print job
- `POST /api/v1/queue/{job_code}/print/` - Print job

## Usage Examples

### As OWNER:

**Create a branch:**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/staff/branches/ \
  -H "Content-Type: application/json" \
  -H "user_id: 1" \
  -d '{
    "name": "Downtown Store",
    "location": "123 Main St",
    "phone": "555-1234"
  }'
```

**Create staff member:**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/staff/ \
  -H "Content-Type: application/json" \
  -H "user_id: 1" \
  -d '{
    "username": "john_staff",
    "email": "john@example.com",
    "password": "secure_password",
    "role": "STAFF"
  }'
```

**Assign staff to branch:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/staff/2/assign-branch?branch_id=1" \
  -H "user_id: 1"
```

**Grant permission:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/staff/2/permissions/?permission_name=create_product" \
  -H "user_id: 1"
```

### As STAFF:

**View print queue:**
```bash
curl http://127.0.0.1:8000/api/v1/queue/ \
  -H "user_id: 2"
```

**Print a job:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/queue/JOB123/print/?printer_name=Printer1" \
  -H "user_id: 2"
```

## Permission Names
Common permissions for STAFF:
- `create_product` - Add new product
- `view_reports` - View reports
- `refund_order` - Process refunds
- `manage_settings` - Change settings
- `print_document` - Print jobs

## Future Enhancements
- [ ] JWT token-based authentication (replace user_id header)
- [ ] Password hashing with bcrypt
- [ ] Role-based permission templates
- [ ] Audit logging
- [ ] API key generation for integrations
