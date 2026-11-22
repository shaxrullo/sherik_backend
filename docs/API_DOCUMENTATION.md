# Backend Sherik API Documentation

Sherik Topish - Talabalar va ishlovchilar uchun uy-joy va sherik topish platformasi.

## API Overview

**Base URL**: `https://sherik-backend.onrender.com` (Production)  
**Base URL**: `http://localhost:8000` (Development)

**API Version**: v1

**Authentication**: JWT Token-based

## Endpoints Overview

### Health & Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health/` | Service health check |
| GET | `/ready/` | Service readiness check |
| GET | `/alive/` | Service liveness check |
| GET | `/monitoring/status/` | Monitoring configuration status |

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login/` | User login (get JWT token) |
| POST | `/api/v1/auth/register/` | User registration |
| POST | `/api/v1/auth/refresh/` | Refresh JWT token |
| POST | `/api/v1/auth/logout/` | User logout |

### Listings (E'lonlar)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/listings/` | List all approved listings (public) |
| POST | `/api/v1/listings/` | Create new listing (authenticated) |
| GET | `/api/v1/listings/{id}/` | Get listing details |
| PATCH | `/api/v1/listings/{id}/` | Update listing (owner only) |
| DELETE | `/api/v1/listings/{id}/` | Delete listing (owner only) |
| GET | `/api/v1/listings/my/` | Get my listings (authenticated) |
| POST | `/api/v1/listings/{id}/photos/upload/` | Upload listing photo |
| DELETE | `/api/v1/listings/photos/{id}/` | Delete listing photo |

### Favorites (Sevimlilar)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/favorites/` | Get my favorites |
| POST | `/api/v1/favorites/add` | Add listing to favorites |
| POST | `/api/v1/favorites/toggle` | Toggle favorite status |
| DELETE | `/api/v1/favorites/remove/{id}/` | Remove from favorites |
| POST | `/api/v1/favorites/clear` | Clear all favorites |

### Reports (Shikoyatlar)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/reports/` | Get my reports |
| POST | `/api/v1/reports/` | Create new report |

### Matching (Moslik Tavsiyalari)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/matching/recommendations` | Get recommended listings |
| GET | `/api/v1/matching/{id}/` | Check listing match score |

---

## Detailed Endpoint Documentation

### Authentication

#### Login

**Endpoint**: `POST /api/v1/auth/login/`

