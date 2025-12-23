# Multi-Owner System Guide

## Overview
The system now supports **multiple independent owners**, each managing their own:
- Branches/Stores
- Staff members
- Permissions
- Operations

Each owner's data is completely isolated from other owners.

---

## Quick Setup for Multiple Owners

### Owner 1: Register & Setup

**Step 1: Register First Owner**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register-owner \
  -H "Content-Type: application/json" \
  -d '{
    "username": "owner1",
    "email": "owner1@example.com",
    "password": "pass123",
    "role": "OWNER"
  }'
```

**Step 2: Login**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "owner1",
    "password": "pass123"
  }'
```
Response: `{"user_id": 1, ...}`

**Step 3: Create Branch**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/staff/branches/ \
  -H "Content-Type: application/json" \
  -H "user_id: 1" \
  -d '{
    "name": "Owner1 Downtown Store",
    "location": "123 Main St",
    "phone": "555-0001"
  }'
```

**Step 4: Create Staff**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/staff/ \
  -H "Content-Type: application/json" \
  -H "user_id: 1" \
  -d '{
    "username": "staff_owner1",
    "email": "staff1@example.com",
    "password": "staff123",
    "role": "STAFF"
  }'
```

---

### Owner 2: Register & Setup

**Step 1: Register Second Owner**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register-owner \
  -H "Content-Type: application/json" \
  -d '{
    "username": "owner2",
    "email": "owner2@example.com",
    "password": "pass456",
    "role": "OWNER"
  }'
```

**Step 2: Login**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "owner2",
    "password": "pass456"
  }'
```
Response: `{"user_id": 3, ...}`

**Step 3: Create Branch**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/staff/branches/ \
  -H "Content-Type: application/json" \
  -H "user_id: 3" \
  -d '{
    "name": "Owner2 Mall Outlet",
    "location": "456 Shopping Blvd",
    "phone": "555-0002"
  }'
```

---

## Data Isolation

### What Each Owner Can See/Manage:

✅ **Owner can:**
- Create unlimited branches under their account
- Create staff and assign to their branches
- View only their own branches
- View only staff in their branches
- Grant permissions to their staff only
- View dashboard with their data

❌ **Owner cannot:**
- See other owners' branches
- See other owners' staff
- Manage other owners' resources
- Access other owners' data

---

## New Endpoint: Owner Dashboard

**GET /api/v1/staff/owner/dashboard**

Shows owner's summary:
```bash
curl http://127.0.0.1:8000/api/v1/staff/owner/dashboard \
  -H "user_id: 1"
```

Response:
```json
{
  "owner_name": "owner1",
  "owner_email": "owner1@example.com",
  "total_branches": 2,
  "total_staff": 5,
  "branches": [
    {
      "id": 1,
      "name": "Downtown Store",
      "location": "123 Main St",
      "is_active": true
    }
  ]
}
```

---

## Testing Multi-Owner Isolation

**1. Create two owners**
```bash
# Owner A
curl -X POST http://127.0.0.1:8000/api/v1/auth/register-owner \
  -H "Content-Type: application/json" \
  -d '{"username":"ownerA","email":"a@mail.com","password":"123","role":"OWNER"}'

# Owner B
curl -X POST http://127.0.0.1:8000/api/v1/auth/register-owner \
  -H "Content-Type: application/json" \
  -d '{"username":"ownerB","email":"b@mail.com","password":"456","role":"OWNER"}'
```

**2. Login both owners**
```bash
# Get user_id for Owner A (e.g., user_id: 1)
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"ownerA","password":"123"}'

# Get user_id for Owner B (e.g., user_id: 2)
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"ownerB","password":"456"}'
```

**3. Each creates a branch**
```bash
# Owner A creates branch
curl -X POST http://127.0.0.1:8000/api/v1/staff/branches/ \
  -H "user_id: 1" \
  -H "Content-Type: application/json" \
  -d '{"name":"Store A","location":"City A"}'

# Owner B creates branch
curl -X POST http://127.0.0.1:8000/api/v1/staff/branches/ \
  -H "user_id: 2" \
  -H "Content-Type: application/json" \
  -d '{"name":"Store B","location":"City B"}'
```

**4. Verify isolation**
```bash
# Owner A sees only Store A
curl http://127.0.0.1:8000/api/v1/staff/branches/ -H "user_id: 1"

# Owner B sees only Store B
curl http://127.0.0.1:8000/api/v1/staff/branches/ -H "user_id: 2"
```

---

## Use Cases

### Single Owner, Multiple Branches
- One owner with multiple store locations
- Centralized management
- Example: Coffee shop chain

### Multiple Independent Owners
- Platform hosting multiple businesses
- Each owner manages their own operations
- Example: SaaS POS system

### Franchise Model
- Multiple franchise owners
- Each owner has their own branches
- Independent operations

---

## Summary of Changes

1. ✅ Removed single owner restriction
2. ✅ Added owner dashboard endpoint
3. ✅ Scoped branch listing to owner
4. ✅ Scoped staff listing to owner's branches
5. ✅ Added ownership verification for permissions
6. ✅ Complete data isolation between owners
