# LakBayan Backend API Documentation

## Summary

**LakBayan** is a comprehensive transportation data API for the Philippines that provides information about terminals, routes, and transportation modes across different regions and cities. The API features **email verification requirements** for user contributions to ensure data quality and prevent spam.

### 🔐 **Authentication & Account Management:**
- `POST /accounts/register/` - Register new user account (sends verification email)
- `POST /accounts/login/` - Authenticate user and get JWT tokens
- `POST /accounts/logout/` - Logout user and blacklist refresh token (requires auth)
- `GET /accounts/profile/` - Get current user's profile (requires auth)
- `PUT /accounts/profile/` - Update current user's profile (requires auth)
- `PATCH /accounts/profile/` - Partially update current user's profile (requires auth)
- `DELETE /accounts/delete/` - Permanently delete user account (requires auth)

### 📧 **Email Verification:**
- `GET /email-verification/status/` - Check current user's email verification status (requires auth)
- `POST /email-verification/resend/` - Resend email verification link (requires auth)

### 🚌 **Terminals:**
- `GET /terminals/city/<city_id>/` - Get all verified terminals in a specific city
- `GET /terminals/region/<region_id>/` - Get all verified terminals in a specific region
- `GET /terminals/nearby/` - Get terminals within specified radius of coordinates

### 🛣️ **User Contributions (Email Verification Required):**
- `POST /contribute/terminal/` - Submit new terminal for verification (requires verified email)
- `POST /contribute/route/` - Submit new route for verification (requires verified email)
- `POST /contribute/stop/` - Submit new route stop for verification (requires verified email)
- `POST /contribute/complete-route/` - Submit complete route with stops (requires verified email)
- `GET /my-contributions/` - View your contribution history (requires auth)

### 🏗️ **Helper Endpoints:**
- `GET /cities/region/<region_id>/` - Get cities in a specific region
- `GET /transport-modes/` - Get available transportation modes

### 📊 **Data Export:**
- `GET /complete/` - Export all verified transportation data
- `GET /metadata/` - Get metadata about the transportation data
- `GET /export/regions-cities/` - Export regions and cities only
- `GET /export/terminals/` - Export all terminals
- `GET /export/routes-stops/` - Export all routes and stops

---

