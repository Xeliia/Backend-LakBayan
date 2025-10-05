# LakBayan Backend API Documentation

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
**Description:** Get all verified terminals in a specific city  
**Authentication:** Not required  

**Example:** `GET /terminals/city/1/`

**Response (200 OK):**
```json
[
    {
        "id": 1,
        "name": "EDSA Bus Terminal",
        "description": "Main bus terminal for northbound trips",
        "latitude": 14.6091,
        "longitude": 121.0223,
        "city": {
            "id": 1,
            "name": "Quezon City",
            "region": 1
        },
        "verified": true,
        "rating": 4.2,
        "routes": [
            {
                "id": 1,
                "mode": {
                    "id": 1,
                    "mode_name": "BUS",
                    "mode_display": "Bus",
                    "fare_type": "FIXED"
                },
                "verified": true,
                "description": "Quezon City to Baguio Route",
                "polyline": "encoded_polyline_string...",
                "stops": [
                    {
                        "id": 1,
                        "stop_name": "EDSA Terminal",
                        "fare": 450.00,
                        "distance": 0.0,
                        "time": 0,
                        "order": 1,
                        "latitude": 14.6091,
                        "longitude": 121.0223,
                        "terminal": 1
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

**Example:** `GET /terminals/nearby/?lat=14.6091&lng=121.0223&radius=10`

**Response (200 OK):**
```json
[
    {
        "id": 1,
        "name": "EDSA Bus Terminal",
        "description": "Main bus terminal for northbound trips",
        "latitude": 14.6091,
        "longitude": 121.0223,
        "city": {
            "id": 1,
            "name": "Quezon City",
            "region": 1
        },
        "verified": true,
        "rating": 4.2,
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
            "name": "National Capital Region",
            "cities": [
                {
                    "id": 1,
                    "name": "Parañaque City",
                    "region": 1,
                    "terminals": [
                        {
                            "id": 1,
                            "name": "PITX (Parañaque Integrated Terminal Exchange)",
                            "description": "Main terminal with multiple transport modes",
                            "latitude": "14.507800",
                            "longitude": "121.018700",
                            "city": 1,
                            "verified": true,
                            "rating": 5,
                            "origin_routes": [
                                {
                                    "id": 1,
                                    "mode": {
                                        "id": 1,
                                        "mode_name": "bus",
                                        "fare_type": "fixed"
                                    },
                                    "verified": true,
                                    "description": "PITX to Baguio Bus Route",
                                    "polyline": null,
                                    "stops": [
                                        {
                                            "id": 1,
                                            "stop_name": "PITX Terminal",
                                            "terminal": 1,
                                            "fare": "0.00",
                                            "distance": "0.00",
                                            "time": 0,
                                            "order": 1,
                                            "latitude": "14.507800",
                                            "longitude": "121.018700"
                                        },
                                        {
                                            "id": 2,
                                            "stop_name": "Baguio Terminal",
                                            "terminal": 5,
                                            "fare": "450.00",
                                            "distance": "250.00",
                                            "time": 360,
                                            "order": 2,
                                            "latitude": "16.407400",
                                            "longitude": "120.596000"
                                        }
                                    ]
                                },
                                {
                                    "id": 2,
                                    "mode": {
                                        "id": 2,
                                        "mode_name": "jeepney",
                                        "fare_type": "distance_based"
                                    },
                                    "verified": true,
                                    "description": "PITX to Alabang Jeepney Route",
                                    "polyline": null,
                                    "stops": [
                                        {
                                            "id": 3,
                                            "stop_name": "PITX Terminal",
                                            "terminal": 1,
                                            "fare": "0.00",
                                            "distance": "0.00",
                                            "time": 0,
                                            "order": 1,
                                            "latitude": "14.507800",
                                            "longitude": "121.018700"
                                        },
                                        {
                                            "id": 4,
                                            "stop_name": "Alabang Terminal",
                                            "terminal": 3,
                                            "fare": "15.00",
                                            "distance": "8.50",
                                            "time": 25,
                                            "order": 2,
                                            "latitude": "14.422200",
                                            "longitude": "121.042100"
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
    "last_updated": "2025-10-05T15:30:00.123456Z",
    "total_terminals": 150,
    "total_routes": 75,
    "export_timestamp": "2025-10-05T15:35:00.123456Z"
}
```

### 2. Data Export Metadata
**Endpoint:** `GET /metadata/`  
**Description:** Get metadata about the transportation data  
**Authentication:** Not required  

**Response (200 OK):**
```json
{
    "last_updated": "2025-10-05T15:30:00.123456Z",
    "total_terminals": 150,
    "total_routes": 75
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