**Request**:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response** (200 OK):
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "phone_number": "+998901234567"
  }
}
```

**Error** (400 Bad Request):
```json
{
  "status": "error",
  "code": "AUTHENTICATION_FAILED",
  "message": "Invalid email or password",
  "timestamp": "2025-11-22T10:30:00Z"
}
```

#### Register

**Endpoint**: `POST /api/v1/auth/register/`

**Request**:
```json
{
  "email": "newuser@example.com",
  "phone_number": "+998901234567",
  "password": "securepass123",
  "first_name": "Ali",
  "last_name": "Vali"
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "email": "newuser@example.com",
  "phone_number": "+998901234567",
  "first_name": "Ali",
  "last_name": "Vali",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

### Listings

#### List All Listings

**Endpoint**: `GET /api/v1/listings/`

**Query Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `city_slug` | string | Filter by city (e.g., `tashkent`) |
| `min_price` | integer | Minimum price |
| `max_price` | integer | Maximum price |
| `gender_preference` | string | `male`, `female`, `any` |
| `listing_type` | string | `have_room`, `need_room` |
| `page` | integer | Page number (default: 1) |
| `page_size` | integer | Results per page (default: 10) |

**Example Request**:
```
GET /api/v1/listings/?city_slug=tashkent&min_price=1000000&max_price=2000000&page=1
```

**Response** (200 OK):
```json
{
  "count": 150,
  "next": "https://api.example.com/listings/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Room in Chilanzar",
      "description": "Spacious room with all amenities",
      "listing_type": "have_room",
      "city": {
        "id": 1,
        "name": "Tashkent",
        "slug": "tashkent"
      },
      "district": {
        "id": 5,
        "name": "Chilanzar"
      },
      "price": 1500000,
      "currency": "UZS",
      "gender_preference": "any",
      "amenities": ["Wi-Fi", "Air Conditioning", "Washing Machine"],
      "photos": [
        {
          "id": 1,
          "image": "https://example.com/media/listings/room1.jpg",
          "is_main": true
        }
      ],
      "author": {
        "id": 2,
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": null  // Hidden from anonymous users
      },
      "status": "active",
      "moderation_status": "approved",
      "created_at": "2025-11-20T10:30:00Z",
      "is_favorited": false
    }
  ]
}
```

#### Create Listing

**Endpoint**: `POST /api/v1/listings/`

**Authentication**: Required (Bearer Token)

**Request**:
```json
{
  "title": "Beautiful room in Yunusobod",
  "description": "Bright, spacious room with all amenities. Near metro.",
  "listing_type": "have_room",
  "city_id": 1,
  "district_id": 5,
  "address_line": "Yunusobod, 20-microraiyan, 12-uy",
  "price": 1800000,
  "currency": "UZS",
  "capacity": 1,
  "gender_preference": "any",
  "amenities": ["Wi-Fi", "Air Conditioning", "Kitchen", "Bathroom"],
  "near_subway": "Yunusobod",
  "nearby_universities": ["TATU", "OzMU"]
}
```

**Response** (201 Created):
```json
{
  "id": 123,
  "title": "Beautiful room in Yunusobod",
  "description": "Bright, spacious room with all amenities. Near metro.",
  "listing_type": "have_room",
  "city_id": 1,
  "district_id": 5,
  "price": 1800000,
  "currency": "UZS",
  "capacity": 1,
  "gender_preference": "any",
  "status": "active",
  "moderation_status": "pending",  // Will be approved after verification
  "created_at": "2025-11-22T10:30:00Z"
}
```

**Errors**:
```json
{
  "status": "error",
  "code": "VALIDATION_ERROR",
  "message": "Validation failed",
  "details": {
    "district_id": ["District does not belong to selected city"],
    "price": ["Ensure this value is greater than or equal to 0"]
  }
}
```

#### Get My Listings

**Endpoint**: `GET /api/v1/listings/my/`

**Authentication**: Required

Shows all your listings (including pending ones awaiting moderation).

**Response** (200 OK):
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 123,
      "title": "My first listing",
      "moderation_status": "pending",
      "status": "active",
      ...
    }
  ]
}
```

---

### Matching / Recommendations

#### Get Recommendations

**Endpoint**: `GET /api/v1/matching/recommendations`

**Authentication**: Required

Returns listings sorted by match score (0-100%).

**Query Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `min_score` | integer | Minimum match score (0-100) |
| `refresh` | boolean | Bypass cache and recalculate |
| `page` | integer | Page number |

**Example Request**:
```
GET /api/v1/matching/recommendations?min_score=70&page=1
```

**Response** (200 OK):
```json
{
  "count": 42,
  "results": [
    {
      "listing": {
        "id": 456,
        "title": "Perfect match room",
        ...
      },
      "match_score": 92,
      "match_breakdown": {
        "location": 30,
        "gender": 25,
        "lifestyle": 24,
        "type": 13
      },
      "match_details": [
        "Shahar bir xil (+20 ball)",
        "Jins mos keldi (female) (+25 ball)",
        "Chekishga munosabat bir xil (+8 ball)",
        "E'lon turi sizning rolingizga to'liq mos (+15 ball)"
      ]
    }
  ]
}
```

#### Check Single Listing Match

**Endpoint**: `GET /api/v1/matching/{id}/`

**Authentication**: Required

Check match score for a specific listing.

**Response** (200 OK):
```json
{
  "listing_id": 456,
  "listing_title": "Perfect match room",
  "match_score": 92,
  "match_breakdown": {
    "location": 30,
    "gender": 25,
    "lifestyle": 24,
    "type": 13
  },
  "match_details": [
    "Shahar bir xil (+20 ball)",
    "Jins mos keldi (female) (+25 ball)"
  ]
}
```

---

### Favorites

#### Add to Favorites

**Endpoint**: `POST /api/v1/favorites/add`

**Request**:
```json
{
  "listing_id": 456
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "listing_id": 456,
  "created_at": "2025-11-22T10:30:00Z"
}
```

#### Toggle Favorite

**Endpoint**: `POST /api/v1/favorites/toggle`

Automatically adds if not favorited, removes if already favorited.

**Request**:
```json
{
  "listing_id": 456
}
```

**Response** (200 OK):
```json
{
  "is_favorited": true,
  "action": "added"  // or "removed"
}
```

#### Get My Favorites

**Endpoint**: `GET /api/v1/favorites/`

**Response** (200 OK):
```json
{
  "count": 15,
  "results": [
    {
      "id": 1,
      "listing": {
        "id": 456,
        "title": "Room in Chilanzar",
        ...
      },
      "created_at": "2025-11-20T10:30:00Z"
    }
  ]
}
```

---

### Reports

#### Create Report

**Endpoint**: `POST /api/v1/reports/`

**Request**:
```json
{
  "reported_listing_id": 123,
  "reason": "Fake listing, photos don't match actual room"
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "reported_listing_id": 123,
  "reason": "Fake listing, photos don't match actual room",
  "status": "new",
  "created_at": "2025-11-22T10:30:00Z"
}
```

#### Get My Reports

**Endpoint**: `GET /api/v1/reports/`

**Response** (200 OK):
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "reported_listing_id": 123,
      "status": "in_review",
      "created_at": "2025-11-22T10:30:00Z"
    }
  ]
}
```

