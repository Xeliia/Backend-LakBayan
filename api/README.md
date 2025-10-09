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

## 🛣️ User Contributions (Email Verification Required)

**All contribution endpoints require:**
1. **Authentication** (JWT token in Authorization header)
2. **Email Verification** (user must have verified their email address)

### 1. Contribute Terminal
**Endpoint:** `POST /contribute/terminal/`  
**Description:** Submit new terminal for admin verification  
**Authentication:** Required + Email Verified  

**Request Body:**
```json
{
    "name": "Biñan JAC Liner Terminal",
    "description": "Buses going to Metro Manila",
    "latitude": 14.339165,
    "longitude": 121.081884,
    "city": 1
}
```

**Response (201 Created):**
```json
{
    "message": "Terminal contribution submitted successfully",
    "terminal_id": 42,
    "status": "pending_verification",
    "data": {
        "name": "Biñan JAC Liner Terminal",
        "description": "Buses going to Metro Manila",
        "latitude": "14.339165",
        "longitude": "121.081884",
        "city": 1
    }
}
```

**Error (403 Forbidden) - Email Not Verified:**
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

**Validation Requirements:**
- `name`: Terminal name (required)
- `description`: Terminal description (optional)
- `latitude`: Must be between -90 and 90 (required)
- `longitude`: Must be between -180 and 180 (required)
- `city`: Must be a valid city ID (required)

### 2. Contribute Route
**Endpoint:** `POST /contribute/route/`  
**Description:** Submit new route to verified terminal  
**Authentication:** Required + Email Verified  

**Request Body:**
```json
{
    "terminal": 1,
    "destination_name": "Gil Puyat LRT Station",
    "mode": 3,
    "description": "Route to Gil Puyat LRT",
    "polyline": null
}
```

**Response (201 Created):**
```json
{
    "message": "Route contribution submitted successfully",
    "route_id": 25,
    "status": "pending_verification",
    "data": {
        "terminal": 1,
        "destination_name": "Gil Puyat LRT Station",
        "mode": 3,
        "description": "Route to Gil Puyat LRT",
        "polyline": null
    }
}
```

**Error (400 Bad Request) - Invalid Terminal:**
```json
{
    "terminal": ["Can only add routes to verified terminals"]
}
```

**Validation Requirements:**
- `terminal`: Must be a verified terminal ID (required)
- `destination_name`: Route destination (required)
- `mode`: Must be a valid transport mode ID (required)
- `description`: Route description (optional)
- `polyline`: GPS coordinates array (optional)

### 3. Contribute Route Stop
**Endpoint:** `POST /contribute/stop/`  
**Description:** Submit new stop to verified route  
**Authentication:** Required + Email Verified  

**Request Body:**
```json
{
    "route": 1,
    "stop_name": "Magallanes Station",
    "fare": 66.00,
    "distance": 32.7,
    "time": 120,
    "order": 1,
    "latitude": 14.539757,
    "longitude": 121.017421,
    "terminal": null
}
```

**Response (201 Created):**
```json
{
    "message": "Route stop contribution submitted successfully",
    "stop_id": 15,
    "data": {
        "route": 1,
        "stop_name": "Magallanes Station",
        "fare": "66.00",
        "distance": "32.70",
        "time": 120,
        "order": 1,
        "latitude": "14.539757",
        "longitude": "121.017421",
        "terminal": null
    }
}
```

**Error (400 Bad Request) - Invalid Route:**
```json
{
    "route": ["Can only add stops to verified routes"],
    "order": ["A stop with this order already exists for this route"]
}
```

**Validation Requirements:**
- `route`: Must be a verified route ID (required)
- `stop_name`: Name of the stop (required)
- `fare`: Fare to this stop in PHP (required)
- `distance`: Distance from origin in km (optional)
- `time`: Travel time from origin in minutes (optional)
- `order`: Stop sequence number (required, must be unique per route)
- `latitude`: Stop latitude -90 to 90 (required)
- `longitude`: Stop longitude -180 to 180 (required)
- `terminal`: Terminal ID if stop is at a terminal (optional)

### 4. Contribute Complete Route
**Endpoint:** `POST /contribute/complete-route/`  
**Description:** Submit route with multiple stops in one request  
**Authentication:** Required + Email Verified  

**Request Body:**
```json
{
    "route": {
        "terminal": 1,
        "destination_name": "Manila City Hall",
        "mode": 3,
        "description": "Complete route to Manila",
        "polyline": null
    },
    "stops": [
        {
            "stop_name": "First Stop",
            "fare": 25.00,
            "distance": 5.0,
            "time": 30,
            "order": 1,
            "latitude": 14.1234,
            "longitude": 121.1234,
            "terminal": null
        },
        {
            "stop_name": "Second Stop", 
            "fare": 45.00,
            "distance": 15.0,
            "time": 60,
            "order": 2,
            "latitude": 14.2345,
            "longitude": 121.2345,
            "terminal": null
        }
    ]
}
```

**Response (201 Created):**
```json
{
    "message": "Complete route with stops submitted successfully",
    "route_id": 26,
    "stops_count": 2,
    "status": "pending_verification"
}
```