**Key Features:**
- 🔐 **JWT Authentication** - Secure user accounts with access/refresh tokens
- 📧 **Email Verification** - Required for all user contributions to prevent spam
- 🚌 **Terminal Management** - Search terminals by city, region, or proximity
- 🛣️ **Route Contributions** - Users can add terminals, routes, and stops
- 🗺️ **Nested Data Structure** - Complete transportation hierarchy
- ✅ **Admin Verification** - All contributions require admin approval
- 📍 **Location-Based Search** - Find nearby terminals using coordinates
- 🇵🇭 **Philippine Focus** - Designed for Philippine transportation systems

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
**Description:** Create a new user account and send verification email  
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
        "date_joined": "2025-10-09T15:30:00.123456Z"
    }
}
```

**Note:** A verification email is automatically sent. User must verify email before contributing.

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

## 📧 Email Verification

### 1. Check Email Verification Status
**Endpoint:** `GET /email-verification/status/`  
**Description:** Check if current user's email is verified  
**Authentication:** Required  

**Response (200 OK) - Verified:**
```json
{
    "email_verified": true,
    "email": "test@example.com",
    "username": "testuser",
    "primary_email": "test@example.com"
}
```

**Response (200 OK) - Not Verified:**
```json
{
    "email_verified": false,
    "email": null,
    "username": "testuser", 
    "primary_email": "test@example.com"
}
```

### 2. Resend Verification Email
**Endpoint:** `POST /email-verification/resend/`  
**Description:** Resend email verification link  
**Authentication:** Required  

**Response (200 OK) - Email Sent:**
```json
{
    "message": "Verification email sent successfully",
    "email": "test@example.com"
}
```

**Response (200 OK) - Already Verified:**
```json
{
    "message": "Email is already verified",
    "email_verified": true
}
```

**Rate Limiting:** Maximum 1 verification email per 3 minutes per user.

---

## 🚌 Terminal Management

### 1. Get Terminals by City
**Endpoint:** `GET /terminals/city/<city_id>/`  
**Description:** Get all verified terminals in a specific city with routes and stops  
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

## 🏗️ Helper Endpoints

### 1. Get Cities by Region
**Endpoint:** `GET /cities/region/<region_id>/`  
**Description:** Get cities in a specific region (for contribution forms)  
**Authentication:** Not required  

**Example:** `GET /cities/region/1/`

**Response (200 OK):**
```json
[
    {
        "id": 1,
        "name": "Biñan"
    },
    {
        "id": 2,
        "name": "Calamba"
    }
]
```

### 2. Get Transport Modes
**Endpoint:** `GET /transport-modes/`  
**Description:** Get available transportation modes (for contribution forms)  
**Authentication:** Not required  

**Response (200 OK):**
```json
[
    {
        "id": 1,
        "name": "Jeepney",
        "fare_type": "Minimum"
    },
    {
        "id": 2,
        "name": "Bus",
        "fare_type": "Fixed"
    },
    {
        "id": 3,
        "name": "UV Express",
        "fare_type": "Fixed"
    }
]
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
                                        "mode_display": "Bus",
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
        },
        {
            "id": 2,
            "name": "National Capital Region",
            "cities": [
                {
                    "id": 2,
                    "name": "Makati",
                    "region": 2,
                    "terminals": [
                        {
                            "id": 2,
                            "name": "One Ayala Terminal",
                            "description": "Massive Terminal",
                            "latitude": "14.549810",
                            "longitude": "121.028399",
                            "city": {
                                "id": 2,
                                "name": "Makati",
                                "region": 2
                            },
                            "verified": true,
                            "rating": 0,
                            "routes": []
                        }
                    ]
                },
                {
                    "id": 3,
                    "name": "Pasay",
                    "region": 2,
                    "terminals": [
                        {
                            "id": 3,
                            "name": "Jac Liner Gil Puyat",
                            "description": "Bus papuntang probinsya (Laguna, at batangas)",
                            "latitude": "14.554152",
                            "longitude": "120.996629",
                            "city": {
                                "id": 3,
                                "name": "Pasay",
                                "region": 2
                            },
                            "verified": true,
                            "rating": 0,
                            "routes": []
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
    "last_updated": "2025-10-09T09:07:49.786296Z",
    "total_terminals": 3,
    "total_routes": 1
}
```

### 3. Export Regions and Cities
**Endpoint:** `GET /export/regions-cities/`  
**Description:** Export only regions and cities data  
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
                    "region": 1
                }
            ]
        }
    ],
    "export_timestamp": "2025-10-09T10:15:30.123456Z"
}
```

### 4. Export Terminals
**Endpoint:** `GET /export/terminals/`  
**Description:** Export all verified terminals with routes  
**Authentication:** Not required  

**Response (200 OK):**
```json
{
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
            "routes": []
        }
    ],
    "last_updated": "2025-10-09T09:07:49.786296Z",
    "export_timestamp": "2025-10-09T10:20:15.789123Z"
}
```

### 5. Export Routes and Stops
**Endpoint:** `GET /export/routes-stops/`  
**Description:** Export all routes with their stops  
**Authentication:** Not required  

**Response (200 OK):**
```json
{
    "routes": [
        {
            "id": 1,
            "mode": {
                "id": 3,
                "mode_name": "bus",
                "fare_type": "fixed"
            },
            "terminal": {
                "id": 1,
                "name": "Biñan Jac Liner Terminal"
            },
            "verified": true,
            "description": "Papontang Gil Puyat LRT",
            "stops": [
                {
                    "id": 1,
                    "stop_name": "Magallanes, Pasay",
                    "fare": "66.00",
                    "distance": "32.70",
                    "time": 120,
                    "order": 1,
                    "latitude": "14.539757",
                    "longitude": "121.017421"
                }
            ]
        }
    ],
    "export_timestamp": "2025-10-09T10:25:45.321654Z"
}
```

---

## 🔧 Error Responses

### Validation Errors (400 Bad Request)
```json
{
    "username": ["Username already exists"],
    "password": ["Passwords don't match"],
    "latitude": ["Latitude must be between -90 and 90"]
}
```

### Authentication Required (401 Unauthorized)
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### Email Verification Required (403 Forbidden)
```json
{
    "error": "Email verification required",
    "message": "Please verify your email address before contributing",
    "code": "EMAIL_VERIFICATION_REQUIRED",
    "action": {
        "type": "resend_verification",
        "url": "/accounts/email/"
    }
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

### Rate Limit Exceeded (429 Too Many Requests)
```json
{
    "detail": "Rate limit exceeded. Please try again later."
}
```

### Server Error (500 Internal Server Error)
```json
{
    "error": "Failed to send verification email",
    "details": "SMTP connection failed"
}
```

---

## 📝 Important Notes

### Email Verification System:
- **Registration:** Verification email sent automatically
- **Rate Limiting:** 1 verification email per 3 minutes per user
- **Verification:** One-time verification (permanent once verified)
- **Contributions:** All require verified email address
- **Email Provider:** Uses Gmail SMTP for reliable delivery

### Authentication & Tokens:
- **Access Tokens:** Expire in 60 minutes
- **Refresh Tokens:** Expire in 7 days, rotate on refresh
- **Token Blacklisting:** Logout blacklists refresh tokens
- **Login Attempts:** Maximum 5 failed attempts per 5 minutes

### Data & Verification:
- **User Contributions:** Require email verification + admin approval
- **Public Data:** Only verified terminals and routes returned
- **Geographic Data:** Coordinates in decimal degrees (WGS84)
- **Currency:** All fares in Philippine Pesos (PHP)
- **Time Values:** In minutes from origin terminal

### Rate Limiting:
- **Login Failures:** 5 attempts per 5 minutes
- **Email Verification:** 1 email per 3 minutes
- **API Calls:** No rate limiting on public endpoints

---

## 🚀 Getting Started

### 1. Register Account & Verify Email
```bash
# 1. Register a new account
curl -X POST https://lakbayan-backend.onrender.com/api/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com", 
    "password": "securepass123",
    "password_confirm": "securepass123"
  }'

# 2. Check your email and click verification link

# 3. Login to get tokens
curl -X POST https://lakbayan-backend.onrender.com/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "securepass123"
  }'
```

### 2. Check Email Verification Status
```bash
curl -X GET https://lakbayan-backend.onrender.com/api/email-verification/status/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. Contribute Transportation Data
```bash
# Contribute a new terminal (requires verified email)
curl -X POST https://lakbayan-backend.onrender.com/api/contribute/terminal/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Terminal",
    "description": "Description of terminal",
    "latitude": 14.1234,
    "longitude": 121.1234,
    "city": 1
  }'
```

### 4. View Your Contributions
```bash
curl -X GET https://lakbayan-backend.onrender.com/api/my-contributions/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 5. Get Public Transportation Data
```bash
# Get complete transportation data
curl https://lakbayan-backend.onrender.com/api/complete/

# Find nearby terminals
curl "https://lakbayan-backend.onrender.com/api/terminals/nearby/?lat=14.3392&lng=121.0819&radius=10"

# Get terminals in a specific city
curl https://lakbayan-backend.onrender.com/api/terminals/city/1/
```

---

## 📊 API Summary

### Public Endpoints (No Authentication):
- ✅ Data export endpoints
- ✅ Terminal search endpoints  
- ✅ Helper endpoints (cities, transport modes)

### Protected Endpoints (Authentication Required):
- 🔐 Account management
- 📧 Email verification status/resend
- 📊 User contribution history

### Contribution Endpoints (Authentication + Email Verification):
- 📧✅ Terminal contributions
- 📧✅ Route contributions  
- 📧✅ Route stop contributions
- 📧✅ Complete route contributions

### Email Verification Features:
- 📧 Automatic verification email on registration
- 📧 Manual resend verification email
- 📧 One-time verification (permanent)
- 📧 Rate limiting (3-minute cooldown)
- 📧 Gmail SMTP for reliable delivery

**The LakBayan API provides a complete, secure, and user-friendly system for crowdsourced transportation data in the Philippines with robust email verification to ensure data quality.** 🇵🇭🚌