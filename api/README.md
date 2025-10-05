# LakBayan Backend API Documentation

## Summary

**LakBayan** is a comprehensive transportation data API for the Philippines that provides information about terminals, routes, and transportation modes across different regions and cities.

### 🔐 **Accounts:**
- `POST /accounts/register/` - Register new user account
- `POST /accounts/login/` - Authenticate user and get JWT tokens
- `POST /accounts/logout/` - Logout user and blacklist refresh token (requires auth)
- `GET /accounts/profile/` - Get current user's profile (requires auth)
- `PUT /accounts/profile/` - Update current user's profile (requires auth)
- `PATCH /accounts/profile/` - Partially update current user's profile (requires auth)
- `DELETE /accounts/delete/` - Permanently delete user account (requires auth)

### 🚌 **Terminals:**
- `GET /terminals/city/<city_id>/` - Get all verified terminals in a specific city
- `GET /terminals/region/<region_id>/` - Get all verified terminals in a specific region
- `GET /terminals/nearby/` - Get terminals within specified radius of coordinates (query params: lat, lng, radius)

### 📊 **Data Export:**
- `GET /complete/` - Export all verified transportation data (regions → cities → terminals → routes → route stops)
- `GET /metadata/` - Get metadata about the transportation data (counts and last updated timestamp)

---

**Key Features:**
- 🔐 **JWT Authentication** - Secure user accounts with access/refresh tokens
- 🚌 **Terminal Management** - Search terminals by city, region, or proximity
- 🗺️ **Nested Data Structure** - Complete transportation hierarchy from regions to individual route stops
- ✅ **Verified Data Only** - Public endpoints return only verified terminals and routes
- 📍 **Location-Based Search** - Find nearby terminals using coordinates and radius
- 🇵🇭 **Philippine Focus** - Designed specifically for Philippine transportation systems

---

## Base URL
```
http://127.0.0.1:8000/api/
```

## Authentication
This API uses JWT (JSON Web Token) authentication. Include the access token in the Authorization header:
```
Authorization: Bearer <access_token>
```

---

## 🔐 Account Management

### 1. Register User
**Endpoint:** `POST /accounts/register/`  
**Description:** Create a new user account  
**Authentication:** Not required  

**Request Body:**
```json
{
    "username": "testuser",
    "email": "test@example.com",
    "password": "securepassword123",
    "password_confirm": "securepassword123"
}
```

**Response (201 Created):**
```json
{
    "message": "Account Created Successfully",
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "date_joined": "2025-10-05T15:30:00.123456Z"
    }
}
```

### 2. Login User
**Endpoint:** `POST /accounts/login/`  
**Description:** Authenticate user and get tokens  
**Authentication:** Not required  

**Request Body:**
```json
{
    "username": "testuser",
    "password": "securepassword123"
}
```

**Response (200 OK):**
```json
{
    "message": "Login Successful",
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com"
    }
}
```

### 3. Get User Profile
**Endpoint:** `GET /accounts/profile/`  
**Description:** Get current user's profile information  
**Authentication:** Required  

**Response (200 OK):**
```json
{
    "id": 1,
    "username": "testuser",
    "email": "test@example.com"
}
```

### 4. Update User Profile
**Endpoint:** `PUT /accounts/profile/`  
**Description:** Update current user's profile  
**Authentication:** Required  

**Request Body:**
```json
{
    "email": "newemail@example.com"
}
```

**Response (200 OK):**
```json
{
    "id": 1,
    "username": "testuser",
    "email": "newemail@example.com"
}
```

### 5. Logout User
**Endpoint:** `POST /accounts/logout/`  
**Description:** Logout user and blacklist refresh token  
**Authentication:** Required  