**Error Responses:**
```json
{
    "error": "Invalid route data",
    "route_errors": {
        "terminal": ["Can only add routes to verified terminals"]
    }
}
```

```json
{
    "error": "Invalid stop data",
    "stop_errors": {
        "order": ["A stop with this order already exists for this route"]
    }
}
```

### 5. Contribute Everything (Terminal + Route + Stops) ⭐ **NEW**
**Endpoint:** `POST /contribute/everything/`  
**Description:** Submit complete transportation data: terminal, route, and stops all together  
**Authentication:** Required + Email Verified  

**Use Case:** When user wants to add a completely new terminal with its routes and stops

**Request Body:**
```json
{
    "terminal": {
        "name": "New Complete Terminal",
        "description": "Brand new terminal with complete route info",
        "latitude": 14.1234,
        "longitude": 121.1234,
        "city": 1
    },
    "route": {
        "destination_name": "Final Destination",
        "mode": 3,
        "description": "Complete route description",
        "polyline": null
    },
    "stops": [
        {
            "stop_name": "First Stop",
            "fare": 25.00,
            "distance": 5.0,
            "time": 30,
            "order": 1,
            "latitude": 14.1111,
            "longitude": 121.1111,
            "terminal": null
        },
        {
            "stop_name": "Second Stop",
            "fare": 45.00,
            "distance": 15.0,
            "time": 60,
            "order": 2,
            "latitude": 14.2222,
            "longitude": 121.2222,
            "terminal": null
        },
        {
            "stop_name": "Final Stop",
            "fare": 75.00,
            "distance": 25.0,
            "time": 90,
            "order": 3,
            "latitude": 14.3333,
            "longitude": 121.3333,
            "terminal": null
        }
    ]
}
```

**Response (201 Created):**
```json
{
    "message": "Complete transportation data submitted successfully",
    "status": "pending_verification",
    "data": {
        "terminal_id": 45,
        "route_id": 30,
        "stops_count": 3,
        "terminal_name": "New Complete Terminal",
        "route_destination": "Final Destination",
        "all_unverified": true,
        "note": "All submissions require admin approval before becoming public"
    }
}
```

**Error Responses:**

**Missing Required Structure (400 Bad Request):**
```json
{
    "error": "Required structure: {\"terminal\": {...}, \"route\": {...}, \"stops\": [...]}"
}
```

**Invalid Terminal Data (400 Bad Request):**
```json
{
    "error": "Invalid terminal data",
    "terminal_errors": {
        "name": ["This field is required"],
        "latitude": ["Latitude must be between -90 and 90"]
    }
}
```

**Validation Requirements:**
- **Terminal**: Same as individual terminal contribution
- **Route**: Same as individual route contribution (but terminal will be auto-assigned)
- **Stops**: Same as individual stop contribution (but route will be auto-assigned)
- **All data**: Automatically marked as unverified regardless of input
- **Atomic transaction**: If any part fails, entire submission is rolled back


### 6. My Contributions
**Endpoint:** `GET /my-contributions/`  
**Description:** View your contribution history and status  
**Authentication:** Required  

**Response (200 OK):**
```json
{
    "terminals": {
        "data": [
            {
                "name": "Biñan JAC Liner Terminal",
                "description": "Buses going to Metro Manila",
                "latitude": "14.339165",
                "longitude": "121.081884",
                "city": 1
            }
        ],
        "total": 1,
        "verified": 0,
        "pending": 1
    },
    "routes": {
        "data": [
            {
                "terminal": 1,
                "destination_name": "Gil Puyat LRT Station",
                "mode": 3,
                "description": "Route to Gil Puyat LRT",
                "polyline": null
            }
        ],
        "total": 1,
        "verified": 0,
        "pending": 1
    },
    "summary": {
        "total_contributions": 2,
        "verified_contributions": 0
    }
}
```


### 🎯 **Contribution Types Summary:**

| Endpoint | Purpose | Requirements | What's Created |
|----------|---------|--------------|----------------|
| `/contribute/terminal/` | Add new terminal only | None | Unverified terminal |
| `/contribute/route/` | Add route to existing terminal | Verified terminal | Unverified route |
| `/contribute/stop/` | Add stop to existing route | Verified route | Unverified stop |
| `/contribute/complete-route/` | Add route + stops to terminal | Verified terminal | Unverified route + stops |
| `/contribute/everything/` ⭐ | Add terminal + route + stops | None | All unverified |

### Contribution Workflow:
1. **User registers** → Verification email sent automatically
2. **User verifies email** → Can now contribute
3. **User submits contributions** → Marked as `pending_verification`
4. **Admin reviews** → Approves/rejects contributions
5. **Approved contributions** → Become visible in public API endpoints

### Important Notes:
- **All contributions require email verification** to prevent spam
- **Admin approval required** before contributions become public
- **Sequential stop ordering** enforced for route stops
- **Geographic validation** ensures valid coordinates
- **Atomic operations** ensure data consistency
- **Auto-linking** in `/contribute/everything/` connects terminal → route → stops
- **User can track status** of all their contributions

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