---

## Error Handling

All errors follow a standardized format:

```json
{
  "status": "error",
  "code": "ERROR_CODE",
  "message": "Human-readable message",
  "details": {
    "field": ["error message"]
  },
  "timestamp": "2025-11-22T10:30:00Z"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `NOT_FOUND` | 404 | Resource not found |
| `PERMISSION_DENIED` | 403 | User lacks required permissions |
| `AUTHENTICATION_FAILED` | 401 | Authentication credentials are invalid |
| `VALIDATION_ERROR` | 400 | Input validation failed |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_SERVER_ERROR` | 500 | Server error |

---

## Authentication

### JWT Token

API uses JWT (JSON Web Token) for authentication.

**Getting a Token**:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

**Using the Token**:

Include in Authorization header:

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  http://localhost:8000/api/v1/listings/
```

**Token Expiration**:
- Access Token: 24 hours
- Refresh Token: 7 days

**Refreshing Token**:

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN"
  }'
```

---

## Rate Limiting

API implements rate limiting:

- **Anonymous Users**: 120 requests/minute
- **Authenticated Users**: 300 requests/minute

When limit is exceeded:

```json
{
  "status": "error",
  "code": "RATE_LIMITED",
  "message": "Request rate limit exceeded. Please try again later.",
  "timestamp": "2025-11-22T10:30:00Z"
}
```

**Headers**:
```
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 299
X-RateLimit-Reset: 1700640600
```

---

## Response Pagination

List endpoints return paginated results:

```json
{
  "count": 150,
  "next": "https://api.example.com/listings/?page=2",
  "previous": null,
  "results": [...]
}
```

**Query Parameters**:
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 10, max: 100)

---

## Filter & Search

### Listing Filters

Listings support multiple filters (can be combined):

```
GET /api/v1/listings/?city_slug=tashkent&min_price=1000000&max_price=2000000&gender_preference=any
```

**Available Filters**:
- `city_slug`: City identifier
- `min_price`: Minimum price
- `max_price`: Maximum price
- `gender_preference`: `male`, `female`, `any`
- `listing_type`: `have_room`, `need_room`
- `ordering`: Sort by field (`created_at`, `price`)

---

## Code Examples

### JavaScript / Fetch

```javascript
// Login
const loginResponse = await fetch('https://api.example.com/api/v1/auth/login/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123'
  })
});

const { access } = await loginResponse.json();

// Get recommendations
const recsResponse = await fetch(
  'https://api.example.com/api/v1/matching/recommendations?min_score=70',
  {
    headers: { 'Authorization': `Bearer ${access}` }
  }
);

const recommendations = await recsResponse.json();
```

### Python / Requests

```python
import requests

# Login
response = requests.post(
    'https://api.example.com/api/v1/auth/login/',
    json={
        'email': 'user@example.com',
        'password': 'password123'
    }
)
token = response.json()['access']

# Get recommendations
response = requests.get(
    'https://api.example.com/api/v1/matching/recommendations?min_score=70',
    headers={'Authorization': f'Bearer {token}'}
)
recommendations = response.json()
```

---

## Interactive Documentation

For interactive API documentation with try-it-out functionality:

- **Swagger UI**: `/api/docs/`
- **ReDoc**: `/api/redoc/`

---

## Support

For issues or questions:
- Create an issue on GitHub
- Contact: support@sherik.uz
- Documentation: https://sherik.uz/docs