**Request Body:**
```json
{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200 OK):**
```json
{
    "message": "Successfully Logged Out"
}
```

### 6. Delete Account
**Endpoint:** `DELETE /accounts/delete/`  
**Description:** Permanently delete user account  
**Authentication:** Required  

**Request Body:**
```json
{
    "password": "securepassword123"
}
```

**Response (204 No Content):**
```json
{
    "message": "Account deleted successfully"
}
```

---

## 🚌 Terminal Management

### 1. Get Terminals by City
**Endpoint:** `GET /terminals/city/<city_id>/`  
**Description:** Get all verified terminals in a specific city with their routes and stops  
**Authentication:** Not required  

**Example:** `GET /terminals/city/1/`

**Response (200 OK):**
```json
[
    {
        "id": 1,
        "name": "Biñan Jac Liner Terminal",
        "description": "Buses going to gil puyat and one ayala",
        "latitude": "14.339165",
        "longitude": "121.081884",
        "city": {
            "id": 1,
            "name": "Biñan",
            "region": 1
        },
        "verified": true,
        "rating": 0,
        "routes": [
            {
                "id": 1,
                "mode": {
                    "id": 3,
                    "mode_name": "bus",
                    "fare_type": "fixed"
                },
                "verified": true,
                "description": "Papontang Gil Puyat LRT",
                "polyline": null,
                "stops": [
                    {
                        "id": 1,
                        "stop_name": "Magallanes, Pasay",
                        "fare": "66.00",
                        "distance": "32.70",
                        "time": 120,
                        "order": 1,
                        "latitude": "14.539757",
                        "longitude": "121.017421",
                        "terminal": null
                    },
                    {
                        "id": 2,
                        "stop_name": "LRT Buendia",
                        "fare": "66.00",
                        "distance": "33.40",
                        "time": 130,
                        "order": 2,
                        "latitude": "14.554152",
                        "longitude": "120.996629",
                        "terminal": 3
                    }
                ]
            }
        ]
    }
]
```

### 2. Get Terminals by Region
**Endpoint:** `GET /terminals/region/<region_id>/`  
**Description:** Get all verified terminals in a specific region  
**Authentication:** Not required  

**Example:** `GET /terminals/region/1/`

**Response:** Same format as terminals by city

### 3. Get Nearby Terminals
**Endpoint:** `GET /terminals/nearby/`  
**Description:** Get terminals within specified radius of coordinates  
**Authentication:** Not required  

**Query Parameters:**
- `lat` (required): Latitude
- `lng` (required): Longitude  
- `radius` (optional): Radius in kilometers (default: 25)

**Example:** `GET /terminals/nearby/?lat=14.3392&lng=121.0819&radius=10`

**Response (200 OK):**
```json
[
    {
        "id": 1,
        "name": "Biñan Jac Liner Terminal",
        "description": "Buses going to gil puyat and one ayala",
        "latitude": "14.339165",
        "longitude": "121.081884",
        "city": {
            "id": 1,
            "name": "Biñan",
            "region": 1
        },
        "verified": true,
        "rating": 0,
        "routes": []
    }
]
```

**Error Response (400 Bad Request):**
```json
{
    "error": "lat and lng parameters are required"
}
```

---

## 📊 Data Export

### 1. Complete Data Export
**Endpoint:** `GET /complete/`  
**Description:** Export all verified transportation data with proper nesting: regions → cities → terminals → routes → route stops  
**Authentication:** Not required  

**Response (200 OK):**
```json
{
    "regions": [
        {
            "id": 1,
            "name": "Laguna",
            "cities": [
                {
                    "id": 1,
                    "name": "Biñan",
                    "region": 1,
                    "terminals": [
                        {
                            "id": 1,
                            "name": "Biñan Jac Liner Terminal",
                            "description": "Buses going to gil puyat and one ayala",
                            "latitude": "14.339165",
                            "longitude": "121.081884",
                            "city": {
                                "id": 1,
                                "name": "Biñan",
                                "region": 1
                            },
                            "verified": true,
                            "rating": 0,
                            "routes": [
                                {
                                    "id": 1,
                                    "mode": {
                                        "id": 3,
                                        "mode_name": "bus",
                                        "fare_type": "fixed"
                                    },
                                    "verified": true,
                                    "description": "Papontang Gil Puyat LRT",
                                    "polyline": null,
                                    "stops": [
                                        {
                                            "id": 1,
                                            "stop_name": "Magallanes, Pasay",
                                            "fare": "66.00",
                                            "distance": "32.70",
                                            "time": 120,
                                            "order": 1,
                                            "latitude": "14.539757",
                                            "longitude": "121.017421",
                                            "terminal": null
                                        },
                                        {
                                            "id": 2,
                                            "stop_name": "LRT Buendia",
                                            "fare": "66.00",
                                            "distance": "33.40",
                                            "time": 130,
                                            "order": 2,
                                            "latitude": "14.554152",
                                            "longitude": "120.996629",
                                            "terminal": 3
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ],
    "last_updated": "2025-10-05T09:07:49.786296Z",
    "total_terminals": 3,
    "total_routes": 1,
    "export_timestamp": "2025-10-05T09:39:30.442051Z"
}
```

### 2. Data Export Metadata
**Endpoint:** `GET /metadata/`  
**Description:** Get metadata about the transportation data  
**Authentication:** Not required  

**Response (200 OK):**
```json
{
    "last_updated": "2025-10-05T09:07:49.786296Z",
    "total_terminals": 3,
    "total_routes": 1
}
```

---

## 🔧 Error Responses

### Validation Errors (400 Bad Request)
```json
{
    "username": ["Username already exists"],
    "password": ["Passwords don't match"]
}
```

### Authentication Required (401 Unauthorized)
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### Permission Denied (403 Forbidden)
```json
{
    "detail": "You do not have permission to perform this action."
}
```

### Not Found (404 Not Found)
```json
{
    "detail": "Not found."
}
```

### Method Not Allowed (405 Method Not Allowed)
```json
{
    "detail": "Method \"GET\" not allowed."
}
```

---

## 📝 Notes

- All timestamps are in ISO 8601 format (UTC)
- JWT access tokens expire in 60 minutes
- JWT refresh tokens expire in 7 days
- Only verified terminals and routes are returned in public endpoints
- Coordinates are in decimal degrees (WGS84)
- Distance calculations use simple bounding box approximation
- All monetary values (fares) are in Philippine Pesos (PHP)
- Time values in route stops are in minutes from origin
- Route stops are ordered sequentially (order field)

---

## 🚀 Getting Started

1. **Register a new account:**
   ```bash
   curl -X POST http://127.0.0.1:8000/api/accounts/register/ \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","email":"test@example.com","password":"pass123","password_confirm":"pass123"}'
   ```

2. **Login to get tokens:**
   ```bash
   curl -X POST http://127.0.0.1:8000/api/accounts/login/ \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","password":"pass123"}'
   ```

3. **Use the access token for protected endpoints:**
   ```bash
   curl -X GET http://127.0.0.1:8000/api/accounts/profile/ \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
   ```

4. **Get complete transportation data:**
   ```bash
   curl http://127.0.0.1:8000/api/complete/
   ```

5. **Find nearby terminals:**
   ```bash
   curl "http://127.0.0.1:8000/api/terminals/nearby/?lat=14.3392&lng=121.0819&radius=10"
   ```